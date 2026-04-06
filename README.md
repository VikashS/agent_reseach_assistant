# Research Assistant Agent

An Basic AI agent that transforms high-level user goals into executable tasks and completes them using real-world tools. This project is built from scratch, without relying on frameworks like LangChain, CrewAI, etc to demonstrate the fundamentals of agent design, reasoning, and execution.

## Goal of the Project

The core focus here is on simple/robust execution. I turn users goals into structured plans, run tasks one by one, handle errors , 
and manage limited context effectively to keep things running smoothly.

## Key Highlights

- **Goal → Plan → Execute → Report Pipeline**: A straightforward flow from input to output.
- **Dynamic Task Generation**: Uses LLM reasoning to break down goals into actionable steps.
- **Tool Integration**: Includes search and URL reading capabilities .
- **Context Management**: Added a sliding window and truncation to stay within limits.
- **Proper Logs**: Detailed execution logs for easy debugging and building trust.

## Architecture Overview

The agent follows a simple yet effective pipeline:

```
User Goal
   ↓
Task Planner (LLM)
   ↓
TODO List
   ↓
Execution Loop
   ├── Search Tool
   ├── Read Tool
   └── Summarization
   ↓
Final Response
```

## Agent Workflow

1. **Planning**: The agent takes the user goal and converts it into a list of structured tasks. Each task has a description, type, and query to guide execution.
2. **Execution**: Tasks are run one after another. Progress is tracked, and intermediate results are stored for reference.
3. **Reporting**: All outputs are gathered and summarized into a clear, structured final response.

## Manual Context Strategy

To prevent token limits from causing issues while keeping responses relevant, we manage context carefully:

- Retain the original goal and current task.
- Keep the last 2–3 steps in memory.
- Truncate lengthy outputs to 500–1000 characters.
- Discard older, less important information.

## Evaluation

We test the agent across main scenarios to ensure reliabilit such as long context .


## Trade offs
- **No Frameworks**: I have added custom agent loop in absense of standard frame work.
 # Custom loop (my approach)
 for task in tasks:
    if task.type == "search":
        result = search_web(task.query)
    elif task.type == "summarize":
        result = llm_summarize(context)

- **Sequential Execution**: Keeps things simple and predictable, though it's slower than running tasks in parallel.
- **Lightweight Memory**: Good for most cases, but not efficient for recall.
- **Search Tools**: Use Only tavily so no falllback.

## Future Improvements

- Implement parallel task execution to boost speed.
- Upgrade to better memory systems, like vector databases for retrieval.
- Add evaluation metrics, such as precision and task success rates.
- Incorporate user feedback loops for continuous learning.
- Enhance reasoning with multi-hop and chain-of-thought techniques.
- Improve error handling and recovery strategies.
- Prioritize architecture and reliability.
- From code prospective will integrate FastAPI for better API management and modularity.
- Integrate with Pydentic for better data validation and structured task management.


## Note: add youe details in .env to run the code successfully
OLLAMA_BASE_URL="http://localhost:11434"
OLLAMA_MODEL="llama3.1:8b"
TAVILY_API_KEY="your_tavily_api_key_here"
SEARCH_PROVIDER="tavily"
OPENAI_MODEL=gpt-4.1
OPENAI_API_KEY="your_openai_api_key_here" 

