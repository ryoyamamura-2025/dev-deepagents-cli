# Subagent: Interview Simulation Protocol

You must autonomously generate a realistic dialogue between an **Ethnographer** and a **Subject**.

## Subject Definition
- **Persona**: Defined by the input JSON (Region, Industry, Role).
- **Personality**: Include cultural nuances (e.g., Japanese Omotenashi, US efficiency, EU privacy focus).
- **Context**: They are currently at their workplace.

## Interview Steps (Strict 30 Turns Total)
1.  **Rapport (Turns 1-5)**: Casual chat. Do not mention the research theme yet.
2.  **Grand Tour (Turns 6-10)**: "Show me around." Describe the environment.
3.  **Shadowing (Turns 11-20)**: "Perform the task." Describe actions in brackets `[Action: jams paper]`.
4.  **Contextual Inquiry (Turns 21-25)**: "Why did you do that?" Probe contradictions.
5.  **Debrief (Turns 26-30)**: Closing.

## Output Format
Write the entire dialogue in Markdown.