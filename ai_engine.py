import os
import json
import hashlib
import logging
from groq import Groq
from fastapi import HTTPException, status

logger = logging.getLogger("ai_engine")

groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def generate_cache_key(task: str, compliance: str) -> str:
    return hashlib.md5(f"{task}_{compliance}".lower().encode()).hexdigest()

async def lookup_tools(task: str, compliance: str):
    prompt = f"""
You are a cybersecurity compliance expert. I need you to recommend exactly 5 tools for the given task and compliance standard.

Task: "{task}"
Compliance Standard: "{compliance}"

Please respond with ONLY a valid JSON array containing exactly 5 tool objects. Each object must have these exact fields:

- "tool": string (tool name)
- "vendor": string (vendor/company name)  
- "description": string (brief description of the tool)
- "how_to": array of strings (DETAILED step-by-step implementation instructions - be very specific with commands, configurations, file paths, URLs, and exact procedures. Include at least 8-12 detailed steps)
- "prerequisites": array of strings (requirements before using this tool)
- "estimated_time": string (time estimate like "2-4 hours", "1-2 days")
- "pitfalls": array of strings (common mistakes or issues to avoid)
- "compliance_notes": string (how this tool helps with the specific compliance standard)

IMPORTANT: For the "how_to" field, provide detailed implementation steps including:
- Specific download URLs or installation commands
- Exact configuration file paths and settings
- Command line instructions with actual commands
- GUI navigation steps (click X, go to Y menu, select Z option)
- Configuration parameters and their values
- Testing and verification steps
- Integration steps with existing systems
- Post-installation configuration requirements

Example format with detailed how_to:
[
  {{
    "tool": "Microsoft Defender for Endpoint",
    "vendor": "Microsoft",
    "description": "Enterprise endpoint protection platform",
    "how_to": [
      "Sign into Microsoft 365 Defender at https://security.microsoft.com with admin credentials",
      "Go to Settings > Endpoints > Onboarding",
      "Select 'Windows Server 2016+' or 'Linux' and download the onboarding package",
      "For Windows, run as admin: 'WindowsDefenderATPLocalOnboardingScript.cmd'",
      "For Linux, run: 'bash mdatp_onboard.sh'",
      "Verify agent: Windows ('sc query sense'), Linux ('mdatp health')",
      "Set exclusions: 'Set-MpPreference -ExclusionPath \"C:\\ProgramData\\DB\"'",
      "Configure policies: Go to Settings > Policies > Antivirus",
      "Test with EICAR: Download eicar.com and verify alert in Incidents & Alerts",
      "Enable cloud protection: Settings > Endpoints > Advanced features",
      "Set up logging: Integrate with Microsoft Sentinel via Connectors"
    ],
    "prerequisites": ["Windows 10/11 systems", "Microsoft 365 E5 or Defender for Endpoint license", "Global Admin rights"],
    "estimated_time": "4-6 hours",
    "pitfalls": ["Ensure proper licensing before deployment", "Configure exclusions for business applications", "Test in pilot group before organization-wide rollout"],
    "compliance_notes": "Provides malware protection required by ISO 27001 control A.12.2.1 - Protection against malware"
  }}
]

Respond with ONLY the JSON array, no other text or explanations.
"""

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a cybersecurity expert who provides tool recommendations in valid JSON format only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=6000
        )
        resp = completion.choices[0].message.content
        
        # Print raw response to console (Anaconda Prompt)
        print("\n--- Raw AI response ---")
        print(resp)
        print("--- End of response ---\n")

        logger.info(f"Raw AI response: {resp}")

        if not resp or resp.strip() == "":
            logger.error("Empty response from AI")
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Empty AI response")

        # Clean up the response - remove any markdown formatting
        resp = resp.strip()
        if resp.startswith("```json"):
            resp = resp[7:]
        if resp.startswith("```"):
            resp = resp[3:]
        if resp.endswith("```"):
            resp = resp[:-3]
        resp = resp.strip()

        try:
            tools = json.loads(resp)
        except json.JSONDecodeError as e:
            # Save the raw response to a file for inspection
            filename = "failed_ai_response.json"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(resp)
            logger.error(f"JSON decode error: {e}. Response saved to {filename}")
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Invalid AI response - JSON parse error: {str(e)}")

        # Validate the structure
        if not isinstance(tools, list):
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="AI response must be a JSON array")
        
        if len(tools) != 5:
            logger.warning(f"Expected 5 tools, got {len(tools)}")
            # Take first 5 if more, or pad with generic tools if less
            if len(tools) > 5:
                tools = tools[:5]
            elif len(tools) < 5:
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Expected 5 tools, got {len(tools)}")

        # Validate each tool object has required fields
        required_fields = ["tool", "vendor", "description", "how_to", "prerequisites", "estimated_time", "pitfalls", "compliance_notes"]
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Tool {i+1} is not a valid object")
            
            for field in required_fields:
                if field not in tool:
                    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Tool {i+1} missing required field: {field}")
                
                # Ensure list fields are actually lists
                if field in ["how_to", "prerequisites", "pitfalls"] and not isinstance(tool[field], list):
                    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Tool {i+1} field '{field}' must be an array")
                
                # Ensure string fields are actually strings
                if field in ["tool", "vendor", "description", "estimated_time", "compliance_notes"] and not isinstance(tool[field], str):
                    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Tool {i+1} field '{field}' must be a string")

        logger.info(f"Successfully parsed {len(tools)} tools")

    except HTTPException:
        raise  # Re-raise FastAPI HTTPException as is

    except Exception as e:
        logger.error(f"Groq API failure: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"AI service unavailable: {str(e)}")

    return tools, "fresh"

def check_dependencies():
    return {"groq_api": "healthy"}
