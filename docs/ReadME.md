# Smart Ask - AI-Powered Knowledge Management System 🤖

<div align="center">

![Smart Ask](https://img.shields.io/badge/Smart%20Ask-AI%20Powered-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.8-orange)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)

</div>

## 📝 Overview

Smart Ask is an advanced AI-powered knowledge management system that helps users find answers to their questions by intelligently searching through various data sources. The system uses state-of-the-art language models and vector search to provide accurate and context-aware responses.

### 🔥 Key Features

- **Intelligent Q&A**: Ask questions in natural language and get accurate answers
- **Multi-Source Integration**: Pulls information from multiple sources including:
  - Zammad tickets
  - Forum discussions
  - Learn site
  - Blog site
- **Context-Aware Responses**: Maintains conversation context while allowing standalone queries
- **Reference Tracking**: Provides source references for all answers
- **Real-time Processing**: Fast and efficient response generation

## 🛠️ Technology Stack

### Core Technologies
- **Backend Framework**: FastAPI
- **AI/ML**: 
  - LlamaIndex for RAG (Retrieval Augmented Generation)
  - OpenAI/Gemini for language models
  - Elasticsearch for vector search
- **Caching & Message Queue**: Redis
- **Containerization**: Docker & Docker Compose

### Key Dependencies
- `llama-index`: Core RAG implementation
- `elasticsearch`: Vector storage and search
- `fastapi`: Web framework
- `redis`: Caching and message queue
- `uvicorn`: ASGI server
- `pydantic`: Data validation
- `python-dotenv`: Environment management

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose
- Git
- OpenAI API key (or other supported LLM provider)

### Installation

1.**Start the Services**
   ```bash
   docker-compose up -d
   ```

   This will start:
   - Web application (FastAPI) on port 8089
   - Redis for caching
   - Elasticsearch for vector storage

2.**Verify Installation**
   ```bash
   curl http://localhost:8089/health
   ```
   You should receive a healthy response.

3.**Test the APP**
   ```bash
   curl http://142.112.78.92:8089/query?message=Hi
   ```
   You should receive a hint text as response.


### Example Queries

1. **General Questions**
   ```
   "How do I reset my password?"
   "What are the system requirements?"
   ```

2. **Ticket-Related Questions**
   ```
   "What's the status of ticket #12345?"
   "Summarize the conversation with john@example.com"
   ```

3. **Documentation Queries**
   ```
   "How can I create a study in Avicenna?"
   "How can I protect my data from being deleted?"
   ```

### Docker Configuration

The system uses two main services:

1. **Web Application**
   - Port: 8089
   - Health check endpoint: `/health`
   - Restart policy: unless-stopped

2. **Redis**
   - Used for caching and message queue
   - Persistence enabled
   - Health check: Redis PING
