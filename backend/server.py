from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
import json
import re


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class CommandRequest(BaseModel):
    command: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class CommandResponse(BaseModel):
    response: str
    action: Optional[str] = None
    url: Optional[str] = None
    success: bool = True

class VoiceCommand(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    command: str
    response: str
    action: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Command Processing Logic
class CommandProcessor:
    def __init__(self):
        self.website_patterns = {
            r'(?:open|go to|visit)\s+youtube': {
                'url': 'https://www.youtube.com',
                'response': 'Opening YouTube for you, sir.'
            },
            r'(?:open|go to|visit)\s+google': {
                'url': 'https://www.google.com',
                'response': 'Opening Google for you, sir.'
            },
            r'(?:open|go to|visit)\s+facebook': {
                'url': 'https://www.facebook.com',
                'response': 'Opening Facebook for you, sir.'
            },
            r'(?:open|go to|visit)\s+twitter': {
                'url': 'https://www.twitter.com',
                'response': 'Opening Twitter for you, sir.'
            },
            r'(?:open|go to|visit)\s+instagram': {
                'url': 'https://www.instagram.com',
                'response': 'Opening Instagram for you, sir.'
            },
            r'(?:open|go to|visit)\s+linkedin': {
                'url': 'https://www.linkedin.com',
                'response': 'Opening LinkedIn for you, sir.'
            },
            r'(?:open|go to|visit)\s+github': {
                'url': 'https://www.github.com',
                'response': 'Opening GitHub for you, sir.'
            },
            r'(?:open|go to|visit)\s+netflix': {
                'url': 'https://www.netflix.com',
                'response': 'Opening Netflix for you, sir.'
            },
            r'(?:open|go to|visit)\s+amazon': {
                'url': 'https://www.amazon.com',
                'response': 'Opening Amazon for you, sir.'
            },
        }
        
        self.search_patterns = {
            r'search\s+(?:for\s+)?(.+?)\s+(?:on|in)\s+youtube': {
                'url_template': 'https://www.youtube.com/results?search_query={}',
                'response': 'Searching {} on YouTube for you, sir.'
            },
            r'search\s+(?:for\s+)?(.+?)\s+(?:on|in)\s+google': {
                'url_template': 'https://www.google.com/search?q={}',
                'response': 'Searching {} on Google for you, sir.'
            },
            r'(?:search|google)\s+(?:for\s+)?(.+)': {
                'url_template': 'https://www.google.com/search?q={}',
                'response': 'Searching {} on Google for you, sir.'
            },
        }
        
        self.greeting_patterns = {
            r'(?:hello|hi|hey)\s+(?:jarvis|assistant)': 'Hello sir, how may I assist you today?',
            r'(?:hello|hi|hey)': 'Hello sir, I am Jarvis, your AI assistant. How may I help you?',
            r'(?:how are you|how\'re you)': 'I am functioning optimally, sir. Ready to assist you.',
            r'(?:good morning|morning)': 'Good morning, sir. How may I assist you today?',
            r'(?:good afternoon|afternoon)': 'Good afternoon, sir. How may I assist you today?',
            r'(?:good evening|evening)': 'Good evening, sir. How may I assist you today?',
            r'(?:good night|goodnight)': 'Good night, sir. Rest well.',
            r'(?:thank you|thanks)': 'You are welcome, sir. Always at your service.',
            r'(?:what is your name|who are you)': 'I am Jarvis, your personal AI assistant, sir.',
        }
        
        self.time_patterns = {
            r'(?:what time is it|what\'s the time|current time)': self._get_current_time,
            r'(?:what date is it|what\'s the date|current date)': self._get_current_date,
        }
    
    def _get_current_time(self):
        now = datetime.now()
        return f"The current time is {now.strftime('%I:%M %p')}, sir."
    
    def _get_current_date(self):
        now = datetime.now()
        return f"Today is {now.strftime('%A, %B %d, %Y')}, sir."

    def process_command(self, command: str) -> CommandResponse:
        command = command.lower().strip()
        
        # Check website opening patterns
        for pattern, data in self.website_patterns.items():
            if re.search(pattern, command, re.IGNORECASE):
                return CommandResponse(
                    response=data['response'],
                    action='open_url',
                    url=data['url']
                )
        
        # Check search patterns
        for pattern, data in self.search_patterns.items():
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                search_term = match.group(1).strip()
                url = data['url_template'].format(search_term.replace(' ', '+'))
                response = data['response'].format(search_term)
                return CommandResponse(
                    response=response,
                    action='open_url',
                    url=url
                )
        
        # Check greeting patterns
        for pattern, response in self.greeting_patterns.items():
            if re.search(pattern, command, re.IGNORECASE):
                return CommandResponse(response=response)
        
        # Check time patterns
        for pattern, func in self.time_patterns.items():
            if re.search(pattern, command, re.IGNORECASE):
                response = func() if callable(func) else func
                return CommandResponse(response=response)
        
        # Default response for unrecognized commands
        return CommandResponse(
            response="I'm sorry sir, I didn't understand that command. Please try again.",
            success=False
        )


# Initialize command processor
command_processor = CommandProcessor()

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Jarvis AI Assistant Backend is running"}

@api_router.post("/process-command", response_model=CommandResponse)
async def process_voice_command(request: CommandRequest):
    try:
        # Process the command
        result = command_processor.process_command(request.command)
        
        # Store command in database
        voice_command = VoiceCommand(
            command=request.command,
            response=result.response,
            action=result.action
        )
        await db.voice_commands.insert_one(voice_command.dict())
        
        return result
    except Exception as e:
        logger.error(f"Error processing command: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing command")

@api_router.get("/commands", response_model=List[VoiceCommand])
async def get_command_history():
    commands = await db.voice_commands.find().sort("timestamp", -1).to_list(50)
    return [VoiceCommand(**cmd) for cmd in commands]

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
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