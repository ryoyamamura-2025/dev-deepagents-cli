---
name: auto-brainstorming
description: This skill facilitates a design-thinking brainstorming session with multiple AI personas to generate and refine a product concept. It focuses on deep diving into user pain points, uncovering latent needs, and creating a convincing narrative. Use this when you need a well-structured concept story, not just a business plan.
---

# Design Thinking Brainstorming

This skill guides the agent to simulate a brainstorming session with a team of specialized AI personas, following a design thinking approach.

## Workflow

**IMPORTANT: Minimal Output Protocol**
This skill is designed to run as a backend process. Do NOT output long text or opinions directly to the user chat. Instead:
*   Perform all work by writing to files in the session directory.
*   Keep your status updates concise (e.g., "Phase 1 complete. Saved to `01_initial_positions.md`. Proceeding to Phase 2.").
*   Do not pollute the context with the full content of the brainstorming.

### Phase 1: Empathize & Define (Deep Dive)

1.  **Understand the Theme:** Read the user's request to understand the core theme.
2.  **Create Session Directory:** Create a directory named `brainstorming_session_{timestamp}` (or a relevant name based on the theme) to store all artifacts.
3.  **Load Personas:** Load the profile for each persona from the `references/` directory:
    *   `product_manager.md` (Facilitator)
    *   `user_researcher.md`
    *   `concept_designer.md`
    *   `critical_strategist.md`
    *   `solution_architect.md`
4.  **Initial Exploration (Parallel Tasks):** 
    *   Use the `task` tool to launch subagents for each persona (User Researcher, Concept Designer, Critical Strategist, Solution Architect) in parallel.
    *   **Instruction to Subagents:** "Adopt the persona defined in [file]. Analyze the theme '[theme]'. Write your initial deep-dive analysis and opinions to a file named `[role]_initial.md`."
    *   Wait for all tasks to complete.
5.  **Consolidate Initial Thoughts:** Read the output files from the subagents and combine them into a single file `[session_dir]/01_initial_positions.md`.

### Phase 2: Parallel Ideation & Deep Dive (Dynamic Breakout Sessions)

This phase utilizes the parallel processing power of AI to run multiple "Breakout Rooms" simultaneously. Instead of a fixed structure, the Product Manager dynamically defines the breakout rooms based on the key conflicts identified in Phase 1.

1.  **Define Breakout Strategy:**
    *   **Act as Product Manager:** Analyze `01_initial_positions.md`.
    *   **Identify Key Conflicts:** What are the biggest tensions? (e.g., "Innovation vs. Regulation", "Short-term profit vs. Long-term brand", "Hardware vs. Software").
    *   **Define Rooms:** Create 2-3 specific "Breakout Rooms" to explore these tensions in isolation. Assign relevant personas to each room.
        *   *Example:* Room A: "Radical Innovation" (Concept Designer + User Researcher).
        *   *Example:* Room B: "Risk & Feasibility" (Critical Strategist + Solution Architect).
    *   **Write Strategy:** Save the room definitions and specific instructions for each room to `02_breakout_strategy.md`.

2.  **Launch Parallel Breakout Rooms:**
    *   Use the `task` tool to launch the defined breakout sessions simultaneously.
    *   **Instructions to Subagents:** 
        *   "Read `01_initial_positions.md` to understand the full context and initial viewpoints."
        *   "You are in [Room Name]. Your specific goal is [Goal]. Adopt the persona of [Role]."
        *   "Discuss deeply with [Other Personas]. Build upon the initial findings but focus intensely on your room's specific goal."
        *   "Output your transcript to `02_transcript_[room_name].md`."

3.  **Review & Synthesis (The "Clash"):**
    *   The **Product Manager** reads all transcript files.
    *   **Identify the Gap:** Where do the conclusions of the rooms clash?
    *   **Integration:** Synthesize a solution that bridges these diverse perspectives.
    *   **Output:** Write the synthesis logic and the integrated discussion points to `02_discussion_integrated.md`.

### Phase 3: Convergence & Final Proposal

1.  **Analyze the Discussion:** Review `02_discussion_integrated.md` (and the raw transcripts if needed).
2.  **Draft the Concept Story:** The **Product Manager** synthesizes the final output.
    *   **Load Template:** Read the template file at `references/concept_template.md`.
    *   **Instruction:** Write the final document by strictly following the structure and instructions in the template. Fill in each section with rich detail derived from the Phase 2 discussions.
    *   **Goal:** Create a high-quality "Product Concept Proposal" that serves as a standalone planning document.
3.  **Save Final Output:** Save this comprehensive concept story to `[session_dir]/03_final_concept_story.md`.
4.  **Final Notification:** Inform the user that the session is complete and list the generated file paths.
