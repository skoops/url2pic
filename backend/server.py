from fastapi import FastAPI, APIRouter, HTTPException, Body, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
import os
import logging
import uuid
from datetime import datetime
from pathlib import Path
import json
from playwright.async_api import async_playwright
import asyncio
import aiofiles

# Root directory and load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Screenshot storage directory
SCREENSHOT_DIR = ROOT_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class ScreenshotRequest(BaseModel):
    url: HttpUrl
    desktop_resolution: str
    mobile_resolution: str
    desktop_user_agent: Optional[str] = None
    mobile_user_agent: Optional[str] = None

class Screenshot(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: str
    desktop_path: str
    mobile_path: str
    desktop_resolution: str
    mobile_resolution: str
    desktop_user_agent: Optional[str] = None
    mobile_user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Common user agents
DESKTOP_USER_AGENTS = [
    {"name": "Chrome (Windows)", "value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
    {"name": "Firefox (Windows)", "value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"},
    {"name": "Safari (macOS)", "value": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"},
    {"name": "Edge (Windows)", "value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"},
    {"name": "Chrome (macOS)", "value": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
    {"name": "Opera (Windows)", "value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0"},
    {"name": "Chrome (Linux)", "value": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
    {"name": "Firefox (macOS)", "value": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.0; rv:109.0) Gecko/20100101 Firefox/115.0"},
    {"name": "Firefox (Linux)", "value": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"},
    {"name": "Edge (macOS)", "value": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"},
]

MOBILE_USER_AGENTS = [
    {"name": "Chrome (Android)", "value": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"},
    {"name": "Safari (iOS)", "value": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"},
    {"name": "Samsung Internet", "value": "Mozilla/5.0 (Linux; Android 10; SAMSUNG SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/20.0 Chrome/106.0.0.0 Mobile Safari/537.36"},
    {"name": "Firefox (Android)", "value": "Mozilla/5.0 (Android 14; Mobile; rv:109.0) Gecko/114.0 Firefox/114.0"},
    {"name": "Chrome (iOS)", "value": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.0.0 Mobile/15E148 Safari/604.1"},
    {"name": "Edge (Android)", "value": "Mozilla/5.0 (Linux; Android 10; HD1913) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36 EdgA/120.0.0.0"},
    {"name": "Firefox (iOS)", "value": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/114.0 Mobile/15E148 Safari/605.1.15"},
    {"name": "Opera (Android)", "value": "Mozilla/5.0 (Linux; Android 10; VOG-L29) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36 OPR/76.0.0.0"},
    {"name": "UC Browser", "value": "Mozilla/5.0 (Linux; U; Android 10; en-US; Pixel 4) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/110.0.0.0 UCBrowser/14.0.0.1381 Mobile Safari/537.36"},
    {"name": "DuckDuckGo (iOS)", "value": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 DuckDuckGo/7 Safari/605.1.15"},
]

# Common screen resolutions
DESKTOP_RESOLUTIONS = [
    {"label": "1920×1080", "width": 1920, "height": 1080},
    {"label": "1366×768", "width": 1366, "height": 768},
    {"label": "1440×900", "width": 1440, "height": 900},
    {"label": "1536×864", "width": 1536, "height": 864},
    {"label": "1280×1024", "width": 1280, "height": 1024},
]

MOBILE_RESOLUTIONS = [
    {"label": "360×800", "width": 360, "height": 800},
    {"label": "375×667", "width": 375, "height": 667},
    {"label": "414×896", "width": 414, "height": 896},
    {"label": "390×844", "width": 390, "height": 844},
    {"label": "360×640", "width": 360, "height": 640},
]

# Routes
@api_router.get("/")
async def root():
    return {"message": "Screenshot API"}

@api_router.get("/user-agents")
async def get_user_agents():
    return {
        "desktop": DESKTOP_USER_AGENTS,
        "mobile": MOBILE_USER_AGENTS
    }

@api_router.get("/resolutions")
async def get_resolutions():
    return {
        "desktop": DESKTOP_RESOLUTIONS,
        "mobile": MOBILE_RESOLUTIONS
    }

@api_router.post("/screenshots", response_model=Screenshot)
async def create_screenshot(request_data: ScreenshotRequest):
    # Generate unique IDs for screenshots
    screenshot_id = str(uuid.uuid4())
    desktop_filename = f"{screenshot_id}_desktop.png"
    mobile_filename = f"{screenshot_id}_mobile.png"
    
    desktop_path = SCREENSHOT_DIR / desktop_filename
    mobile_path = SCREENSHOT_DIR / mobile_filename
    
    # Get resolution dimensions
    desktop_res = next((res for res in DESKTOP_RESOLUTIONS if res["label"] == request_data.desktop_resolution), DESKTOP_RESOLUTIONS[0])
    mobile_res = next((res for res in MOBILE_RESOLUTIONS if res["label"] == request_data.mobile_resolution), MOBILE_RESOLUTIONS[0])
    
    # Take screenshots
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            # Desktop screenshot
            desktop_context = await browser.new_context(
                viewport={"width": desktop_res["width"], "height": desktop_res["height"]},
                user_agent=request_data.desktop_user_agent
            )
            desktop_page = await desktop_context.new_page()
            await desktop_page.goto(str(request_data.url), wait_until="networkidle", timeout=60000)
            await desktop_page.screenshot(path=desktop_path)
            await desktop_context.close()
            
            # Mobile screenshot
            mobile_context = await browser.new_context(
                viewport={"width": mobile_res["width"], "height": mobile_res["height"]},
                user_agent=request_data.mobile_user_agent,
                is_mobile=True
            )
            mobile_page = await mobile_context.new_page()
            await mobile_page.goto(str(request_data.url), wait_until="networkidle", timeout=60000)
            await mobile_page.screenshot(path=mobile_path)
            await mobile_context.close()
            
            await browser.close()
    except Exception as e:
        logging.error(f"Error taking screenshot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to capture screenshot: {str(e)}")
    
    # Save metadata to MongoDB
    screenshot = Screenshot(
        id=screenshot_id,
        url=str(request_data.url),
        desktop_path=str(desktop_path),
        mobile_path=str(mobile_path),
        desktop_resolution=request_data.desktop_resolution,
        mobile_resolution=request_data.mobile_resolution,
        desktop_user_agent=request_data.desktop_user_agent,
        mobile_user_agent=request_data.mobile_user_agent
    )
    
    await db.screenshots.insert_one(screenshot.dict())
    
    return screenshot

@api_router.get("/screenshots", response_model=List[Screenshot])
async def get_screenshots():
    screenshots = await db.screenshots.find().sort("created_at", -1).to_list(1000)
    return [Screenshot(**screenshot) for screenshot in screenshots]

@api_router.get("/screenshots/{screenshot_id}")
async def get_screenshot(screenshot_id: str):
    screenshot = await db.screenshots.find_one({"id": screenshot_id})
    if not screenshot:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    return Screenshot(**screenshot)

@api_router.get("/screenshots/{screenshot_id}/{mode}")
async def get_screenshot_image(screenshot_id: str, mode: str):
    screenshot = await db.screenshots.find_one({"id": screenshot_id})
    if not screenshot:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    
    # Determine which path to return
    if mode.lower() == "desktop":
        path = screenshot["desktop_path"]
    elif mode.lower() == "mobile":
        path = screenshot["mobile_path"]
    else:
        raise HTTPException(status_code=400, detail="Invalid mode. Must be 'desktop' or 'mobile'")
    
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Screenshot file not found")
    
    return FileResponse(path)

@api_router.delete("/screenshots/{screenshot_id}")
async def delete_screenshot(screenshot_id: str):
    screenshot = await db.screenshots.find_one({"id": screenshot_id})
    if not screenshot:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    
    # Delete files
    try:
        if os.path.exists(screenshot["desktop_path"]):
            os.remove(screenshot["desktop_path"])
        if os.path.exists(screenshot["mobile_path"]):
            os.remove(screenshot["mobile_path"])
    except Exception as e:
        logging.error(f"Error deleting screenshot files: {e}")
    
    # Delete from database
    result = await db.screenshots.delete_one({"id": screenshot_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Failed to delete screenshot from database")
    
    return {"status": "success", "message": "Screenshot deleted"}

# Include the router in the main app
app.include_router(api_router)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
