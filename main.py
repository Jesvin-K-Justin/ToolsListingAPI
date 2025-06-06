from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from models import User
from schemas import UserCreate, UserResponse, Token, ToolLookupRequest, ToolLookupResponse, HealthResponse
from auth import get_password_hash, verify_password, create_access_token, get_current_user
from ai_engine import lookup_tools, check_dependencies
from fastapi import Request

from datetime import timedelta, datetime
import logging

# Initialize
Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="GRC AI Engine",
    version="1.0.0",
    description="AI-powered cybersecurity tool recommendation engine",
    contact={"name": "GRC Team", "email": "grc-team@company.com"},
    license_info={"name": "Internal Use Only"}
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
logger = logging.getLogger("uvicorn.access")

# -------- ROUTES --------

@app.post("/api/auth/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed = get_password_hash(user.password)
    u = User(username=user.username, hashed_password=hashed)
    db.add(u); db.commit(); db.refresh(u)
    return u

@app.post("/api/auth/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.username}, expires=timedelta(minutes=60))
    return {"access_token": token, "token_type": "bearer"}

@app.post("/api/ai-engine/v1/lookup", response_model=ToolLookupResponse)
async def lookup(req: ToolLookupRequest, user: User = Depends(get_current_user)):
    tools, status = await lookup_tools(req.task, req.compliance)
    return ToolLookupResponse(
        task=req.task, compliance=req.compliance, tools=tools,
        generated_at=datetime.utcnow().isoformat() + "Z",
        cache_status=status
    )

@app.get("/api/health", response_model=HealthResponse)
def health():
    deps = check_dependencies()
    status_overall = "healthy" if all(v=="healthy" for v in deps.values()) else "degraded"
    return HealthResponse(status=status_overall, timestamp=datetime.utcnow().isoformat()+"Z", version="1.0.0", dependencies=deps)

# Global exception handlers


@app.exception_handler(HTTPException)
async def custom_http(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "message": str(exc.detail),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )

@app.exception_handler(Exception)
async def global_exc(request: Request, exc: Exception):
    logger.error(f"Unhandled: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "Unexpected error",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
