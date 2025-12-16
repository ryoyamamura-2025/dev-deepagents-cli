---
name: persona-builder
description: Builds and updates an AI persona based on logs and conversation history. Use this skill when the user wants to create an agent that mimics a specific person's values and judgment, or when they want to update an existing persona with new log data.
---

# Persona Builder Skill

This skill allows you to build and maintain a high-fidelity AI persona by analyzing log files (meeting notes, chat logs, emails). It supports both **initial creation** and **incremental updates**.

## Workflow

Follow these steps to process logs and update the persona.

### Step 1: Discover New Logs

First, check for any unprocessed log files in the user's log directory.

1.  Ask the user for the **Log Directory** path (if not provided).
2.  Define the **History File** path (default: `[Log Directory]/persona_history.json`).
3.  Run the discovery script:
    ```bash
    uv run python scripts/manage_logs.py --log-dir [LOG_DIR] --history-file [HISTORY_FILE] --action check
    ```

### Step 2: Analyze Logs

If the script returns `new_files`:

1.  **Read the Analysis Guide**: Load `references/analysis_guide.md` to understand the extraction framework and standardized output format.
2.  **Read Log Files**: Read the content of the new files identified in Step 1.
3.  **Analyze Content**: For each file, create a standardized analysis summary following the format in Section 3 of `references/analysis_guide.md`. Extract:
    *   **Core Values**: What is prioritized? (with evidence quotes)
    *   **Decision Logic**: How are decisions made? (with examples)
    *   **Tone/Style**: Key phrases and speaking style. (exact quotes)
    *   **Knowledge Base**: Domain expertise and blind spots.
    *   **Conflicts/Changes**: Any contradictions with previous knowledge? (apply resolution protocol from Section 2.C)
4.  **Complete Analysis Checklist**: Ensure each analysis summary covers all sections (A-D) from the standard format. If a section has no evidence, explicitly note "No new evidence found" to confirm review.

### Step 3: Create or Update Persona

Check if a persona file already exists (e.g., `[Log Directory]/persona_definition.md` or a path specified by the user).

#### Scenario A: Creating a New Persona (First Run)
1.  Read the template: `assets/persona_template.md`.
2.  Fill in the template placeholders (`{{CORE_VALUES}}`, etc.) based on your analysis.
3.  Write the new file to `[Log Directory]/persona_definition.md` (or user-specified path).

#### Scenario B: Updating an Existing Persona
1.  Read the existing persona file.
2.  **Integrate New Findings**:
    *   **Reinforce**: Add new examples to "Few-Shot Examples" (include context for each example).
    *   **Refine**: Update values or logic descriptions if new nuances are found. Use conditional logic when context matters.
    *   **Resolve Contradictions**: Follow the decision tree in Section 2.C of `references/analysis_guide.md`:
      *   Check context differences first
      *   Check temporal order (prioritize recent if >3 months newer)
      *   Check frequency (one-off vs pattern)
      *   Check source reliability (direct quotes > transcripts > summaries)
      *   Default: prioritize recent data with note
3.  Overwrite the persona file with the updated content.

### Step 4: Quality Check

Before committing changes, verify the persona meets quality standards:

1.  **Completeness Check**: Ensure all required sections are present:
    *   Core Values & Principles (at least 2-3 items)
    *   Decision Making Style (with specific examples)
    *   Communication Profile (tone, catchphrases, feedback style)
    *   Knowledge & Context (domain knowledge, team/projects if relevant)
    *   Few-Shot Examples (at least 3-4 examples with context)

2.  **Evidence Check**: Verify every trait has supporting evidence:
    *   All values have quotes or examples from logs
    *   All catchphrases are exact quotes from logs
    *   All examples in "Few-Shot Examples" are real quotes with context

3.  **Specificity Check**: Ensure traits are specific, not generic:
    *   ❌ Bad: "Professional"
    *   ✅ Good: "Professional but uses casual humor to defuse tension in team meetings"
    *   ❌ Bad: "Makes decisions"
    *   ✅ Good: "Makes consultative decisions, asking 'What do you think?' before finalizing"

4.  **Consistency Check**: Review for internal contradictions:
    *   If conditional logic is used (e.g., "In situation X, does Y"), ensure it's clearly stated
    *   If contradictions were resolved, verify the resolution follows the protocol from Section 2.C of `references/analysis_guide.md`

5.  **Template Compliance**: Verify the persona follows the structure in `assets/persona_template.md`:
    *   All placeholders are filled
    *   Formatting matches the template
    *   Instructions section is included

If any check fails, revise the persona before proceeding to Step 5.

### Step 5: Commit Changes

After quality checks pass, mark the logs as processed to avoid re-analyzing them later.

1.  Run the mark script:
    ```bash
    uv run python scripts/manage_logs.py --log-dir [LOG_DIR] --history-file [HISTORY_FILE] --action mark --files [LIST_OF_PROCESSED_FILES]
    ```
    *(Note: If you processed all new files, you can omit `--files` to mark all pending files.)*

2.  Report the results to the user:
    *   Number of new files processed.
    *   Key updates made to the persona (e.g., "Added new decision rule regarding budget approval," "Updated tone to be more direct").
    *   Quality check results (brief summary: "All quality checks passed" or specific notes if any adjustments were made).

## Tips for High Quality

### Essential Principles
*   **Quote Verbatim**: When populating "Catchphrases" or "Examples", use exact quotes from the logs. Include context (e.g., "In team meetings, often says 'Hai, wakarimashita' to acknowledge before asking follow-up questions").
*   **Be Specific**: Avoid generic traits like "Professional." Use "Professional but uses sarcasm to defuse tension in team meetings when discussing technical challenges."
*   **Data-Driven**: Base every trait on evidence found in the logs. If you can't find evidence, don't include the trait.

### Analysis Best Practices
*   **Count Frequency**: If a phrase appears multiple times, note it (e.g., "'Hai' appears 15+ times in meeting transcripts").
*   **Context Matters**: Always note the context when extracting traits (e.g., "Uses formal tone in client emails, casual in internal chats").
*   **Look for Patterns**: Don't just extract single instances—identify recurring patterns across multiple log files.

### Writing Quality Persona Definitions
*   **Use Examples**: Every trait should have at least one concrete example in the "Few-Shot Examples" section.
*   **Show, Don't Tell**: Instead of "Direct communicator," show it: "Example: 'Let's cut to the chase. What's the blocker?'"
*   **Balance Detail**: Include enough detail to be useful, but avoid overwhelming with minutiae. Focus on distinctive traits that differentiate this person.
