import os
import stripe
import uvicorn
from fastapi import FastAPI, Request, HTTPException, logger
from fastapi.middleware.cors import CORSMiddleware # Import CORS Middleware
# Removed RedirectResponse as it's not used
from pydantic import BaseModel
from dotenv import load_dotenv

from api import create_api_routes
from config.settings import frontend_url

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# --- CORS Configuration ---
# List of allowed origins (your frontend URL)
origins = [
    frontend_url, # Get from .env
    # You can add more origins here if needed, e.g., your production frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Allows specified origins
    allow_credentials=True, # Allows cookies (not strictly needed here, but good practice)
    allow_methods=["*"], # Allows all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"], # Allows all headers
)

create_api_routes(app=app)

if __name__ == "__main__":
    logger.info("Starting FastAPI server...")
    # Use port 8000 by default, matching the Stripe CLI forward example
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
