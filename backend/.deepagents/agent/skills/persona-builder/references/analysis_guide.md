# Persona Analysis Guide

This guide defines how to extract persona attributes from logs and conversation history.

## Table of Contents
1. [Extraction Framework](#1-extraction-framework) - What to extract (Core Values, Decision Making, Communication, Knowledge)
2. [Integration & Update Protocol](#2-integration--update-protocol) - How to update existing personas (Confirmation, Refinement, Contradiction Resolution)
3. [Standardized Analysis Output Format](#3-standardized-analysis-output-format) - Required format for analysis summaries

## 1. Extraction Framework

When analyzing logs, identify the following elements to build a high-fidelity persona.

### A. Core Values & Priorities (価値観・優先順位)
*   **What matters most?** (e.g., Speed, Quality, Cost, Innovation, Stability, User Experience)
*   **Trade-offs:** When forced to choose, what do they sacrifice? (e.g., "Launch now, fix later" vs "Delay for perfection")
*   **Motivation:** What drives them? (e.g., Solving hard problems, Helping others, Winning market share)

### B. Decision Making Process (意思決定プロセス)
*   **Input Data:** What information do they request before deciding? (e.g., KPIs, Customer anecdotes, Competitor analysis)
*   **Logic:** How do they connect facts to conclusions? (e.g., Deductive, Inductive, Analogical)
*   **Risk Tolerance:** Are they risk-averse or risk-seeking?
*   **Authority:** Do they decide alone or seek consensus?

### C. Communication Style (コミュニケーションスタイル)
*   **Tone:** Formal, Casual, Direct, Diplomatic, Enthusiastic, Cynical.
*   **Length:** Bullet points vs Narrative paragraphs.
*   **Key Phrases:** Recurring idioms, catchphrases, or sentence structures (e.g., "Let's take a step back," "To be honest," "Just ship it").
*   **Feedback Style:** Constructive, Critical, Socratic (asking questions), Supportive.

### D. Knowledge Base & Expertise (知識・専門性)
*   **Domain Knowledge:** Specific technical topics, industries, or historical context they reference.
*   **Blind Spots:** Areas they explicitly delegate or admit ignorance about.

## 2. Integration & Update Protocol

When processing NEW logs to update an EXISTING persona:

### A. Confirmation (強化)
*   If new behavior matches existing traits, increase the confidence level of that trait.
*   Add the new example to the "Few-Shot Examples" section.

### B. Refinement (洗練)
*   If new behavior adds nuance (e.g., "Usually risk-averse, BUT takes risks when competitor X is involved"), update the trait with this condition.

### C. Contradiction Resolution (矛盾解消)

When new logs contradict existing persona traits, follow this decision tree:

1. **Check Context First:**
   *   **Different situation?** (e.g., Formal meeting vs Casual chat, Internal vs External, Crisis vs Normal operation)
   *   → **Action:** Add conditional logic: "In [context X], [behavior Y]; otherwise [default behavior Z]"
   *   **Example:** "Usually risk-averse, BUT takes calculated risks during product launches when market timing is critical."

2. **Check Temporal Order:**
   *   **More recent data?** (Check file dates/timestamps)
   *   → **Action:** If new log is significantly more recent (>3 months), prioritize new behavior and mark old as "evolved"
   *   **Example:** "Previously preferred detailed reports, but now favors concise summaries (as of 2025-06)."

3. **Check Frequency:**
   *   **One-off vs Pattern?** Count occurrences in logs
   *   → **Action:** If contradiction appears only once, mark as exception: "Exception: [specific context] where [different behavior]"
   *   → **Action:** If contradiction appears 2+ times, it's a pattern - update the trait with conditional logic
   *   **Example:** "Exception: Uses formal tone in client-facing emails, but casual in internal team chats."

4. **Check Source Reliability:**
   *   **Different log types?** (Meeting notes vs Chat logs vs Emails)
   *   → **Action:** Prioritize in this order: (1) Direct quotes from person, (2) Meeting transcripts, (3) Chat logs, (4) Third-party descriptions
   *   **Example:** If meeting transcript shows direct quote contradicting email summary, trust the transcript.

5. **Default Rule:**
   *   If none of the above apply, **prioritize recent data** and add a note: "Updated based on recent evidence from [date]."

## 3. Standardized Analysis Output Format

For each analyzed log file, generate a summary using this **exact structure** before updating the main profile. This ensures consistency and completeness:

```markdown
### Log Analysis Summary: [Filename]
**Context:** [Meeting/Chat/Email] about [Topic]
**Date:** [YYYY-MM-DD if available]
**Source Type:** [Direct transcript / Summary / Third-party notes]

**A. Core Values & Priorities:**
*   [Value 1]: [Evidence/Quote with line number or timestamp if available]
*   [Value 2]: [Evidence/Quote]
*   Trade-offs observed: [What they prioritize when forced to choose]

**B. Decision Making Process:**
*   Input Data requested: [What information they asked for]
*   Logic pattern: [Deductive/Inductive/Analogical - with example]
*   Risk tolerance: [Evidence/Quote showing risk-averse or risk-seeking]
*   Authority style: [Solo decision / Consultative / Consensus - with example]

**C. Communication Style:**
*   Tone: [Formal/Casual/Direct/etc. - with quote example]
*   Key phrases/catchphrases: [Exact quotes, frequency if notable]
*   Feedback style: [Constructive/Critical/Socratic/Supportive - with example]

**D. Knowledge & Expertise:**
*   Domain knowledge referenced: [Specific topics, technologies, concepts]
*   Blind spots mentioned: [Areas they delegate or admit ignorance]

**E. Conflicts/Contradictions:**
*   [If any contradictions with existing persona:]
  *   Contradiction: [Description]
  *   Resolution approach: [Contextualize/Evolution/Anomaly - per Section 2.C]
  *   Final decision: [How to update persona]

**F. Recommended Updates:**
*   New traits to add: [List]
*   Existing traits to refine: [List with new nuance]
*   Examples to add to Few-Shot: [Specific quotes with context]
```

**Completeness Checklist:** Before proceeding to persona update, ensure each section (A-D) has at least one item. If a section is empty, explicitly note "No new evidence found" to confirm the section was reviewed.
