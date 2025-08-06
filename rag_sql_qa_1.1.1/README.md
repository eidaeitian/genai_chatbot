
# RAG Chatbot (v1.4)

A simple Retrieval-Augmented Generation (RAG) chatbot using OpenAI API and ChromaDB for document-augmented conversations. We plan to migrate to GCP infrastructure in the next phase.

---

## Setup Instructions

### 1. Set Your OpenAI API Key

Edit the `config.py` file and set your API credentials:

```python
OPENAI_API_KEY = "your-api-key"
EMBED_MODEL = "text-embedding-ada-002"
LLM_MODEL = "gpt-4"
```

Alternatively, you can use a `.env` file:

```env
OPENAI_API_KEY=your-api-key
```

---

### 2. Ingest Your Documents

Run the following script to embed documents into ChromaDB:

```bash
python ingest_manifest.py
```

---

### 3. Start the Chatbot Agent

Launch the RAG chatbot:

```bash
python rag_agent_v1_4.py
```

---

## Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

Required packages include:

- `langchain`
- `langchain_openai`
- `langchain_community`
- `chromadb`
- `openai`
- `python-dotenv`

---

## Python Version

Python 3.8+ is recommended.

---
## Contact

For any questions or suggestions, feel free to reach out to the dig-coe-ai-data-assistant slack channel.
