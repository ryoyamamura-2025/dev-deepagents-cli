---
name: docx-creator
description: "Document creation with .docx file. When Agent needs to work with professional documents (.docx file) for: (1) Creating new documents, (2) Creating manuals with specialized page layouts and best practices for technical documentation, user guides, or procedural manuals"
---

# DOCX creation

## Overview

A user may ask you to create a .docx file. You have a workflow explained bellow.

## Creating a new Word document

When creating a new Word document from scratch, use **docx-js**, which allows you to create Word documents using JavaScript/TypeScript.

### Workflow
1. **MANDATORY - READ ENTIRE FILE**: Read [`docx-js.md`](docx-js.md) (~500 lines) completely from start to finish **NEVER set any range limits when reading this file.** Read the full file content for detailed syntax, critical formatting rules, and best practices before proceeding with document creation.
2. Create a JavaScript/TypeScript file using Document, Paragraph, TextRun components (You can assume all dependencies are installed, but if not, refer to the dependencies section below)
3. Export as .docx using Packer.toBuffer()

## Creating manuals

When creating manuals (technical documentation, user guides, or procedural manuals), follow specialized page layout best practices.

### Workflow for manual creation

1. **MANDATORY - READ ENTIRE FILE**: Read [`references/manual-layout.md`](references/manual-layout.md) completely from start to finish for detailed page layout guidelines, section structure, tag styling, screenshot placement, and best practices specific to manual creation.
2. Apply the recommended page layout structure: title page, table of contents, sections with proper spacing and visual hierarchy.
3. Use tag-based visual distinctions (Check, Analysis, Conclusion, etc.) with appropriate colors and styling.
4. Follow the screenshot placement guidelines for images with captions.
5. Ensure consistent styling throughout the manual using the provided style templates.

## Code Style Guidelines
**IMPORTANT**: When generating code for DOCX operations:
- Write concise code
- Avoid verbose variable names and redundant operations
- Avoid unnecessary print statements