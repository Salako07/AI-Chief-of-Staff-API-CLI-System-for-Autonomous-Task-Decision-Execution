 The High level architecture


We have the API and CLI for testing

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