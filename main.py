from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, validator
from fastapi.middleware.cors import CORSMiddleware
import httpx
from fastapi.responses import JSONResponse
import logging

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure CORS - add your frontend URL here
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://leadsystem-vert.vercel.app",  # <-- Add your frontend URL here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Lead(BaseModel):
    name: str
    email: EmailStr
    company: str = ""
    message: str = ""

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.title()

@app.get("/")
async def root():
    return {"message": "Welcome to the Lead Submission API"}

@app.post("/submit")
async def submit_lead(lead: Lead):
    webhook_url = "https://bsnehith19.app.n8n.cloud/webhook/lead-submit"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        logger.info(f"Processing lead: {lead.json()}")
        
        # Validate data before sending
        if not lead.name or not lead.email:
            raise HTTPException(status_code=422, detail="Name and email are required")
        
        payload = {
            "name": lead.name,
            "email": lead.email,
            "company": lead.company,
            "message": lead.message
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                webhook_url,
                json=payload,
                headers=headers
            )
            
            response.raise_for_status()
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "Lead submitted successfully",
                    "data": payload
                }
            )
            
    except httpx.HTTPStatusError as e:
        logger.error(f"Webhook error: {e.response.text}")
        raise HTTPException(
            status_code=400,
            detail=f"Webhook error: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Service is healthy"}
