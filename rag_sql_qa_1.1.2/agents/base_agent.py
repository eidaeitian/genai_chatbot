from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.memory import ConversationBufferWindowMemory
from config import GOOGLE_API_KEY, EMBED_MODEL, LLM_MODEL
import json
import logging

logger = logging.getLogger(__name__)

class BaseAgent:
    """基础Agent类，提供共享的LLM和向量数据库配置"""
    
    def __init__(self):
        # 共享的LLM配置
        self.llm = ChatGoogleGenerativeAI(
            model=LLM_MODEL,
            temperature=0,
            google_api_key=GOOGLE_API_KEY,
        )
        
        # 共享的embeddings配置
        self.embeddings = GoogleGenerativeAIEmbeddings(
            google_api_key=GOOGLE_API_KEY,
            model=EMBED_MODEL,
        )
        
        # 共享的向量数据库
        self.vectordb = Chroma(
            persist_directory="chroma_db",
            embedding_function=self.embeddings,
            collection_name="rag_manifest"
        )
        
        # 共享的内存
        self.memory = ConversationBufferWindowMemory(
            k=12, memory_key="chat_history", return_messages=True
        )
        
        # 加载manifest
        with open("manifest.json", "r", encoding="utf-8") as f:
            self.manifest = json.load(f)
    
    def get_manifest(self):
        """获取dbt manifest"""
        return self.manifest
    
    def get_vectordb(self):
        """获取向量数据库实例"""
        return self.vectordb
    
    def get_llm(self):
        """获取LLM实例"""
        return self.llm 