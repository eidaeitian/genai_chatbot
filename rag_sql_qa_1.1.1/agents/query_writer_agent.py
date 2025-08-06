from typing import Dict, Any, List
from langchain.agents import initialize_agent, AgentType
from langchain.agents import Tool
from agents.base_agent import BaseAgent
import json
import re

class QueryWriterAgent(BaseAgent):
    """Query Writing Agent for generating SQL queries and answers with product logic"""
    
    def __init__(self):
        super().__init__()
        self.tools = self._create_tools()
        self.agent = self._create_agent()
        
        # Define product values and enterprise logic
        self.product_values = [
            "core", "games", "cooking", "wirecutter", "audio", 
            "the-athletic", "other", "enterprise"
        ]
        self.enterprise_value = "enterprise"
    
    def _create_tools(self):
        """Create query writing related tools with input data in prompts"""
        return [
            Tool(
                name="ValidateTableExists",
                func=self.validate_table_exists_fn,
                description=(
                    "Use this tool to validate table existence and get metadata.\n"
                    "Call this tool when user asks about table structure, validation, or table existence.\n"
                    "The tool will receive the user query, intent analysis, and collected data in its prompt.\n"
                    "Output: Table validation and metadata information."
                )
            ),
            Tool(
                name="GenerateSQLQuery",
                func=self.generate_sql_query_fn,
                description=(
                    "Use this tool to generate SQL queries with product column logic.\n"
                    "Call this tool when the user asks for SQL queries, data extraction, or database queries.\n"
                    "The tool will receive the user query, intent analysis, and collected data in its prompt.\n"
                    "Output: SQL query with proper product filtering."
                )
            ),
            Tool(
                name="GenerateGeneralAnswer",
                func=self.generate_general_answer_fn,
                description=(
                    "Use this tool to generate general answers for non-SQL questions.\n"
                    "Call this tool for metadata questions, lineage questions, or general data questions.\n"
                    "The tool will receive the user query, intent analysis, and collected data in its prompt.\n"
                    "Output: Comprehensive answer based on collected information."
                )
            )
        ]
    
    def _create_agent(self):
        """Create query writing agent with LangChain Agent to call tools"""
        prompt = """
        You are a Query Writing Specialist Agent with Product Logic.
        
        YOUR ROLE: Use LangChain Agent to call tools and generate final answers for user queries.
        
        AVAILABLE TOOLS:
        1. ValidateTableExists: Use for table validation questions. Call this tool when user asks about table structure, validation, or table existence.
        2. GenerateSQLQuery: Use for SQL generation questions. Call this tool when user asks for SQL queries, data extraction, or database queries.
        3. GenerateGeneralAnswer: Use for all other questions. Call this tool for lineage questions, metadata questions, general questions, or any other query types.
        
        TOOL SELECTION RULES:
        - If user asks about table structure, validation, or table existence → Call ValidateTableExists
        - If user asks for SQL queries, data extraction, or database queries → Call GenerateSQLQuery
        - For all other questions (lineage, metadata, general search, etc.) → Call GenerateGeneralAnswer
        
        IMPORTANT PRODUCT COLUMN LOGIC:
        - Product column contains values: core, games, cooking, wirecutter, audio, the-athletic, other, enterprise
        - 'enterprise' is a special value that represents data across ALL products
        - When user query doesn't specify a product, default to 'enterprise' for cross-product data
        - When user mentions specific products, use those products in WHERE clause
        
        YOUR PROCESS:
        1. Analyze the user query
        2. Determine which tool to call based on the query type
        3. Call the appropriate tool using LangChain Agent
        4. Generate comprehensive final answer for the user query
        
        IMPORTANT:
        - Show your thinking process and tool calling
        - Call the tools using LangChain Agent
        - Generate comprehensive final answers for user queries
        - Always call one of the available tools
        """
        
        return initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            prompt=prompt,
            max_iterations=4,
            early_stopping_method="generate",
            verbose=True,
            handle_parsing_errors=True,
        )
    
    def _extract_user_query_from_prompt(self, prompt: str) -> str:
        """Extract user query from prompt"""
        try:
            if "User Original Query:" in prompt:
                start = prompt.find("User Original Query:") + len("User Original Query:")
                end = prompt.find("\n", start)
                if end == -1:
                    end = len(prompt)
                return prompt[start:end].strip()
            return ""
        except Exception as e:
            print(f"Error extracting user query: {e}")
            return ""

    def _extract_intent_analysis_from_prompt(self, prompt: str) -> Dict[str, Any]:
        """Extract intent analysis from prompt"""
        try:
            if "IntentAgent Response:" in prompt:
                start = prompt.find("IntentAgent Response:") + len("IntentAgent Response:")
                end = prompt.find("\n", start)
                if end == -1:
                    end = len(prompt)
                intent_str = prompt[start:end].strip()
                return eval(intent_str) if intent_str else {}
            return {}
        except Exception as e:
            print(f"Error extracting intent analysis: {e}")
            return {}

    def _extract_collected_data_from_prompt(self, prompt: str) -> Dict[str, Any]:
        """Extract collected data from prompt"""
        try:
            if "RelevantDataAgent Response:" in prompt:
                start = prompt.find("RelevantDataAgent Response:") + len("RelevantDataAgent Response:")
                end = prompt.find("\n", start)
                if end == -1:
                    end = len(prompt)
                data_str = prompt[start:end].strip()
                return eval(data_str) if data_str else {}
            return {}
        except Exception as e:
            print(f"Error extracting collected data: {e}")
            return {}

    def _extract_data_bucket_from_prompt(self, prompt: str) -> Dict[str, Any]:
        """Extract data bucket from prompt"""
        try:
            if "Data Bucket:" in prompt:
                start = prompt.find("Data Bucket:") + len("Data Bucket:")
                end = prompt.find("\n", start)
                if end == -1:
                    end = len(prompt)
                bucket_str = prompt[start:end].strip()
                return eval(bucket_str) if bucket_str else {}
            return {}
        except Exception as e:
            print(f"Error extracting data bucket: {e}")
            return {}

    def _extract_all_data_from_prompt(self, prompt: str) -> Dict[str, Any]:
        """Extract all data from prompt including data bucket"""
        try:
            user_query = self._extract_user_query_from_prompt(prompt)
            intent_analysis = self._extract_intent_analysis_from_prompt(prompt)
            data_bucket = self._extract_data_bucket_from_prompt(prompt)
            
            # If data bucket is empty, try to extract from RelevantDataAgent Response
            if not data_bucket:
                data_bucket = self._extract_collected_data_from_prompt(prompt)
            
            return {
                "user_query": user_query,
                "intent_analysis": intent_analysis,
                "data_bucket": data_bucket
            }
        except Exception as e:
            print(f"Error extracting all data from prompt: {e}")
            return {
                "user_query": "",
                "intent_analysis": {},
                "data_bucket": {}
            }

    def _extract_mentioned_products(self, query: str) -> List[str]:
        """Extract mentioned products from query"""
        products = []
        product_keywords = ['core', 'games', 'cooking', 'wirecutter', 'audio', 'the-athletic', 'enterprise']
        
        for product in product_keywords:
            if product.lower() in query.lower():
                products.append(product)
        
        return products
    
    def _determine_product_filter(self, query: str) -> dict:
        """Determine the appropriate product filter based on user query"""
        mentioned_products = self._extract_mentioned_products(query)
        
        if not mentioned_products:
            # No specific product mentioned, use enterprise for cross-product data
            return {
                "filter_type": "enterprise",
                "products": ["enterprise"],
                "explanation": "No specific product mentioned, using 'enterprise' for cross-product data"
            }
        elif "enterprise" in mentioned_products:
            # Enterprise explicitly mentioned
            return {
                "filter_type": "enterprise",
                "products": ["enterprise"],
                "explanation": "Enterprise explicitly mentioned for cross-product data"
            }
        else:
            # Specific products mentioned
            return {
                "filter_type": "specific",
                "products": mentioned_products,
                "explanation": f"Using specific products: {', '.join(mentioned_products)}"
            }
    
    def _determine_best_table_from_bucket(self, data_bucket: Dict[str, Any], intent_analysis: Dict[str, Any]) -> str:
        """Determine the best table to use based on data bucket"""
        try:
            # 从意图分析中获取提到的表
            mentioned_tables = intent_analysis.get('mentioned_tables', [])
            
            # 从数据bucket中获取表信息
            lineage_info = data_bucket.get('lineage_info', {})
            metadata_info = data_bucket.get('metadata_info', {})
            tool_results = data_bucket.get('tool_results', {})
            
            # 优先使用提到的表
            if mentioned_tables:
                return mentioned_tables[0]
            
            # 如果没有提到的表，使用lineage_info中的表
            if lineage_info:
                for table in lineage_info.keys():
                    return table
            
            # 如果都没有，使用默认表
            return "your_table"
            
        except Exception as e:
            print(f"Error determining best table from bucket: {e}")
            return "your_table"

    def generate_sql_query_fn(self, prompt_with_data: str) -> str:
        """Generate SQL query with product logic using LLM"""
        try:
            print("🔧 GenerateSQLQuery Tool Called")
            
            # Get data from global storage
            user_query = self.current_data["user_query"]
            intent_analysis = self.current_data["intent_analysis"]
            collected_data = self.current_data["collected_data"]
            
            # Create a simple prompt for SQL generation
            sql_prompt = f"""
            You are a SQL generation expert. Generate a SQL query based on the following information:
            
            INPUT 1 - User Original Query: {user_query}
            
            INPUT 2 - Previous Agents Results:
            - IntentAgent Response: {intent_analysis}
            - RelevantDataAgent Response (collected table/data): {collected_data}
            
            IMPORTANT PRODUCT COLUMN LOGIC:
            - Product column contains values: core, games, cooking, wirecutter, audio, the-athletic, other, enterprise
            - 'enterprise' is a special value that represents data across ALL products
            - When user query doesn't specify a product, default to 'enterprise' for cross-product data
            - When user mentions specific products, use those products in WHERE clause
            
            Generate a SQL query that:
            1. Uses appropriate product filtering based on the user query
            2. Extracts the relevant data requested
            3. Uses proper SQL syntax and best practices
            
            Return only the SQL query, no explanations.
            """
            
            # Use LLM to generate SQL
            response = self.llm.invoke(sql_prompt)
            
            return response.content
            
        except Exception as e:
            return f"Error generating SQL: {str(e)}"
    
    def validate_table_exists_fn(self, prompt_with_data: str) -> str:
        """Validate table exists and get metadata using LLM"""
        try:
            print("🔧 ValidateTableExists Tool Called")
            
            # Get data from global storage
            user_query = self.current_data["user_query"]
            intent_analysis = self.current_data["intent_analysis"]
            collected_data = self.current_data["collected_data"]
            
            # Create a simple prompt for table validation
            validation_prompt = f"""
            You are a table validation expert. Validate table existence and provide metadata based on the following information:
            
            INPUT 1 - User Original Query: {user_query}
            
            INPUT 2 - Previous Agents Results:
            - IntentAgent Response: {intent_analysis}
            - RelevantDataAgent Response (collected table/data): {collected_data}
            
            Analyze the user query to determine which table(s) they are asking about, then:
            1. Check if the table exists in the data collection
            2. Provide table metadata and structure information
            3. Explain the table's purpose and relationships
            
            Return a comprehensive table validation and metadata report.
            """
            
            # Use LLM to generate validation report
            response = self.llm.invoke(validation_prompt)
            
            return response.content
            
        except Exception as e:
            return f"Error validating table: {str(e)}"
    
    def generate_general_answer_fn(self, prompt_with_data: str) -> str:
        """Generate general answer using LLM"""
        try:
            print("🔧 GenerateGeneralAnswer Tool Called")
            
            # Get data from global storage
            user_query = self.current_data["user_query"]
            intent_analysis = self.current_data["intent_analysis"]
            collected_data = self.current_data["collected_data"]
            
            # Create a simple prompt for general answer generation
            answer_prompt = f"""
            You are a data analysis expert. Generate a comprehensive answer based on the following information:
            
            INPUT 1:
            User Original Query: {user_query}
            
            INPUT 2:
            - IntentAgent Response: {intent_analysis}
            - RelevantDataAgent Response (collected table/data): {collected_data}

            RelevantDataAgent Response explaination:
            "lineage_info": lineage information of the targeted tables.
            "metadata_info": targeted table inforamtion.
            "direct_parents_info": targeted table's direct parents.
            "search_results": potential targeted table collected by similarity search.
            
            Generate a comprehensive answer that:
            1. Addresses the user's question (User Original Query) directly
            2. Uses the provided data and context (RelevantDataAgent Response) for the answer.
            3. Provides clear, helpful information
            4. Explains any relevant data relationships or insights
            
            Return a well-structured answer that directly addresses the user's query.
            """
            
            print(answer_prompt)
            # Use LLM to generate answer
            response = self.llm.invoke(answer_prompt)
            
            return response.content
            
        except Exception as e:
            return f"Error generating answer: {str(e)}"
    
    def _generate_lineage_answer_from_data(self, user_query: str, intent_analysis: Dict[str, Any], collected_data: Dict[str, Any]) -> str:
        """Generate lineage answer using collected data"""
        lineage_info = collected_data.get("lineage_info", {})
        tool_calls = collected_data.get("tool_calls", {})
        
        response = f"Lineage Information for: {user_query}\n\n"
        
        if lineage_info:
            for table, info in lineage_info.items():
                response += f"Table: {table}\n"
                if isinstance(info, dict):
                    if "upstream_dependencies" in info:
                        parents = info["upstream_dependencies"]
                        response += f"Dependencies: {', '.join(parents) if parents else 'None'}\n"
                    elif "direct_parents" in info:
                        parents = info["direct_parents"]
                        response += f"Dependencies: {', '.join(parents) if parents else 'None'}\n"
                    if "full_result" in info:
                        response += f"Details: {info['full_result']}\n"
                    if "error" in info:
                        response += f"Error: {info['error']}\n"
                else:
                    response += f"Info: {info}\n"
                response += "\n"
        else:
            response += "No lineage information found in collected data.\n"
        
        return json.dumps({
            "answer": response,
            "query_type": "lineage",
            "tables_analyzed": list(lineage_info.keys()),
            "explanation": f"Generated lineage answer for {len(lineage_info)} tables"
        }, ensure_ascii=False)

    def _generate_metadata_answer_from_data(self, user_query: str, intent_analysis: Dict[str, Any], collected_data: Dict[str, Any]) -> str:
        """Generate metadata answer using collected data"""
        metadata_info = collected_data.get("metadata_info", {})
        tool_calls = collected_data.get("tool_calls", {})
        
        response = f"Metadata Information for: {user_query}\n\n"
        
        if metadata_info:
            if isinstance(metadata_info, dict):
                for table, info in metadata_info.items():
                    response += f"Table: {table}\n"
                    if isinstance(info, dict):
                        if "documents" in info:
                            docs = info["documents"]
                            response += f"Documents: {len(docs)} found\n"
                            for i, doc in enumerate(docs[:3], 1):  # Show first 3 docs
                                preview = doc[:200] + "..." if len(doc) > 200 else doc
                                response += f"  Doc {i}: {preview}\n"
                        if "full_result" in info:
                            response += f"Details: {info['full_result']}\n"
                        if "error" in info:
                            response += f"Error: {info['error']}\n"
                    else:
                        response += f"Info: {info}\n"
                    response += "\n"
            else:
                response += f"Metadata Info: {metadata_info}\n"
        else:
            response += "No metadata information found in collected data.\n"
        
        return json.dumps({
            "answer": response,
            "query_type": "metadata",
            "tables_analyzed": list(metadata_info.keys()) if isinstance(metadata_info, dict) else [],
            "explanation": f"Generated metadata answer using collected data"
        }, ensure_ascii=False)

    def _generate_general_answer_from_data(self, user_query: str, intent_analysis: Dict[str, Any], collected_data: Dict[str, Any]) -> str:
        """Generate general answer using collected data"""
        search_results = collected_data.get("search_results", [])
        tool_calls = collected_data.get("tool_calls", {})
        
        response = f"General Information for: {user_query}\n\n"
        
        if search_results:
            response += f"Found {len(search_results)} relevant documents:\n\n"
            for i, result in enumerate(search_results, 1):
                preview = result[:300] + "..." if len(result) > 300 else result
                response += f"Result {i}:\n{preview}\n\n"
        else:
            response += "No relevant information found in collected data.\n"
        
        return json.dumps({
            "answer": response,
            "query_type": "general_search",
            "documents_found": len(search_results),
            "explanation": f"Generated general answer using {len(search_results)} collected documents"
        }, ensure_ascii=False)
    
    def generate_answer(self, query: str, intent_analysis: Dict[str, Any], collected_data: Dict[str, Any]) -> str:
        """Generate answer with product logic using data bucket"""
        try:
            query_type = intent_analysis.get("query_type", "general_search")
            
            print(f"🤖 QueryWriterAgent generating answer for query type: {query_type}")
            print(f"📊 Using data bucket with keys: {list(collected_data.keys())}")
            
            if query_type == "sql_generation":
                return self._generate_sql_answer(query, intent_analysis, collected_data)
            elif query_type == "lineage":
                return self._generate_lineage_answer(query, intent_analysis, collected_data)
            elif query_type == "metadata":
                return self._generate_metadata_answer(query, intent_analysis, collected_data)
            else:
                return self._generate_general_answer(query, intent_analysis, collected_data)
                
        except Exception as e:
            return f"Error generating answer: {str(e)}"
    
    def _generate_sql_answer(self, query: str, intent_analysis: Dict[str, Any], collected_data: Dict[str, Any]) -> str:
        """Generate SQL answer with product column logic using data bucket"""
        try:
            # Determine product filter
            product_filter = self._determine_product_filter(query)
            
            # Get metadata and lineage from data bucket
            metadata_info = collected_data.get("metadata_info", {})
            lineage_info = collected_data.get("lineage_info", {})
            
            # Prepare requirements for SQL generation
            requirements = {
                "user_query": query,
                "table_info": metadata_info,
                "lineage_info": lineage_info,
                "context": f"Product filter: {product_filter['explanation']}",
                "product_filter": product_filter
            }
            
            # Generate SQL
            sql_result = self.generate_sql_query_fn(json.dumps(requirements, ensure_ascii=False))
            
            # Parse result
            try:
                result = json.loads(sql_result)
            except:
                result = {"query": sql_result, "explanation": "Generated SQL query"}
            
            # Format response
            response = f"SQL Query for: {query}\n\n"
            response += f"Product Filter: {product_filter['explanation']}\n\n"
            
            if "query" in result:
                response += f"Generated SQL:\n```sql\n{result['query']}\n```\n\n"
            
            if "explanation" in result:
                response += f"Explanation: {result['explanation']}\n\n"
            
            if "alternative_queries" in result:
                response += "Alternative Queries:\n"
                for i, alt_query in enumerate(result["alternative_queries"], 1):
                    response += f"{i}. {alt_query}\n"
            
            return response
            
        except Exception as e:
            return f"Error generating SQL answer: {str(e)}"
    
    def _generate_lineage_answer(self, query: str, intent_analysis: Dict[str, Any], collected_data: Dict[str, Any]) -> str:
        """Generate lineage answer using data bucket"""
        lineage_info = collected_data.get("lineage_info", {})
        tool_calls = collected_data.get("tool_calls", {})
        
        response = f"Lineage Information for: {query}\n\n"
        
        if lineage_info:
            for table, info in lineage_info.items():
                response += f"Table: {table}\n"
                if isinstance(info, dict):
                    if "upstream_dependencies" in info:
                        parents = info["upstream_dependencies"]
                        response += f"Dependencies: {', '.join(parents) if parents else 'None'}\n"
                    elif "direct_parents" in info:
                        parents = info["direct_parents"]
                        response += f"Dependencies: {', '.join(parents) if parents else 'None'}\n"
                    if "full_result" in info:
                        response += f"Details: {info['full_result']}\n"
                    if "error" in info:
                        response += f"Error: {info['error']}\n"
                else:
                    response += f"Info: {info}\n"
                response += "\n"
        else:
            response += "No lineage information found in data bucket.\n"
        
        return response
    
    def _generate_metadata_answer(self, query: str, intent_analysis: Dict[str, Any], collected_data: Dict[str, Any]) -> str:
        """Generate metadata answer using data bucket"""
        metadata_info = collected_data.get("metadata_info", {})
        tool_calls = collected_data.get("tool_calls", {})
        
        response = f"Metadata Information for: {query}\n\n"
        
        if metadata_info:
            if isinstance(metadata_info, dict):
                for table, info in metadata_info.items():
                    response += f"Table: {table}\n"
                    if isinstance(info, dict):
                        if "documents" in info:
                            docs = info["documents"]
                            response += f"Documents: {len(docs)} found\n"
                            for i, doc in enumerate(docs[:3], 1):  # Show first 3 docs
                                preview = doc[:200] + "..." if len(doc) > 200 else doc
                                response += f"  Doc {i}: {preview}\n"
                        if "full_result" in info:
                            response += f"Details: {info['full_result']}\n"
                        if "error" in info:
                            response += f"Error: {info['error']}\n"
                    else:
                        response += f"Info: {info}\n"
                    response += "\n"
            else:
                response += f"Metadata Info: {metadata_info}\n"
        else:
            response += "No metadata information found in data bucket.\n"
        
        return response
    
    def _generate_general_answer(self, query: str, intent_analysis: Dict[str, Any], collected_data: Dict[str, Any]) -> str:
        """Generate general answer using data bucket"""
        search_results = collected_data.get("search_results", [])
        tool_calls = collected_data.get("tool_calls", {})
        
        response = f"General Information for: {query}\n\n"
        
        if search_results:
            response += f"Found {len(search_results)} relevant documents:\n\n"
            for i, result in enumerate(search_results, 1):
                preview = result[:300] + "..." if len(result) > 300 else result
                response += f"Result {i}:\n{preview}\n\n"
        else:
            response += "No relevant information found in data bucket.\n"
        
        return response
    
    def run(self, user_query: str, intent_analysis: Dict[str, Any], collected_data: Dict[str, Any]) -> str:
        """Run query writing using LangChain Agent with all inputs"""
        try:
            # Store data globally for tools to access
            self.current_data = {
                "user_query": user_query,
                "intent_analysis": intent_analysis,
                "collected_data": collected_data
            }
            # Simple agent input
            agent_input = f"""
            TASK: Use LangChain Agent to call tools and generate final answer for user query.
            
            User Query: {user_query}
            
            Process:
            1. Analyze the user query
            2. Call the appropriate tool to generate the final answer
            3. Return the complete answer for the user
            
            Choose the right tool:
            - Use ValidateTableExists for table validation requests
            - Use GenerateSQLQuery for SQL generation requests
            - Use GenerateGeneralAnswer for other types of questions
            
            IMPORTANT: The tools have access to all the data automatically.
            """
            
            print("🤖 QueryWriterAgent is thinking and calling tools...")
            
            # Use LangChain Agent
            result = self.agent.run(agent_input)
            
            print("\n" + "="*50)
            print(" QUERY WRITER AGENT RESULT:")
            print("="*50)
            print(result)
            print("="*50)
            
            return result
            
        except Exception as e:
            print(f"❌ Error in QueryWriterAgent: {e}")
            return f"Error generating final answer: {str(e)}" 