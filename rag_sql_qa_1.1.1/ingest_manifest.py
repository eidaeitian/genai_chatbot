from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.schema import Document
from config import OPENAI_API_KEY, EMBED_MODEL
import shutil
import json
import os
from dotenv import load_dotenv
load_dotenv()  

CHROMA_DB_PATH = "chroma_db"
COLLECTION_NAME = "rag_manifest"


def load_manifest(path="manifest.json"):
    with open(path, "r") as f:
        return json.load(f)


def create_readable_chunks(manifest):
    docs = []
    for node_key, node in manifest.get("nodes", {}).items():
        if not node_key.startswith("model."):
            continue

        short_name = node.get("name", "<unknown>")
        full_name = node_key
        sql_code = node.get("raw_sql", "").strip() or "(no SQL code)"
        table_desc = node.get("description", "").strip(
        ) or "No description provided."
        columns = node.get("columns", {})
        upstream = node.get("depends_on", {}).get("nodes", [])
        db = node.get("database", "")
        schema = node.get("schema", "")
        alias = node.get("alias", "")
        warehouse_table = f"{db}.{schema}.{alias}" if db and schema and alias else "Unknown"

        column_section = "\n".join(
            f"- {col}: {meta.get('description','').strip()}"
            for col, meta in columns.items()
        ) or "No columns documented."

        upstream_section = ", ".join(upstream) if upstream else "None"

        content = (
            f"Table Name: {short_name}\n"
            f"Full Model Key: {full_name}\n"
            f"Warehouse Table: {warehouse_table}\n\n"
            f"Description:\n{table_desc}\n\n"
            f"Columns:\n{column_section}\n\n"
            f"SQL Code:\n```sql\n{sql_code}\n```\n\n"
            f"Model Upstream Models:\n{upstream_section}\n"
        )

        metadata = {
            "model_name": short_name,
            "full_key":   full_name,
            "table_ref":  warehouse_table,
            "n_columns":  len(columns),
        }

        docs.append(Document(page_content=content, metadata=metadata))

    return docs


def ingest_to_chroma(docs,
                     persist_dir=CHROMA_DB_PATH,
                     collection_name=COLLECTION_NAME):
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set in config")

    embeddings = OpenAIEmbeddings(
        openai_api_key=OPENAI_API_KEY,
        model=EMBED_MODEL
    )

    # ← use from_documents since we're passing Document objects
    vectordb = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=persist_dir,
        collection_name=collection_name
    )
    vectordb.persist()
    print(
        f"Ingested {len(docs)} documents into ChromaDB at `{persist_dir}`.")


def main():
    if os.path.exists(CHROMA_DB_PATH):
        shutil.rmtree(CHROMA_DB_PATH)
        print("🧹 Existing ChromaDB deleted.")

    manifest = load_manifest()
    docs = create_readable_chunks(manifest)
    ingest_to_chroma(docs)


if __name__ == "__main__":
    main()
