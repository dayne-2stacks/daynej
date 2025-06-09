from openai import OpenAI
import os
import time
import json
import requests
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
from registry import Registry
from dotenv import load_dotenv


def get_article_body(article_url):
    response = requests.get(article_url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")

        # Use the correct tag/class to extract the article body
        # Adjust 'div.article-body' based on the actual structure of the article page
        body = soup.find("article", class_="post")

        if body:
            # Get text content and clean it up
            return body.get_text(strip=True)
        else:
            print(f"Could not find article body for {article_url}")
            return None
    else:
        print(f"Failed to fetch article: {response.status_code}")
        return None


def hello():
    """When a user says "hi" you should call this function"""
    print("Hello")
    return "Talk to John like he is your best friend from Junior College"


def search():
    """When a user asks you about the news you should call this function"""
    url = "https://edition.channel5belize.com/post-sitemap.xml"
    response = requests.get(url)

    if response.status_code == 200:
        # Parse the XML content
        tree = ET.fromstring(response.content)
        articles = []

        # Extract all <loc> tags (which usually contain the URLs of the articles)
        for url in tree.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
            articles.append(url.text)

        articles = articles[:10]

        recent_articles = []
        for url in articles:
            print(f"Fetching body for: {url}")
            article_body = get_article_body(url)
            recent_articles.append(article_body)
            if article_body:
                print(f"Article Body: {article_body}\n")
            else:
                print("No content found.\n")

        return recent_articles
    else:
        print(f"Failed to fetch sitemap: {response.status_code}")
        return []


# Load the .env file
load_dotenv()

# Get open ai API key
api_key = os.getenv("JOB_API")


# initialize a client
client = OpenAI(api_key=api_key)


class AssistantManager:
    thread_id = None
    assistant_id = None

    def __init__(self, model: str = "gpt-4o", registry=None) -> None:
        self.client = client
        self.model = model
        self.assistant = None
        self.thread = None
        self.run = None
        self.summary = None
        self.registry = registry or Registry()

        if AssistantManager.assistant_id:
            self.assistant = self.client.beta.assistants.retrieve(
                assistant_id=AssistantManager.assistant_id
            )

        if AssistantManager.thread_id:
            self.thread = self.client.beta.threads.retrieve(
                thread_id=AssistantManager.thread_id
            )

    def connect_confirm(self):
        return {
            "status": "Manager created!",
            "assistant_id": self.assistant.id,
            "thread_id": self.thread.id,
        }

    def create_assistant(self, name, instructions, description="", tools=[]):
        if not tools:
            tools = [{"type": "file_search"}, {"type": "code_interpreter"}]
        else:
            tools += [{"type": "file_search"}, {"type": "code_interpreter"}]
        if not self.assistant:
            assistant_obj = self.client.beta.assistants.create(
                name=name,
                instructions=instructions,
                description=description,
                tools=tools,
                model=self.model,
            )
            AssistantManager.assistant_id = assistant_obj.id
            self.assistant = assistant_obj
            self.enable_file_search()
            print(assistant_obj)

    def create_thread(self):
        if not self.thread:
            thread_obj = self.client.beta.threads.create()
            AssistantManager.thread_id = thread_obj.id
            self.thread = thread_obj

    def add_message_to_thread(self, role, content):
        if self.thread:
            self.client.beta.threads.messages.create(
                thread_id=self.thread.id, role=role, content=content
            )

    def enable_file_search(self):
        # Create a vector store caled "Financial Statements"
        vector_store = self.client.beta.vector_stores.create(name="Dayne Details")

        # Ready the files for upload to OpenAI
        file_paths = ["api/dayne.json"]
        file_streams = [
            open(os.path.join(os.path.dirname(__file__), path), "rb")
            for path in file_paths
        ]

        # Use the upload and poll SDK helper to upload the files, add them to the vector store,
        # and poll the status of the file batch for completion.
        file_batch = self.client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id, files=file_streams
        )
        print(f"File batch uploaded: {file_batch.id}")

        self.client.beta.assistants.update(
            assistant_id=self.assistant.id,
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
        )

        print(f"Updated Assitant with Vector store: {vector_store.id}")

    def add_registry(self, registry):
        self.registry = registry

    def run_assistant(self, instructions):
        if self.assistant and self.thread:
            self.run = self.client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id,
                instructions=instructions,
            )

    def get_last_message(self):
        if self.thread:
            messages = self.client.beta.threads.messages.list(
                thread_id=self.thread_id,
            )
            last_message = messages.data[0]
            return last_message

    def process_messages(self):
        if self.thread:

            summary = []
            last_message = self.get_last_message()
            print(f"Last Message ->>> {last_message}")
            response = last_message.content[0].text.value
            role = last_message.role
            summary.append(response)
            self.summary = "\n".join(summary)
            print(f"SUMMARY---> {role.capitalize()}: ==> {response}")

    def call_required_functions(self, required_actions):
        if not self.run:
            return
        tool_outputs = []

        for action in required_actions["tool_calls"]:
            func_name = action["function"]["name"]
            args = json.loads(action["function"]["arguments"])
            if func_name in self.registry.manager.keys():
                output = self.registry.call(func_name, **args)
                tool_outputs.append({"toolcall_id": action["id"], "output": output})
            else:
                raise ValueError(f"Unknown function: {func_name}")
        print("SUBMITTING TOOLS BACK TO ASSISTANT")
        self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread.id, run_id=self.run.id, tool_outputs=tool_outputs
        )

    def wait_for_completion(self):
        if self.thread and self.run:
            while True:
                time.sleep(0.5)
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread.id, run_id=self.run.id
                )
                print(f"RUN STATUS ---> {run_status.model_dump_json(indent=4)}")

                if run_status.status == "completed":
                    self.process_messages()
                    break
                elif run_status.status == "requires_action":
                    print("FUNCTIONS CALLING NOW")
                    self.call_required_functions(
                        required_actions=run_status.required_action.submit_tool_outputs.model_dump()
                    )

    def run_steps(self):
        run_steps = self.client.beta.threads.runs.steps.list(
            thread_id=self.thread.id, run_id=self.run.id
        )

        print(f"Run Steps::: {run_steps}")
        return run_steps.data


if "__main__" == __name__:
    assistant = AssistantManager()
    assistant.create_assistant(name="DJ", instructions="You are a chatbot", tools=None)

    # assistant.client.beta.assistants.retrieve(assistant_id='asst_812CIMTS6q8O5d0yTXp67iav')

    assistant.create_thread()
    assistant.add_message_to_thread(
        role="user", content="Would Dayne be a good fit for a software engineer role?"
    )

    assistant.run_assistant("Answer the questions")

    assistant.wait_for_completion()
    print(f"{assistant.get_last_message()}")
