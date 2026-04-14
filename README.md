 1. # AI Chief of Staff API CLI System for Autonomous Task Decision Execution

## Problem

Manual business operations are messy and inefficient.

## Solution

AI Chief of Staff that automates task extraction and execution.

## Architecture

(Diagram — even if simple)

### High-Level Architecture

We have the API and CLI for testing.

```
Input (CLI/API)
   ↓
Orchestrator (CrewAI)
   ↓
Agent Loop (Generate → Critique → Refine)
   ↓
Tool Execution Layer
   ↓
Memory (MongoDB)
   ↓
Response (JSON + Summary)
```

## Features

- Multi-agent system
- Memory
- Tool execution
- API + CLI

## Demo

### POST /process

**Input:**

```json
{
  "text": "We need to prepare the investor report by Friday. John should handle the financials. Also schedule a follow-up meeting."
}
```

**Output:**

```json
{
  "tasks": [
    {
      "title": "Prepare investor report",
      "owner": "John",
      "deadline": "Friday"
    },
    {
      "title": "Schedule follow-up meeting",
      "owner": null,
      "deadline": null
    }
  ],
  "decisions": [],
  "risks": [],
  "summary": "Two tasks identified..."
}
```

### GET /tasks

Returns stored tasks from MongoDB.


