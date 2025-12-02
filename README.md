# DeepAgents Web UI

This project provides a web-based user interface for the `deepagents` CLI tool, built with the [NiceGUI](https://nicegui.io/) framework.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd dev-deepagents-cli
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    The project uses `uv` for package management.
    ```bash
    pip install uv
    uv pip install -e .
    ```

4.  **Configure API Keys:**
    Create a `.env` file in the project root and add your API keys. At a minimum, you'll need the Google API key.
    ```
    GOOGLE_API_KEY="your-google-api-key"
    # Optional, for web search functionality
    TAVILY_API_KEY="your-tavily-api-key"
    ```

## Running the Web Application

To start the web-based chat interface, run the following command:

```bash
python -m app.web_ui
```

This will start a web server. You can access the UI by opening your browser and navigating to the URL displayed in the console (usually `http://localhost:8080`).

## Running the CLI

The original CLI interface is also available. You can run it with:

```bash
deepagents-cli
```