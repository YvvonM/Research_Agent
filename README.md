# AI Research Agent System

An automated research paper generation system that uses multiple AI agents to conduct comprehensive research, gather information from various sources, and compile structured academic reports.

## Overview

This system leverages LangGraph, LangChain, and multiple LLM agents to:
- Generate research queries based on a topic
- Structure research into academic sections (Introduction, Background, Research Findings, Application, Conclusion)
- Search multiple sources (Brave Search, arXiv, Semantic Scholar, DuckDuckGo, Google)
- Extract and analyze content from web sources
- Compile findings into a professionally formatted PDF report

## Features

- **Multi-Agent Architecture**: Specialized worker agents for each section of the research paper
- **Multiple Search Engines**: Integrates Brave Search, arXiv, Semantic Scholar, DuckDuckGo, and Google Search
- **Intelligent Content Extraction**: Uses newspaper3k, BeautifulSoup, and Playwright for robust web scraping
- **Semantic Ranking**: Employs sentence transformers to rank and select the most relevant content
- **Database Integration**: Stores research sessions, queries, structures, and reports in SQLite
- **PDF Generation**: Creates formatted research reports with proper citations

## Architecture

```
User Query → Query Generator → Research Structure Generator → Manager Agent
                                                                    ↓
                        ┌──────────────────────────────────────────┴────────────────────────────┐
                        ↓                    ↓                    ↓              ↓               ↓
              Introduction Worker  Background Worker  Research Worker  Application Worker  Summary Worker
                        ↓                    ↓                    ↓              ↓               ↓
                    Sub-agents (search, scrape, summarize for each query)
                        ↓                    ↓                    ↓              ↓               ↓
                        └──────────────────────────────────────────┬────────────────────────────┘
                                                                    ↓
                                                Final Report → PDF Generation
```

## Prerequisites

- Python 3.8+
- Groq API keys (multiple keys for different agents)
- Brave Search API key
- Git

## Quick Start Guide

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ai-research-agent.git
cd ai-research-agent
```

### 2. Create Virtual Environment

```bash
python -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright Browsers

```bash
playwright install
```

### 5. Configure Environment Variables

Create a `.env` file in the root directory:
```bash
# Clone repository
git clone https://github.com/yourusername/ai-research-agent.git
cd ai-research-agent

# Create virtual environment
python -m venv myenv
source myenv/bin/activate  # Windows: myenv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

### Step 2: Configure API Keys
Create `.env` file with your API keys:
```env
RESEARCH_QUESTIONS_GENERATOR=your_groq_api_key
RESEARCH_STRUCTURE_GENERATOR=your_groq_api_key
MANAGER_AGENT_RESEARCH=your_groq_api_key
WORKER_AGENT_1=your_groq_api_key
WORKER_AGENT_2=your_groq_api_key
WORKER_AGENT_3=your_groq_api_key
WORKER_AGENT_4=your_groq_api_key
WORKER_AGENT_5=your_groq_api_key
LITERATURE_REVIEW_AGENT=your_groq_api_key
SUB_AGENT=your_groq_api_key
SUMMARY_AGENT=your_groq_api_key
BRAVE_SEARCH=your_brave_search_api_key
```

### Step 3: Choose Your Workflow

**Option A: Use Jupyter Notebook Directly**
```bash
jupyter notebook research.ipynb
# Run all cells or specific cells as needed
```

**Option B: Convert to Python Module and Run**
```bash
# Convert notebook to Python file
jupyter nbconvert --to python research.ipynb

# Create run_research.py (see Usage section)
# Then run:
python run_research.py
```

```bash
git clone https://github.com/yourusername/ai-research-agent.git
cd ai-research-agent
```

### 2. Create Virtual Environment

```bash
python -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright Browsers

```bash
playwright install
```

### 5. Configure Environment Variables

Create a `.env` file in the root directory:

```env
# Research Agent API Keys
RESEARCH_QUESTIONS_GENERATOR=your_groq_api_key_1
RESEARCH_STRUCTURE_GENERATOR=your_groq_api_key_2
MANAGER_AGENT_RESEARCH=your_groq_api_key_3
WORKER_AGENT_1=your_groq_api_key_4
WORKER_AGENT_2=your_groq_api_key_5
WORKER_AGENT_3=your_groq_api_key_6
WORKER_AGENT_4=your_groq_api_key_7
WORKER_AGENT_5=your_groq_api_key_8
LITERATURE_REVIEW_AGENT=your_groq_api_key_9
SUB_AGENT=your_groq_api_key_10
SUMMARY_AGENT=your_groq_api_key_11

# Search API Keys
BRAVE_SEARCH=your_brave_search_api_key
```

**Note**: You can use the same Groq API key for all agents, but using different keys prevents rate limiting.

## Requirements.txt

```txt
requests==2.31.0
beautifulsoup4==4.12.2
python-dotenv==1.0.0
langgraph==0.2.0
langchain-core==0.3.0
langchain-groq==0.2.0
IPython==8.18.0
duckduckgo-search==4.1.0
langchain==0.3.0
newspaper3k==0.2.8
sentence-transformers==2.2.2
playwright==1.40.0
reportlab==4.0.7
googlesearch-python==1.2.3
asyncio==3.4.3
```

