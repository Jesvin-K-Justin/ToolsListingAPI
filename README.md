# GRC AI Engine

An AI-powered cybersecurity tool recommendation engine designed to help organizations establish and enforce GRC (Governance, Risk & Compliance) and cybersecurity policies. Perfect for interns and junior security professionals who need expert-level guidance on compliance implementation.

## Overview

The GRC AI Engine leverages advanced AI to provide intelligent tool recommendations for cybersecurity compliance tasks. Given a specific task and compliance standard, the engine returns the top 5 most suitable tools along with detailed implementation guidance.

### Key Features

-  **AI-Powered Recommendations**: Uses Groq's LLaMA model for intelligent tool suggestions
-  **JWT Authentication**: Secure API access with token-based authentication
-  **Comprehensive Tool Details**: Each recommendation includes implementation steps, prerequisites, pitfalls, and compliance notes
-  **Health Monitoring**: Built-in health checks and dependency monitoring
-  **Fast API**: Built with FastAPI for high performance and automatic API documentation
-  **Database Integration**: SQLAlchemy-based user management and session handling

### Quick Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**
   ```bash
   # Create a .env file or set environment variable
   export GROQ_API_KEY="your_groq_api_key_here"
   ```

3. **Run the application**
   ```bash
   uvicorn main:app 
   ```

4. **Access the API**
   - API Base URL: `http://localhost:8000`
   - Interactive Docs: `http://localhost:8000/docs`
   - OpenAPI Schema: `http://localhost:8000/openapi.json`

##  Usage

### Authentication

First, register a user and obtain an access token:

```bash
# Register a new user
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# Login to get access token
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_username&password=your_password"
```

### Get Tool Recommendations

```bash
curl -X POST "http://localhost:8000/api/ai-engine/v1/lookup" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "All servers should have an AntiMalware tool installed",
    "compliance": "ISO 27001:2022"
  }'
```

### Example Response

```json
{
  "task": "All servers should have an AntiMalware tool installed",
  "compliance": "ISO 27001:2022",
  "generated_at": "2024-01-15T10:30:00Z",
  "cache_status": "fresh",
  "tools": [
    {
      "tool": "Microsoft Defender for Endpoint",
      "vendor": "Microsoft",
      "description": "Enterprise endpoint protection platform",
      "how_to": [
        "Install via Microsoft 365 Security Center",
        "Configure policies",
        "Deploy to endpoints"
      ],
      "prerequisites": [
        "Windows 10/11 systems",
        "Microsoft 365 license"
      ],
      "estimated_time": "4-6 hours",
      "pitfalls": [
        "Ensure proper licensing",
        "Configure exclusions properly"
      ],
      "compliance_notes": "Provides malware protection required by ISO 27001 control A.12.2.1"
    }
    // ... 4 more tools
  ]
}
```

##  API Reference

### Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register` | Register new user | No |
| POST | `/api/auth/login` | Login user | No |
| POST | `/api/ai-engine/v1/lookup` | Get tool recommendations | Yes |
| GET | `/api/health` | Health check | No |

### Tool Lookup Request Schema

```json
{
  "task": "string (min 10 chars)",
  "compliance": "string (min 3 chars)"
}
```

##  Error Handling

The API returns appropriate HTTP status codes:

- `200`: Success
- `400`: Bad Request (invalid input)
- `401`: Unauthorized (invalid/missing token)
- `502`: Bad Gateway (AI service error)
- `503`: Service Unavailable (AI service down)


##  Testing

Run the application and test the endpoints:

```bash
# Start the server
uvicorn main:app 

# Test health endpoint
curl http://localhost:8000/api/health

# Test authentication
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'
```

##  Security

- JWT tokens expire after 60 minutes
- Passwords are hashed using bcrypt
- Input validation on all endpoints
- Rate limiting recommended for production use


### Environment Variables

```bash
GROQ_API_KEY=your_groq_api_key
DATABASE_URL=sqlite:///./users.db  # Optional, defaults to SQLite
JWT_SECRET_KEY=your_jwt_secret     # Optional, auto-generated if not provided
```

