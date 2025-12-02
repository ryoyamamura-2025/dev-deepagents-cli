import asyncio
from datetime import datetime
from typing import List, Tuple

from deepagents_cli.agent import create_agent_with_config
from deepagents_cli.config import create_model, settings
from deepagents_cli.tools import fetch_url, http_request, web_search
from nicegui import Client, ui

# 1. Agent Setup
# -----------------------------------------------------------------------------
try:
    model = create_model()
    tools = [http_request, fetch_url]
    if settings.has_tavily:
        tools.append(web_search)

    ASSISTANT_ID = "deepagents-webapp"
    agent, _ = create_agent_with_config(model, ASSISTANT_ID, tools)
    agent_ready = True
except Exception as e:
    agent_ready = False
    agent_error_message = str(e)
# -----------------------------------------------------------------------------


# In-memory message storage
messages: List[Tuple[str, str]] = []

# 2. Backend Logic for Streaming
# -----------------------------------------------------------------------------
async def stream_agent_response(message: str):
    """Streams the agent's response."""
    if not agent_ready:
        yield f"Agent could not be initialized: {agent_error_message}"
        return

    try:
        response_stream = agent.chat(message, stream=True)
        async for chunk in response_stream:
            yield chunk
    except Exception as e:
        # This will catch errors during the chat execution
        yield f"An error occurred while communicating with the agent: {e}"
# -----------------------------------------------------------------------------


# 3. NiceGUI User Interface
# -----------------------------------------------------------------------------
@ui.page('/')
async def chat_page(client: Client):

    def send() -> None:
        """Handles sending a message and starting the agent response stream."""
        user_message = text.value
        if not user_message:
            return

        # Add user message to UI
        messages.append(('You', user_message))
        chat_messages.render_messages()  # Use the refreshable function directly
        
        # Add a placeholder for the agent's response
        messages.append(('Agent', ''))
        chat_messages.render_messages()
        
        text.value = ''
        
        # Stream the agent's response
        async def stream_response():
            full_response = ""
            async for chunk in stream_agent_response(user_message):
                full_response += chunk
                messages[-1] = ('Agent', full_response)
                chat_messages.render_messages()

        asyncio.create_task(stream_response())

    # Styling
    ui.add_head_html('''
        <style>
            .chat-window {
                height: calc(100vh - 150px);
                overflow-y: auto;
            }
            .user-message { background-color: #e0f7fa; }
            .agent-message { background-color: #f1f8e9; }
        </style>
    ''')

    # Main layout
    with ui.column().classes('w-full max-w-3xl mx-auto items-stretch'):
        # Header
        ui.label('DeepAgents Web UI').classes('text-2xl font-bold text-center my-4')
        
        # Display error if agent failed to initialize
        if not agent_ready:
            ui.label(f'Agent Error: {agent_error_message}').classes('text-red-500 bg-red-100 p-4 rounded')

        # Chat messages area
        @ui.refreshable
        def chat_messages():
            with ui.column().classes('w-full flex-grow chat-window border rounded p-4'):
                for source, content in messages:
                    with ui.row().classes('w-full no-wrap'):
                        ui.avatar(
                            '🧑‍💻' if source == 'You' else '🤖',
                            size='sm',
                        )
                        ui.markdown(content).classes(
                            'p-2 rounded-lg',
                            'user-message' if source == 'You' else 'agent-message'
                        )
        chat_messages()


        # Input area
        with ui.row().classes('w-full items-center p-4'):
            with ui.input(placeholder='Ask the agent...').classes('flex-grow').on('keydown.enter', send, throttle=0.5) as text:
                ...
            ui.button('Send', on_click=send, disabled=not agent_ready)

# Run the app
ui.run()
