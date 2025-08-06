from typing import Dict, Any
from langchain.agents import initialize_agent, AgentType
from langchain.agents import Tool
from agents.base_agent import BaseAgent
import json
import re

class IntentAgent(BaseAgent):
    """Intent Analysis Agent for analyzing user query types and intentions"""
    
    def __init__(self):
        super().__init__()
        self.data_domains = self._create_data_domains()
        self.tools = self._create_tools()
        self.agent = self._create_agent()
        self.last_response_content = None  # Store response content for next step
    
    def _create_data_domains(self):
        """Create data domain mappings"""
        return {
            "user_activity": {
                "keywords": [
                    "visitors", "visitor", "visit", "visited", "visiting",
                    "onsite", "on-site", "site", "website", "web",
                    "unique visitors", "unique users", "unique sessions",
                    "daily active", "weekly active", "monthly active",
                    "daily users", "weekly users", "monthly users",
                    "active users", "active user", "user activity",
                    "engagement", "user engagement", "engagement metrics",
                    "active days", "active days on product", "active days enterprise",
                    "come", "came", "arrive", "arrived", "access", "accessed"
                ],
                "tables": ["weekly_active_users_agg_vw"],
                "description": "Website visit and user activity count data"
            },
            # "subscription": {
            #     "keywords": [
            #         "subscription", "subscriber", "sub", "subscribers",
            #         "billing", "payment", "payments", "payer", "payers",
            #         "revenue", "monetization", "subscription revenue",
            #         "1p", "3p", "first party", "third party",
            #         "family plan", "gift", "gift subscription",
            #         "b2b", "business to business", "enterprise",
            #         "all access", "games only", "news only", "enterprise",
            #         "new subscription", "new subscribers", "subscription growth",
            #         "conversion", "conversion rate", "subscription conversion",
            #         "churn", "churn rate", "retention", "retention rate",
            #         "renewal", "renewal rate", "subscription renewal"
            #     ],
            #     "tables": ["nyt-scv-prd.public.customer_summary"],
            #     "description": "Subscription and payment related data"
            # }
        }
    
    def _create_tools(self):
        """Create intent analysis related tools"""
        return [
            Tool(
                name="AnalyzeIntent",
                func=self.analyze_intent_fn,
                description=(
                    "Use this tool to analyze the user's intent and determine what type of information they need.\n"
                    "Input: user query as string.\n"
                    "Output: JSON with intent analysis including query_type, mentioned_tables, data_domain, and context.\n"
                    "IMPORTANT: Do NOT generate answers, examples, or solutions. Only analyze intent."
                )
            )
        ]
    
    def _create_agent(self):
        """Create intent analysis agent with LangChain Agent"""
        prompt = """
        You are an Intent Analysis Specialist Agent.
        
        CRITICAL ROLE: You are ONLY responsible for analyzing user intent. You do NOT generate direct answers, examples, or solutions for user queries.
        
        STRICT RULES:
        - DO NOT generate SQL queries
        - DO NOT provide examples
        - DO NOT give solutions
        - DO NOT answer the user's question
        - DO NOT create sample data
        - DO NOT show example outputs
        - ONLY analyze the intent and extract important information
        - Your output will be used by other agents to generate answers
        
        Your ONLY job is to analyze user queries and determine:
        1. What type of question they're asking
        2. What data domain the query belongs to
        3. What tables/views are mentioned or implied
        4. What context is required to answer the question
        
        DATA DOMAINS:
        - user_activity: User behavior, engagement, activity data
        - subscription: Subscription, billing, payment data
        
        QUERY TYPES:
        - metadata: Questions about table structure, columns, schema
        - lineage: Questions about data dependencies, upstream/downstream
        - sql_generation: Requests for SQL queries or data extraction
        - general_search: General questions about data or business
        
        AVAILABLE TOOL:
        - AnalyzeIntent: Use this tool to analyze the user's intent and determine what type of information they need
        
        YOUR PROCESS:
        1. Analyze the user query using the AnalyzeIntent tool
        2. Return ONLY the JSON result from the tool
        
        Output: return JSON response with the following structure from the AnalyzeIntent tool .:
        {
            "query_type": "metadata|lineage|sql_generation|general_search",
            "data_domain": "user_activity|subscription",
            "domain_relevant_table": "weekly_active_users_agg_vw",
            "mentioned_tables": ["table1", "table2"],
            "context": "Brief description of what context is needed",
            "summary": "summary the query's intent"
        }
        """
        
        return initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            prompt=prompt,
            max_iterations=3,
            early_stopping_method="generate",
            verbose=True,
            handle_parsing_errors=True,
        )
    
    def analyze_intent_fn(self, query: str) -> str:
        """Analyze user intent and determine query type"""
        print("🔧 AnalyzeIntent Tool Called")
        
        # Create a comprehensive prompt for intent analysis with data domains
        # analysis_prompt = f"""
        # Analyze the following user query and determine their intent:
        
        # User Query: {query}
        
        # AVAILABLE DATA DOMAINS AND TABLES:
        # {json.dumps(self.data_domains, indent=2)}
        
        # Use the data domains dictionary to help identify:
        # 1. Which data domain the query belongs to based on keywords
        # 2. Which tables are relevant based on the domain and query content
        # 3. Whether the query mentions specific tables or implies them through domain keywords
        
        # Provide a JSON response with the following structure:
        # {{
        #     "query_type": "metadata|lineage|sql_generation|general_search",
        #     "data_domain": "user_activity|subscription",
        #     "domain_relevant_table": "weekly_active_users_agg_vw|nyt-scv-prd.public.customer_summary",
        #     "mentioned_tables": ["table1", "table2"],
        #     "context": "Brief description of what context is needed",
        #     "summary": "summary the query's intent"
        # }}
        
        # ANALYSIS RULES:
        # - query_type: Determine if they want metadata, lineage, SQL generation, or general search
        # - data_domain: Identify the business domain using keywords from the data_domains dictionary
        # - domain_relevant_table: Extract the relevant table based on the identified domain
        # - mentioned_tables: Extract any table names mentioned or implied using the data_domains dictionary
        # - context: Describe what additional context would help answer this query
        # - summary: Provide a brief summary of the user's intent
        
        # EXAMPLES:
        # - Query: "How many visitors did we have?" → data_domain: "user_activity", domain_relevant_table: "weekly_active_users_agg_vw"
        # - Query: "Show subscription data" → data_domain: "subscription", domain_relevant_table: "nyt-scv-prd.public.customer_summary"
        
        # Return only the JSON response, no explanations.
        # """
        analysis_prompt = f"""
        Analyze the following user query and determine their intent:
        
        User Query: {query}
        
        AVAILABLE DATA DOMAINS AND TABLES:
        {json.dumps(self.data_domains, indent=2)}
        
        Use the data domains dictionary to help identify:
        1. Which data domain the query belongs to based on keywords
        2. Which tables are relevant based on the domain and query content
        3. Whether the query mentions specific tables or implies them through domain keywords
        
        Provide a JSON response with the following structure:
        {{
            "query_type": "metadata|lineage|sql_generation|general_search",
            "data_domain": "user_activity|subscription",
            "domain_relevant_table": "weekly_active_users_agg_vw",
            "mentioned_tables": ["table1", "table2"],
            "context": "Brief description of what context is needed",
            "summary": "summary the query's intent"
        }}
        
        ANALYSIS RULES:
        - query_type: Determine if they want metadata, lineage, SQL generation, or general search
        - data_domain: Identify the business domain using keywords from the data_domains dictionary
        - domain_relevant_table: Extract the relevant table based on the identified domain
        - mentioned_tables: Extract any table names mentioned or implied using the data_domains dictionary
        - context: Describe what additional context would help answer this query
        - summary: Provide a brief summary of the user's intent
        
        EXAMPLES:
        - Query: "How many visitors did we have?" → data_domain: "user_activity", domain_relevant_table: "weekly_active_users_agg_vw"
        
        Return only the JSON response, no explanations.
        """
        
        # Use LLM to analyze intent
        response = self.llm.invoke(analysis_prompt)
        print(response.content)
        self.last_response_content = response.content
        return response.content
        
    def run(self, query: str) -> Dict[str, Any]:
        result = self.agent.run(query)  # result is a JSON string
        print("✅ Final Agent Output:")
        print(result)