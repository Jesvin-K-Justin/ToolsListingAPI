from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any

# Auth
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)

class UserResponse(BaseModel):
    id: int
    username: str

    model_config = {
        "from_attributes": True
    }


class Token(BaseModel):
    access_token: str
    token_type: str

# Lookup
class ToolLookupRequest(BaseModel):
    task: str = Field(..., min_length=10, example="All servers should have an AntiMalware tool installed")
    compliance: str = Field(..., min_length=3, example="ISO 27001:2022")

class ToolRecommendation(BaseModel):
    tool: str
    vendor: str
    description: str
    how_to: List[str]
    prerequisites: List[str]
    estimated_time: str
    pitfalls: List[str]
    compliance_notes: str

class ToolLookupResponse(BaseModel):
    task: str
    compliance: str
    tools: List[ToolRecommendation]
    generated_at: str
    cache_status: str

# Health
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    dependencies: Dict[str, str]
