import inspect
import json
import os

def execute_tool_call(tool_call, tools_map):
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)

    try:
        print(f"Assistant: {name}({args})")
        return tools_map[name](**args)
    except Exception as e:
        print(f"Error executing tool {name}: {e}")
        return None


def function_to_schema(func) -> dict:
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null",
    }

    try:
        signature = inspect.signature(func)
    except ValueError as e:
        raise ValueError(
            f"Failed to get signature for function {func.__name__}: {str(e)}"
        )

    parameters = {}
    for param in signature.parameters.values():
        try:
            param_type = type_map.get(param.annotation, "string")
        except KeyError as e:
            raise KeyError(
                f"Unknown type annotation {param.annotation} for parameter {param.name}: {str(e)}"
            )
        parameters[param.name] = {"type": param_type}

    required = [
        param.name
        for param in signature.parameters.values()
        if param.default == inspect._empty
    ]

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": (func.__doc__ or "").strip(),
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required,
            },
        },
    }


def get_assistant(client, tool_schemas) -> str:
    assistant_id = ""
    # Check if an assistant ID exists in the environment, otherwise create one
    if os.getenv("ASSISTANT_ID"):
        assistant_id = os.getenv("ASSISTANT_ID")
    else:
        # Create a new assistant with specified instructions and tools
        assistant = client.beta.assistants.create(
            name="Dayne's Assistant",
            instructions=(
                "You are Dayne's personal assistant. You will respond to prospective employers and "
                "discuss Dayne's qualifications based on their company or specific role."
            ),
            tools=tool_schemas,
            model="gpt-4o",  # Specify the advanced model to use
        )
        # Save the assistant ID for future use
        assistant_id = assistant.id
        with open(".env", "a") as env_file:
            env_file.write(f"ASSISTANT_ID={assistant_id}\n")

    return assistant_id


def get_thread(client) -> str:
    # Check if a thread ID exists in the environment, otherwise create one
    if os.getenv("THREAD_ID"):
        thread_id = os.getenv("THREAD_ID")
    else:
        # Start a new conversation thread for the assistant
        thread = client.beta.threads.create()
        thread_id = thread.id
        # Save the thread ID for future use
        with open(".env", "a") as env_file:
            env_file.write(f"THREAD_ID={thread_id}\n")

    return thread_id