from pydantic import BaseModel, Field
from typing import Callable, Any, Dict


class Tool(BaseModel):
    func: Callable[[], Any]
    handler: Callable
    __name__: str  # Stores the name of the function

    def __init__(self, func: Callable[[], Any], handler: Callable):
        super().__init__(func=func, handler=handler)
        object.__setattr__(self, "__name__", func.__name__)


class Registry(BaseModel):
    manager: Dict[str, Tool] = Field(
        default_factory=dict
    )  # Initialize as an empty dictionary

    def register_tool(self, tool: Tool):
        # Add the tool to the manager using its __name__
        self.manager[tool.__name__] = tool

    def call(self, tool_name: str, *args, **kwargs):
        # Call the handler of the specified tool by its name
        if tool_name in self.manager:
            return self.manager[tool_name].handler(
                self.manager[tool_name].func, **kwargs
            )
        else:
            raise ValueError(f"Tool '{tool_name}' not found in registry.")

    def __getitem__(self, item: str) -> Tool:
        # Implement subscriptable access for the registry
        if item in self.manager:
            return self.manager[item]
        else:
            raise KeyError(f"Tool '{item}' not found in registry.")

    def model_dump(self, **kwargs):
        # Serialize the manager, calling `model_dump` on each Tool
        return {
            "manager": {name: tool.model_dump() for name, tool in self.manager.items()}
        }
