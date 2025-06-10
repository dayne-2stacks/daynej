from fastapi import FastAPI, Request, Response, Depends, WebSocket, WebSocketDisconnect
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

# from .tools import search_dayne_info, search_dayne_info_handler
from fastapi.middleware.cors import CORSMiddleware


# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents_manager import AgentManager
from agents import ItemHelpers
from registry import Registry

from dotenv import load_dotenv

load_dotenv()


app = FastAPI()

# Allow CORS for specific origins or all origins
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)


# Connect to Redis
url = urlparse(os.environ.get("REDISCLOUD_URL"))
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
    session_id: str = Depends(ensure_session),
) -> AgentManager:
    # Retrieve session data from Redis
    session_data = redis_client.get(session_id)

    # Safely parse session data or initialize an empty object
    try:
        session_data = json.loads(session_data) if session_data else {}
    except json.JSONDecodeError:
        session_data = {}

    # Initialize or retrieve AgentManager
    manager_data = session_data.get("assistant")
    if manager_data:
        registry = Registry()
        manager = AgentManager(registry=registry)
    else:
        # toolkit = [search_dayne_info]

        # helpers = [search_dayne_info_handler]

        registry = Registry()

        # Loop to register each tool
        # for func, helper in zip(toolkit, helpers):
        #     registry.register_tool(Tool(func, helper))

        # Create a new manager
        manager = AgentManager(registry=registry)

        # manager.add_registry(registry)

        # tools = [function_to_schema(tool) for tool in toolkit]

        instructions = """
         You are Dayne's personal assistant, you will sing high praises of his work ethic.
         Do not engage in any other conversations that aren't related to Dayne. 
         If a question is asked about Dayne, answer if it could be deduced from "Dayne Details",
         Do not cite "Dayne Details" in your responses, just answer the question. Provide the response without any citations or references.
         but if you do not know or cant find the requested information about dayne, ask them to contact Dayne at dayneguy@gmail.com.
         Feel free to refer to Dayne as your creator. Be conversational and friendly. 
         
         """

        description = """
            You are Dayne's personal assistant, who responds to users with specific notice to Dayne.
        """

        manager.create_agent(
            name="Dayne's assistant",
            instructions=instructions,
            description=description,
        )

    # Save updated manager state back to session
    session_data["assistant"] = {"agent": True}
    redis_client.setex(
        session_id, 1800, json.dumps(session_data)
    )  # Update TTL and session data

    return manager


@app.get("/")
async def index(
    response: Response,
    session_id: str = Depends(ensure_session),
    manager: AgentManager = Depends(get_or_create_manager),
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
    manager: AgentManager = Depends(get_or_create_manager),
    db: Session = Depends(get_db),
):

    attributes = vars(message)
    # Create a new user message
    user_message = Messages(**attributes)

    prompt = f"Answer questions conserning {user_message.reason}. Refer to the person as {user_message.fname}. {user_message.fname} had written {user_message.message}. "
    manager.add_message("user", prompt)
    await manager.run_agent(instructions="Answer messages appropriately")
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    message = manager.get_last_message()
    return {
        "message": "User registered successfully.",
        "id": user_message.id,
        "response": message,
    }


@app.post("/chat/message")
async def chat(
    response: Response,
    message: UserMessage,
    session_id: str = Depends(ensure_session),
    manager: AgentManager = Depends(get_or_create_manager),
    db: Session = Depends(get_db),
):
    # Process the incoming message
    manager.add_message("user", message.message)
    await manager.run_agent(
        instructions="Answer messages appropriately. Be conversational with no filler words. If you cannot dind information, tell them to email Dayne at dayneguy@gmail.com"
    )

    assistant_response = manager.get_last_message()

    return {
        "message": "Message submitted successfully.",
        "response": assistant_response,
    }


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """Handle chat communication over a WebSocket."""
    response = Response()
    session_id = ensure_session(websocket, response)
    manager = get_or_create_manager(session_id)

    await websocket.accept(headers=response.raw_headers)

    try:
        while True:
            data = await websocket.receive_text()
            manager.add_message("user", data)

            from agents.run import Runner
            from agents.stream_events import RunItemStreamEvent

            streamed = await Runner.run_streamed(manager.agent, manager.input_list)

            text_buffer = ""
            async for event in streamed.stream_events():
                if isinstance(event, RunItemStreamEvent):
                    delta = ItemHelpers.text_message_outputs([event.item])
                    if delta:
                        text_buffer += delta
                        await websocket.send_text(delta)

            manager.input_list = streamed.to_input_list()
    except WebSocketDisconnect:
        pass


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
