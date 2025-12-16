#!/bin/bash
uv run langgraph dev --allow-blocking --host 0.0.0.0 --port 2024 &
sleep 3
uv run python file_main.py