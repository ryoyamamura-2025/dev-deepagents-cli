---
name: video-analyzer
description: Analyze videos stored on GCS and generate structured JSON outputs. Use this skill when the user provides a video filename (e.g., xxxx.mp4) and a mode (summary, manual, or questions).
---

# Video Analyzer

This skill analyzes video content stored in GCS and outputs the results in a specified JSON format.
It supports two execution patterns: local script execution and API-based execution.

## Usage

When the user requests video analysis, confirm the `video_title` and `mode`.

### Parameters

- `video_title`: The filename of the video (e.g., `lecture.mp4`). Assumed to be on GCS.
- `mode`: Analysis mode. Must be one of:
    - `summary`: Generates a summary of the video.
    - `manual`: Generates a step-by-step manual from the video.
    - `questions`: Generates a set of practice questions based on the video.

## Execution Patterns

Choose the appropriate pattern based on the user's preference or system configuration.

### Pattern 1: Script Execution (Local Processing)

Use the python script to run the analysis locally.

```bash
uv run python {SKILL_DIR}/scripts/analyze_video_script.py --title "{video_title}" --mode "{mode}"
```

### Pattern 2: API Call (Remote Processing)

Use the python script that simulates an API call to a remote analysis service.

```bash
uv run python {SKILL_DIR}/scripts/analyze_video_api.py --title "{video_title}" --mode "{mode}"
```