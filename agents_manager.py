from openai import OpenAI
from agents import (
    Agent,
    run,
    FileSearchTool,
    CodeInterpreterTool,
    function_tool,
    ItemHelpers,
)
import os
from registry import Registry


class AgentManager:
    """Manage an OpenAI Agent and conversation state."""

    def __init__(self, model: str = "gpt-4o", registry: Registry | None = None) -> None:
        api_key = os.getenv("JOB_API")
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.registry = registry or Registry()
        self.agent: Agent | None = None
        self.input_list: list = []
        self.result = None
        self.vector_store_id: str | None = None

    def _registry_tools(self):
        tools = []
        for tool in self.registry.manager.values():
            wrapped = function_tool(tool.func)
            tools.append(wrapped)
        return tools

    def connect_confirm(self) -> dict:
        return {"status": "Agent ready"}

    def enable_file_search(self) -> None:
        vector_store = self.client.beta.vector_stores.create(name="Dayne Details")
        file_paths = ["api/dayne.json"]
        file_streams = [
            open(os.path.join(os.path.dirname(__file__), p), "rb") for p in file_paths
        ]
        self.client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id, files=file_streams
        )
        self.vector_store_id = vector_store.id

    def create_agent(self, name: str, instructions: str, description: str = "") -> None:
        if not self.vector_store_id:
            self.enable_file_search()
        tools = self._registry_tools()
        tools.append(FileSearchTool(vector_store_ids=[self.vector_store_id]))
        tools.append(CodeInterpreterTool({}))
        self.agent = Agent(
            name=name, instructions=instructions, model=self.model, tools=tools
        )

    def add_message(self, role: str, content: str) -> None:
        self.input_list.append({"role": role, "content": content})

    async def run_agent(self, instructions: str = "") -> None:
        if not self.agent:
            raise RuntimeError("Agent not created")
        agent = (
            self.agent
            if not instructions
            else self.agent.clone(instructions=instructions)
        )
        self.result = await run(agent, self.input_list)
        self.input_list = self.result.to_input_list()

    def get_last_message(self) -> str | None:
        if not self.result:
            return None
        return ItemHelpers.text_message_outputs(self.result.new_items)