## Usage

### Basic Usage

Create a new Python file (e.g., `run_research.py`) and import the necessary functions:

```python
import asyncio
from databases import ResearchDatabase
from source.utils import ResearchHelpFunctions
# Import the core functions from research.ipynb (converted to a module)
from research import (
    create_multiple_queries,
    create_researh_structure,
    manager_agent1
)

# Initialize database
db = ResearchDatabase()
user_id = "user_001"
session_id = db.create_session(user_id=user_id, metadata={"purpose": "research"})

# Initialize helper functions
assistant = ResearchHelpFunctions()

# Define your research topic
query = "Machine Learning in Healthcare"

# Run the research pipeline
async def run_research():
    # Generate multiple queries
    multiple_queries = create_multiple_queries(query)
    query_id = db.save_research_queries(session_id, query, multiple_queries)
    
    # Create research structure
    research_structure = create_researh_structure(query, multiple_queries)
    structure_id = db.save_research_structure(query_id, session_id, research_structure)
    
    # Generate report
    final_report = await manager_agent1(research_structure)
    report_id = db.save_final_report(session_id, structure_id, final_report)
    
    # Save as PDF
    assistant.save_final_report_as_pdf(final_report, query)
    
    return final_report

# Execute
if __name__ == "__main__":
    report = asyncio.run(run_research())
    print("Research completed successfully!")
```

### Converting Notebook to Module

Before running, you need to convert `research.ipynb` to a Python module. You can either:

**Option 1: Export as Python file**
```bash
jupyter nbconvert --to python research.ipynb
```

**Option 2: Create a standalone module**
Extract the functions from `research.ipynb` into a file called `research.py`:
```python
# research.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
import os
import re
import asyncio
import time
from typing import List
from source.utils import ResearchHelpFunctions

# Initialize assistant
assistant = ResearchHelpFunctions()

# Initialize LLMs
llm_query = ChatGroq(temperature=0.7, api_key=os.getenv("RESEARCH_QUESTIONS_GENERATOR"), model="qwen-qwq-32b")
llm_structure = ChatGroq(temperature=0.7, api_key=os.getenv("RESEARCH_STRUCTURE_GENERATOR"), model="qwen-qwq-32b")
llm_worker1 = ChatGroq(temperature=0.7, api_key=os.getenv("WORKER_AGENT_1"), model="qwen-qwq-32b")
# ... initialize other workers similarly

def create_multiple_queries(query):
    # Copy function implementation from notebook
    pass

def create_researh_structure(question: str, generated_queries: list):
    # Copy function implementation from notebook
    pass

async def manager_agent1(organized_dict: dict):
    # Copy function implementation from notebook
    pass

# ... copy other worker functions
```

### Running the Example

```bash
python run_research.py
```

Or run directly with the notebook:
```bash
jupyter notebook research.ipynb
```

## Project Structure

```
ai-research-agent/
├── research.ipynb              # Main Jupyter notebook with all functions             
├── run_research.py             # Execution script
├── db.py                # Database management
├── source/
│   ├── utils.py               # Helper functions and utilities
├── downloads/                 # Generated PDF reports
├── .env                       # Environment variables
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Key Components

### 1. Query Generation
Generates 5 distinct research queries based on the input topic using the `qwen-qwq-32b` model.

### 2. Research Structure
Organizes queries into academic sections:
- Introduction
- Background
- Research Findings
- Application
- Conclusion

### 3. Worker Agents
Each worker agent:
- Receives section-specific queries
- Searches multiple sources
- Extracts and summarizes content
- Compiles findings into coherent narratives

### 4. Sub-agents
Handle individual query processing:
- Perform web searches
- Scrape content
- Rank relevance using semantic similarity
- Generate summaries

### 5. PDF Generation
Creates professionally formatted reports with:
- Section headers
- Justified paragraphs
- Source citations
- Unique filenames with timestamps

## API Rate Limits

**Important**: The system respects API rate limits:
- Groq API: 100,000 tokens per day per key (free tier)
- Brave Search: 1 request per second (free Tier)
- Delays between requests: 3-5 seconds

**Recommendation**: Use multiple Groq API keys to distribute load.

## Database Schema

The system uses SQLite with tables for:
- `sessions`: Research sessions
- `research_queries`: Generated queries
- `research_structures`: Organized query structures
- `final_reports`: Completed research reports

## Troubleshooting

### Rate Limit Errors
If you encounter rate limit errors:
1. Use multiple Groq API keys
2. Increase delays between requests
3. Reduce the number of queries per section

### Playwright Installation Issues
```bash
playwright install chromium
```

### Content Extraction Failures
The system tries multiple methods:
1. Requests + BeautifulSoup
2. newspaper3k
3. Playwright (headless browser)

If all fail, the system continues with available content.

## Limitations

- Rate limits on free API tiers
- Some websites block automated scraping
- Content quality depends on source availability
- Processing time: 5-15 minutes per research topic

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- LangChain and LangGraph frameworks
- Groq for LLM inference
- Brave Search API
- Semantic Scholar and arXiv APIs

## Contact

For questions or support, please open an issue on GitHub.

---

**Note**: This system is designed for academic research assistance. Always verify information and cite sources appropriately in your work.
