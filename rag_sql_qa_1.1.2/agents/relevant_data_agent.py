from typing import List, Dict, Any
from collections import deque
from langchain.agents import initialize_agent, AgentType
from langchain.agents import Tool
from langchain.schema import Document
from agents.base_agent import BaseAgent
import re
import json

class RelevantDataAgent(BaseAgent):
    """Relevant Data Agent for searching and collecting related information"""
    
    def __init__(self):
        super().__init__()
        self.tools = self._create_tools()
        self.agent = self._create_agent()
        self.data_bucket = {
            "lineage_info": {},
            "metadata_info": {},
            "direct_parents_info": {},
            "search_results": []
        }
        
        # Load manifest for dependency tools
        try:
            with open("manifest.json", "r", encoding="utf-8") as f:
                self.manifest = json.load(f)
            print("✅ Manifest loaded successfully")
        except Exception as e:
            print(f"❌ Error loading manifest: {e}")
            self.manifest = {"nodes": {}}

    
    def _create_tools(self):
        """Create data search related tools"""
        return [
            Tool(
                name="FindLayers",
                func=self.find_layers_fn,
                description=(
                    "Use this tool to find the shortest dependency path or relationship between two tables in the dbt manifest.\n"
                    "Input: two table names in a comma-separated string, e.g., 'users,orders'.\n"
                    "Call this when asked about how two tables are connected or their transformation lineage.\n"
                )
            ),
            Tool(
                name="FindDirectParents",
                func=self.find_direct_parents_fn,
                description=(
                    "Use this tool to retrieve the immediate upstream dependencies of a given table/model.\n"
                    "Call this when a query involves dependency tracing and more information is needed about upstream lineage.\n"
                    "Input: a single model name (string)."
                )
            ),
            Tool(
                name="GeneralSimilaritySearch",
                func=self.general_similarity_search_fn,
                description=(
                    "Use this tool for general, vague, or metadata-related questions — especially when no table is explicitly provided.\n"
                    "Always call this tool if the question is unclear, exploratory, or references concepts rather than specific tables.\n"
                    "DO NOT try to answer general questions directly — you MUST call this tool.\n"
                    "Input: the user question as a string.\n"
                    "Output: relevant documents found using vector similarity search (ChromaDB)."
                )
            ),
            Tool(
                name="GetTableInfoByExactTableName",
                func=self.metadata_search_fn,
                description=(
                    "Use this tool FIRST when the question provides exact table/model names and you're asked to explain or explore them.\n"
                    "Input: comma-separated table identifiers like 'users,orders'.\n"
                    "Output: documents (table metadata, descriptions, SQL, etc.) from ChromaDB.\n"
                )
            ),
        ]
    
    def _create_agent(self):
        """Create data collection agent - RETURN DATA BUCKET AND SUMMARY ONLY"""
        # prompt = """
        # You are a Data Collection Specialist Agent.
        
        # CRITICAL ROLE: You are ONLY responsible for collecting data and providing a summary of collected data. You do NOT generate answers for user queries.
        
        # YOUR PROCESS:
        # 1. Analyze the user query and intent analysis response to understand what data is needed
        # 2. Use LangChain Agent to automatically call the appropriate tools based on the context
        # 3. Show your thinking process: "🤔 Thinking: [your reasoning]"
        # 4. Call tools automatically: "🔧 Action: [tool_name]" and "📊 Observation: [tool_result]"
        # 5. Provide a comprehensive summary of what data was collected
        # 6. Return the collected data as your final answer
        
        # AVAILABLE TOOLS:
        # - FindDirectParents: Get immediate upstream dependencies of a table
        # - FindLayers: Find dependency path between two tables  
        # - GetTableInfoByExactTableName: Get metadata information about tables
        # - GeneralSimilaritySearch: Search for similar content in the knowledge base
        
        # TOOL SELECTION GUIDELINES:
        # - For lineage questions: Use FindDirectParents or FindLayers
        # - For metadata questions: Use GetTableInfoByExactTableName
        # - For general questions: Use GeneralSimilaritySearch
        # - For SQL generation: Use both lineage and metadata tools
        # - For unclear questions: Start with GeneralSimilaritySearch
        
        # IMPORTANT INSTRUCTIONS:
        # - Show your thinking process with "🤔 Thinking:"
        # - Call tools automatically using LangChain Agent's tool calling mechanism
        # - Collect data only, do not answer user queries
        # - Use the intent analysis response to guide your tool selection
        # - Call multiple tools if needed to gather comprehensive data
        # - Provide a detailed summary of all collected data
        
        # CONTEXT FORMAT:
        # User Query: [original user question]
        # Intent Analysis Response: [response from previous agent]
        
        # Use both pieces of information to determine which tools to call and what data to collect.
        # """
        prompt = """
        You are a Data Collection Specialist Agent.
        
        CRITICAL ROLE: You are ONLY responsible for collecting data and providing a summary of collected data. You do NOT generate answers for user queries.
        
        YOUR PROCESS:
        1. Analyze the user query and intent analysis response to understand what data is needed
        2. Use LangChain Agent to automatically call the appropriate tools based on the context
        3. Show your thinking process: "🤔 Thinking: [your reasoning]"
        4. Call tools automatically: "🔧 Action: [tool_name]" and "📊 Observation: [tool_result]"
        5. Provide a comprehensive summary of what data was collected
        6. Return the collected data as your final answer
        
        AVAILABLE TOOLS:
        - FindDirectParents: Get immediate upstream dependencies of a table
        - FindLayers: Find dependency path between two tables  
        - GetTableInfoByExactTableName: Get metadata information about tables
        - GeneralSimilaritySearch: Search for similar content in the knowledge base
        
        TOOL SELECTION GUIDELINES:
        - For lineage questions: Use FindDirectParents or FindLayers
        - For metadata questions: Use GetTableInfoByExactTableName
        - For general questions: Use GeneralSimilaritySearch
        - For SQL generation: all of the sql query question should only use table "weekly_active_users_agg_vw" by tool GetTableInfoByExactTableName
        - For unclear questions: Start with GeneralSimilaritySearch
        
        IMPORTANT INSTRUCTIONS:
        - Show your thinking process with "🤔 Thinking:"
        - Call tools automatically using LangChain Agent's tool calling mechanism
        - Collect data only, do not answer user queries
        - Use the intent analysis response to guide your tool selection
        - Call multiple tools if needed to gather comprehensive data
        - Provide a detailed summary of all collected data
        - When user question is about sql query, use tool GetTableInfoByExactTableName and get table "weekly_active_users_agg_vw" to answer the question.
        
        CONTEXT FORMAT:
        User Query: [original user question]
        Intent Analysis Response: [response from previous agent]
        
        Use both pieces of information to determine which tools to call and what data to collect.
        """
        
        return initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            prompt=prompt,
            max_iterations=5,
            early_stopping_method="generate",
            verbose=True,
            handle_parsing_errors=True,
        )
    
    def find_layers_fn(self, arg: str) -> List[str]:
        """Find the shortest dependency path between two tables"""
        parts = [t.strip() for t in arg.split(",") if t.strip()]
        if len(parts) != 2:
            raise ValueError(
                'find_layers_fn expects exactly two table names separated by a comma, '
                'e.g. "users,orders"'
            )
        a, b = parts

        # Build alias‑to‑alias dependency graph
        dep_graph: Dict[str, List[str]] = {}
        for node_key, node in self.manifest["nodes"].items():
            alias = node.get("alias") or node.get("name")
            parents: List[str] = []
            for parent_key in node.get("depends_on", {}).get("nodes", []):
                parent_node = self.manifest["nodes"].get(parent_key)
                if not parent_node:
                    continue
                parents.append(parent_node.get("alias") or parent_node.get("name"))
            dep_graph[alias] = parents

        # BFS to find shortest path from start → end
        def bfs(start: str, end: str) -> List[str]:
            queue = deque([[start]])
            seen = {start}
            while queue:
                path = queue.popleft()
                last = path[-1]
                if last == end:
                    return path
                for parent in dep_graph.get(last, []):
                    if parent not in seen:
                        seen.add(parent)
                        queue.append(path + [parent])
            return []

        # Try both directions
        path = bfs(a, b)
        if path:
            result = path
        else:
            rev = bfs(b, a)
            result = rev[::-1] if rev else []
        
        print(f"🔍 Shortest path between {a} and {b}: {result}")
        self.data_bucket["lineage_info"]["shortest_path"] = result
        return result

    def find_direct_parents_fn(self, table: str) -> List[str]:
        """Find the direct upstream dependencies of a table"""
        # 1) Locate the manifest key for this table
        node_key = None
        for key, node in self.manifest["nodes"].items():
            if (
                node.get("alias") == table
                or node.get("name") == table
                or key.endswith(f".{table}")
            ):
                node_key = key
                break
        if node_key is None:
            raise ValueError(f"No model named '{table}' in manifest.")

        node = self.manifest["nodes"][node_key]

        # 2) Start with manifest-declared parents
        parents = set(node.get("depends_on", {}).get("nodes", []))

        # 3) Parse the compiled SQL for extra references
        sql = node.get("compiled_sql", "") or node.get("raw_sql", "")
        pattern = re.compile(
            r'\b(?:from|join|in)\s+([A-Za-z0-9_\.\"]+)',
            re.IGNORECASE
        )
        for match in pattern.findall(sql):
            tbl = match.strip('"')
            if not tbl.lower().endswith(f".{table.lower()}"):
                parents.add(tbl)

        # 4) Normalize to simple model names
        normalized = []
        for key in parents:
            if key in self.manifest["nodes"]:
                normalized.append(self.manifest["nodes"][key]["name"])
            else:
                normalized.append(key)

        result = sorted(set(normalized))
        print(f"🔍 Direct parents for {table}: {result}")
        self.data_bucket["direct_parents_info"][table] = result
        return result

    def general_similarity_search_fn(self, query: str) -> List[Document]:
        """General similarity search"""
        SCORE_THRESHOLD = 0.2
        
        docs_and_scores = self.vectordb.similarity_search_with_relevance_scores(
            query, k=3)
        
        docs = [doc for doc, score in docs_and_scores if score > SCORE_THRESHOLD]
        self.data_bucket["search_results"].extend([doc.page_content for doc in docs])
        return docs

    def metadata_search_fn(self, tables_input: str) -> List[Document]:
        """Search metadata by table names"""
        table_list = [t.strip() for t in tables_input.split(",") if t.strip()]

        results = self.vectordb._collection.get(
            where={"model_name": {"$in": table_list}}
        )

        documents = [
            Document(page_content=content, metadata=md)
            for content, md in zip(results["documents"], results["metadatas"])
        ]

        if not documents:
            print(f"[metadata_search_fn] No matches for: {table_list}")

        self.data_bucket["metadata_info"].update({
            table: [doc.page_content for doc in documents]
            for table in table_list
        })
        return documents
    
    def run(self, query: str, intent_analysis_response: str) -> Dict[str, Any]:
        try:
            print("🤔 RelevantDataAgent is calling LangChain agent directly...")

            self.data_bucket = {
                "query": query,
                "intent_analysis_response": intent_analysis_response,
                "lineage_info": {},
                "metadata_info": {},
                "direct_parents_info": {},
                "search_results": [],
            }

            agent_input = f"""
            CONTEXT:
            User Query: {query}
            Intent Analysis Response: {intent_analysis_response}
            
            INSTRUCTIONS:
            Based on the context above, automatically call the appropriate tools
            to collect relevant data. Then, summarize what was collected.
            """

            relevant_data_summary = self.agent.run(agent_input)

            self.data_bucket["relevant_data_summary"] = relevant_data_summary  # ✅ renamed key
            return self.data_bucket

        except Exception as e:
            print(f"❌ Error in RelevantDataAgent: {e}")
            return {
                "query": query,
                "intent_analysis_response": intent_analysis_response,
                "error": str(e),
                "relevant_data_summary": "Error occurred during data collection"
            }

    # def run(self, query: str, intent_analysis_response: str) -> Dict[str, Any]:
    #     try:
    #         print("🤔 RelevantDataAgent is calling LangChain agent directly...")

    #         # Construct agent prompt input with user query and prior intent response
    #         agent_input = f"""
    #         CONTEXT:
    #         User Query: {query}
    #         Intent Analysis Response: {intent_analysis_response}
            
    #         INSTRUCTIONS:
    #         Based on the context above, automatically call the appropriate tools
    #         to collect relevant data. Then, summarize what was collected.
    #         """

    #         # LangChain agent will automatically choose tools
    #         agent_summary = self.agent.run(agent_input)
    #         # print({
    #         #     "query": query,
    #         #     "intent_analysis_response": intent_analysis_response,
    #         #     "agent_summary": agent_summary
    #         # })

    #         return {
    #             "query": query,
    #             "intent_analysis_response": intent_analysis_response,
    #             "agent_summary": agent_summary
    #         }

    #     except Exception as e:
    #         print(f"❌ Error in RelevantDataAgent: {e}")
    #         return {
    #             "query": query,
    #             "intent_analysis_response": intent_analysis_response,
    #             "error": str(e),
    #             "agent_summary": "Error occurred during data collection"
    #         }
