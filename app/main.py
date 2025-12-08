import asyncio
from typing import List, Tuple, AsyncGenerator, Dict, Any
from pathlib import Path
from nicegui import ui, app

# --- Project Directory Setup ---
PROJECT_DIR = Path('project')
PROJECT_DIR.mkdir(exist_ok=True)

# --- Placeholder for deepagents_cli ---
async def run_agent(message: str) -> AsyncGenerator[dict, None]:
    """A mock async generator to simulate the behavior of the deepagents_cli."""
    yield {'type': 'thinking', 'content': 'Analyzing the request...'}
    await asyncio.sleep(1)
    yield {'type': 'tool_call', 'content': 'Searching for information...'}
    await asyncio.sleep(2)
    yield {'type': 'final_response', 'content': f"This is the final answer to your message: '{message}'"}
# --- End of placeholder ---

# Set the title of the web page
ui.page_title('DeepAgents WebApp')

# Data structure for chat history
chat_history: List[Tuple[str, str]] = []


def get_file_icon(file_path: Path) -> str:
    """Get an appropriate icon for a file based on its extension."""
    if file_path.is_dir():
        return 'folder'
    
    ext = file_path.suffix.lower()
    icon_map = {
        '.py': 'code',
        '.js': 'javascript',
        '.ts': 'code',
        '.html': 'html',
        '.css': 'style',
        '.json': 'data_object',
        '.md': 'article',
        '.txt': 'description',
        '.yml': 'settings',
        '.yaml': 'settings',
        '.sh': 'terminal',
        '.env': 'key',
        '.toml': 'settings',
    }
    return icon_map.get(ext, 'description')


def build_file_tree_data(path: Path) -> List[Dict[str, Any]]:
    """Recursively build the data structure for the file tree."""
    nodes = []
    for p in sorted(path.iterdir()):
        node = {'id': str(p), 'label': p.name, 'path': p}
        if p.is_dir():
            node['children'] = build_file_tree_data(p)
            node['props'] = {'icon': 'folder'}
        else:
            node['props'] = {'icon': get_file_icon(p)}
        nodes.append(node)
    return nodes


# Header
with ui.header(elevated=True).style('background-color: #3874c8').classes('items-center justify-between'):
    ui.label('DeepAgents WebApp')


