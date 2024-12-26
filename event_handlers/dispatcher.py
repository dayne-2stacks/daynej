from typing_extensions import override
from openai import AssistantEventHandler
from helper import execute_tool_call

class EventHandler(AssistantEventHandler):
  def __init__(self, client, registry):
    super().__init__()
    self.client = client
    self.registry = registry

  @override
  def on_event(self, event):
    # Retrieve events that are denoted with 'requires_action'
    # since these will have our tool_calls
    if event.event == 'thread.run.requires_action':
      run_id = event.data.id  # Retrieve the run ID from the event data
      self.handle_requires_action(event.data, run_id)

  def handle_requires_action(self, data, run_id):
    tool_outputs = []
      
    for tool in data.required_action.submit_tool_outputs.tool_calls:
      execute_tool_call(tool, self.registry)
      
    # Submit all tool_outputs at the same time
    self.submit_tool_outputs(tool_outputs, run_id)

  def submit_tool_outputs(self, tool_outputs, run_id):
    # Use the submit_tool_outputs_stream helper
    with self.client.beta.threads.runs.submit_tool_outputs_stream(
      thread_id=self.current_run.thread_id,
      run_id=self.current_run.id,
      tool_outputs=tool_outputs,
      event_handler=EventHandler(self.client, self.registry),
    ) as stream:
      for text in stream.text_deltas:
        print(text, end="", flush=True)
      print()


