from fastapi import FastAPI, Request, Response, HTTPException, Depends
import secrets
import redis
import json
from urllib.parse import urlparse
import logging
import sys
import os
from .models import UserMessage 
from sqlalchemy.orm import Session
from .connection import Messages, init_db, get_db
from .tools import search_dayne_info, search_dayne_info_handler
from fastapi.middleware.cors import CORSMiddleware


# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from helper import function_to_schema
from registry import Tool
from managers import AssistantManager
from registry import Registry



app = FastAPI()

# Allow CORS for specific origins or all origins
origins = [
    "http://localhost:3000",  # Your React app during development
    "https://portfolio-1-eight-rosy.vercel.app",  # Your production frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow specific origins or use ["*"] to allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)


# Connect to Redis
url = urlparse(os.environ.get('REDISCLOUD_URL'))
redis_client = redis.Redis(host=url.hostname, port=url.port, password=url.password)

# Test Redis connection
try:
    redis_client.ping()
    print("Redis server is running!")
except redis.ConnectionError as e:
    print(f"Failed to connect to Redis: {e}")

init_db()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
debug = True


# Dependency to check or create a session
def ensure_session(request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    logging.debug(f"Received session_id from cookies: {session_id}")

    if session_id:
        if redis_client.exists(session_id):
            logging.debug("Session exists in Redis. Refreshing TTL.")
            redis_client.expire(session_id, 1800)  # Refresh TTL
            return session_id
        else:
            logging.debug("Session ID exists in cookies but not in Redis.")
            response.delete_cookie("session_id")
    
    # Create a new session if none exists
    logging.debug("Creating a new session.")
    new_session_id = secrets.token_hex(32)
    redis_client.setex(new_session_id, 1800, "session_active")  # 30 minutes TTL
    response.set_cookie(
        key="session_id",
        value=new_session_id,
        httponly=True,
        secure=False,  # Use False for local development; switch to True in production
        samesite="Lax",
    )
    logging.debug(f"New session_id set: {new_session_id}")
    return new_session_id


def get_or_create_manager(
    session_id: str = Depends(ensure_session)
) -> AssistantManager:
    # Retrieve session data from Redis
    session_data = redis_client.get(session_id)
    
    # Safely parse session data or initialize an empty object
    try:
        session_data = json.loads(session_data) if session_data else {}
    except json.JSONDecodeError:
        session_data = {}
    
    # Initialize or retrieve AssistantManager
    manager_data = session_data.get("assistant")
    if manager_data:
        # Deserialize existing manager
        AssistantManager.assistant_id = manager_data.get("assistant_id")
        AssistantManager.thread_id = manager_data.get("thread_id")
        toolkit = [search_dayne_info]

        helpers = [search_dayne_info_handler]

        registry = Registry()
        
        # Loop to register each tool
        for func, helper in zip(toolkit, helpers):
            registry.register_tool(Tool(func, helper))
        manager = AssistantManager(registry=registry)
    else:
        toolkit = [search_dayne_info]

        helpers = [search_dayne_info_handler]

        registry = Registry()
        
        # Loop to register each tool
        for func, helper in zip(toolkit, helpers):
            registry.register_tool(Tool(func, helper))

        # Create a new manager
        manager = AssistantManager(registry=registry)

          
       

        # manager.add_registry(registry)

        tools = [function_to_schema(tool) for tool in toolkit]

        manager.create_assistant(
            name="Dayne's assistant",
            instructions="You are Dayne's personal assistant, you will sing high praises of his ethic",
            tools=tools
        )
        manager.create_thread()
    
    # Save updated manager state back to session
    session_data["assistant"] = {
        "assistant_id": AssistantManager.assistant_id,
        "thread_id": AssistantManager.thread_id,
    }
    redis_client.setex(session_id, 1800, json.dumps(session_data))  # Update TTL and session data
    
    return manager


@app.get("/")
async def index(
    response: Response, 
    session_id: str = Depends(ensure_session), 
    manager: AssistantManager = Depends(get_or_create_manager)
):
    # Use the `manager` injected by the dependency
    status = manager.connect_confirm()

    return {
        "message": "You accessed the page!",
        "session_id": session_id,
        "assistant_info": status,
    }



@app.post("/register")
async def register(
    response: Response,
    message: UserMessage,
    manager: AssistantManager = Depends(get_or_create_manager),
    db: Session = Depends(get_db)
):
    
    attributes = vars(message)
    # Create a new user message
    user_message = Messages(
       **attributes
    )

    prompt = f"Answer questions conserning {user_message.reason}. Refer to the person as {user_message.fname}. {user_message.fname} had written {user_message.message}. "
    manager.add_message_to_thread("user", prompt )
    manager.run_assistant(instructions="Answer messages appropriately")
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    manager.wait_for_completion()
    message = manager.get_last_message()
    return {"message": "User registered successfully.", "id": user_message.id, "response" : message}
    

@app.post("/chat/message")
async def chat(
    response: Response,
    message: UserMessage,
    session_id: str = Depends(ensure_session), 
    manager: AssistantManager = Depends(get_or_create_manager),
    db: Session = Depends(get_db)
):
    # Process the incoming message
    manager.add_message_to_thread("user", message.message)
    manager.run_assistant(instructions="Answer messages appropriately. Be conversational with no filler words. If you cannot dind information, tell them to email Dayne at dayneguy@gmail.com")
    manager.wait_for_completion()
    
    # Get the assistant's response
    assistant_response = manager.get_last_message() 
    logging.debug(manager.run_steps())
    
    return {"message": "Message submitted successfully.", "response": assistant_response}
    

# @app.get("/start-session")
# def start_session(response: Response):
#     # Generate a unique session ID
#     session_id = secrets.token_hex(32)
#     # Save the session in Redis with a default expiration (e.g., 30 minutes)
#     redis_client.setex(session_id, 1800, "session_active")
#     # Set the session ID in a secure cookie
#     response.set_cookie(
#         key="session_id",
#         value=session_id,
#         httponly=True,  # JavaScript cannot access this cookie
#         secure=True,  # Send cookie only over HTTPS
#         samesite="Lax",  # Prevent CSRF
#     )
#     return {"message": "Session started!", "session_id": session_id}


# @app.get("/validate-session")
# def validate_session(request: Request):
    # Retrieve session ID from cookies
    # session_id = request.cookies.get("session_id")
    # if not session_id or not redis_client.get(session_id):
    #     raise HTTPException(status_code=401, detail="Session invalid or expired")
    
    # return {"message": "Session is valid", "session_id": session_id}