@ui.page('/')
def main_page():
    """Main page with file explorer and chat interface."""
    
    async def handle_file_select(e: any):
        """Handle the selection of a file in the file tree."""
        if not e.value:
            return

        file_path = Path(e.value)
        if file_path.is_dir():
            return

        try:
            content = file_path.read_text()
        except Exception as err:
            ui.notify(f"Error reading file: {err}", color='negative')
            return

        with ui.dialog() as dialog, ui.card().style('min-width: 80%; min-height: 80%'):
            with ui.row().classes('w-full justify-between items-center'):
                ui.label(f'Editing: {file_path.name}').classes('text-lg font-bold')
                ui.button(icon='close', on_click=lambda: close_with_check()).props('flat round dense')

            # Store original content for comparison
            original_content = content
            editor = ui.editor(value=content, on_change=None).classes('w-full flex-grow')
            
            # Track if there are unsaved changes
            has_unsaved_changes = {'value': False}
            
            def on_editor_change(e):
                has_unsaved_changes['value'] = editor.value != original_content
            
            editor.on('update:modelValue', on_editor_change)

            with ui.row().classes('w-full justify-between items-center'):
                unsaved_indicator = ui.label('').classes('text-sm text-orange-600')
                
                def update_unsaved_indicator():
                    if has_unsaved_changes['value']:
                        unsaved_indicator.text = '● Unsaved changes'
                    else:
                        unsaved_indicator.text = ''
                
                # Update indicator periodically
                ui.timer(0.5, update_unsaved_indicator)
                
                with ui.row().classes('gap-2'):
                    async def save_file():
                        try:
                            file_path.write_text(editor.value)
                            ui.notify(f"Saved {file_path.name}", color='positive')
                            has_unsaved_changes['value'] = False
                            nonlocal original_content
                            original_content = editor.value
                            await refresh_file_tree()
                        except Exception as err:
                            ui.notify(f"Error saving file: {err}", color='negative')
                    
                    ui.button('Save', icon='save', on_click=save_file).props('color=positive')
            
            async def close_with_check():
                if has_unsaved_changes['value']:
                    with ui.dialog() as confirm_dialog, ui.card():
                        ui.label('You have unsaved changes. Are you sure you want to close?')
                        with ui.row().classes('w-full justify-end gap-2'):
                            ui.button('Cancel', on_click=confirm_dialog.close)
                            ui.button('Close without saving', on_click=lambda: [confirm_dialog.close(), dialog.close()]).props('color=negative')
                    confirm_dialog.open()
                else:
                    dialog.close()

        dialog.open()

    async def refresh_file_tree():
        """Refresh the file tree by rebuilding it from the project directory."""
        file_tree_container.clear()
        tree_data = build_file_tree_data(PROJECT_DIR)
        with file_tree_container:
            ui.tree(tree_data, label_key='label', on_select=handle_file_select).props('dense')
        ui.notify('File tree refreshed', color='positive')

    async def show_new_file_dialog():
        """Show a dialog to create a new file."""
        with ui.dialog() as dialog, ui.card():
            ui.label('Create New File').classes('text-lg')
            file_name_input = ui.input(label='File name', placeholder='example.txt').classes('w-full')
            
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Cancel', on_click=dialog.close)
                
                async def create_file():
                    file_name = file_name_input.value.strip()
                    if not file_name:
                        ui.notify('Please enter a file name', color='negative')
                        return
                    
                    file_path = PROJECT_DIR / file_name
                    try:
                        if file_path.exists():
                            ui.notify(f'File {file_name} already exists', color='negative')
                            return
                        
                        file_path.write_text('')
                        ui.notify(f'Created {file_name}', color='positive')
                        dialog.close()
                        await refresh_file_tree()
                    except Exception as err:
                        ui.notify(f'Error creating file: {err}', color='negative')
                
                ui.button('Create', on_click=create_file)
        
        dialog.open()

    async def show_new_folder_dialog():
        """Show a dialog to create a new folder."""
        with ui.dialog() as dialog, ui.card():
            ui.label('Create New Folder').classes('text-lg')
            folder_name_input = ui.input(label='Folder name', placeholder='my-folder').classes('w-full')
            
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Cancel', on_click=dialog.close)
                
                async def create_folder():
                    folder_name = folder_name_input.value.strip()
                    if not folder_name:
                        ui.notify('Please enter a folder name', color='negative')
                        return
                    
                    folder_path = PROJECT_DIR / folder_name
                    try:
                        if folder_path.exists():
                            ui.notify(f'Folder {folder_name} already exists', color='negative')
                            return
                        
                        folder_path.mkdir(parents=True)
                        ui.notify(f'Created folder {folder_name}', color='positive')
                        dialog.close()
                        await refresh_file_tree()
                    except Exception as err:
                        ui.notify(f'Error creating folder: {err}', color='negative')
                
                ui.button('Create', on_click=create_folder)
        
        dialog.open()
    
    # Left drawer with file explorer
    with ui.left_drawer(value=True, bordered=True).classes('w-64'):
        with ui.row().classes('w-full items-center justify-between p-2'):
            ui.label('File Explorer').classes('text-lg')
            with ui.row().classes('gap-1'):
                ui.button(icon='add', on_click=lambda: show_new_file_dialog()).props('flat dense round').tooltip('New File')
                ui.button(icon='create_new_folder', on_click=lambda: show_new_folder_dialog()).props('flat dense round').tooltip('New Folder')
                ui.button(icon='refresh', on_click=lambda: refresh_file_tree()).props('flat dense round').tooltip('Refresh')
        file_tree_container = ui.column().classes('w-full')
    
    # Main content area with chat
    with ui.column().classes('w-full max-w-2xl mx-auto items-stretch'):
        chat_area = ui.column().classes('w-full')
    
    # Footer with input
    with ui.footer().style('background-color: #f0f0f0'):
        with ui.row().classes('w-full items-center'):
            user_input = ui.input(placeholder='Type your message...').classes('flex-grow')
            
            async def send_message():
                """Handles sending a message from the user and streaming the agent's response."""
                user_message = user_input.value
                if not user_message:
                    return

                chat_history.append(('user', user_message))
                with chat_area:
                    ui.chat_message(user_message, name='You', sent=True)
                user_input.value = ''

                with chat_area:
                    agent_message = ui.chat_message(name='Agent', sent=False)

                with agent_message:
                    with ui.expansion('思考プロセス', icon='psychology').classes('w-full') as expansion:
                        log = ui.column()
                    final_response_container = ui.column()

                async for event in run_agent(user_message):
                    if event['type'] in ['thinking', 'tool_call']:
                        with log:
                            ui.label(event['content'])
                    elif event['type'] == 'final_response':
                        with final_response_container:
                            ui.markdown(event['content'])
                        chat_history.append(('agent', event['content']))
                        expansion.set_visibility(False)
            
            user_input.on('keydown.enter', send_message)
            ui.button('Send', on_click=send_message)
    
    # Initialize file tree
    ui.timer(0.1, refresh_file_tree, once=True)


ui.run()
