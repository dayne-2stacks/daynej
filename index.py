
from dotenv import load_dotenv
import os
from event_handlers.dispatcher import EventHandler 
from helper import function_to_schema, execute_tool_call, get_assistant, get_thread
from managers import AssistantManager, search
from registry import Tool, Registry

def hello():
    """ When a user says "hi" you should call this function"""
    print("Hello")
    return "Talk to John like he is your best friend from Junior College"


def main():

    manager = AssistantManager()

    toolkit = [hello]

    def hello_helper(hello):
        output = hello()
        return output

    helpers = [hello_helper]

    registry = Registry()
    
    # Loop to register each tool
    for func, helper in zip(toolkit, helpers):
        registry.register_tool(Tool(func, helper))

    manager.add_registry(registry)

    tools =[function_to_schema(tool) for tool in toolkit]


    print(registry.model_dump())
    # Create Assistant
    manager.create_assistant(
        name="Dayne's assistant",
        instructions="You are Dayne's personal assistant, you will sing high praises of his ethic",
        tools=tools
                             )
    # Create Thread
    manager.create_thread()

    
    # Add message to thread
    manager.add_message_to_thread(
        role="user",
        content="Hi"
    )

    # run assistant
    manager.run_assistant(instructions="Answer messages appropriately")
    # Wait for completion
    manager.wait_for_completion()

    # print(manager.run_steps())
    # manager.process_messages()
    





    # # Load environment variables
    # load_dotenv()

    
    # tools=[hello]
    # tool_schemas = [function_to_schema(tool) for tool in tools]

    # assistant_id = get_assistant(client, tool_schemas)

    # thread_id = get_thread(client)

    # tools_map = {func.__name__ : func for func in tools}

    # messages = []

    # # Create a user message in the conversation thread with the provided input
    # message = client.beta.threads.messages.create(
    #     thread_id=thread_id,
    #     role="user",  # Designates the message as coming from the user
    #     content=f"""Hi, Today I wanted to learn more about Dayne Guy"""  # User's input content
    # )
    
    # messages.append(message)

    # prompt = input("How may I assist you?\n")

    # # Create a user message in the conversation thread with the provided input
    # message = client.beta.threads.messages.create(
    #     thread_id=thread_id,
    #     role="user",  # Designates the message as coming from the user
    #     content=f"""Hi, Today I wanted to learn more about {prompt}"""  # User's input content
    # )

    # messages.append(message)
    
    # with client.beta.threads.runs.stream(
    #     thread_id=thread_id,
    #     assistant_id=assistant_id,
    #     instructions="As a personal assistant, answer any questions related to my skills and qualifications and treat guests with hospitality",
    #     event_handler=EventHandler(client=client, registry=tools_map),
    # ) as stream:
    #     stream.until_done()




if __name__=="__main__":
    main()