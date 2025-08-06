
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
cd rag_sql_qa_1.1.1
python optimized_three_agent_system_with_product_logic.py
```

### 2. Test Product Logic
```bash
python test_product_logic.py
```

---

## System Architecture

### Three-Agent Pipeline:
1. **IntentAgent**: Analyzes user queries and determines intent
2. **RelevantDataAgent**: Collects relevant data (metadata, lineage, search)
3. **QueryWriterAgent**: Generates SQL queries and answers with product logic

### Product Logic Features:
- **Enterprise Default**: When no product is mentioned, uses 'enterprise' for cross-product data
- **Smart Detection**: Automatically detects mentioned products (core, games, cooking, etc.)
- **Enhanced SQL**: Generates SQL with proper WHERE clauses for product filtering

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
