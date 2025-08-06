#!/usr/bin/env python3
"""
Optimized Three Agent System with Product Logic
Simplified version with full data collection
"""

import logging
from agents.intent_agent import IntentAgent
from agents.relevant_data_agent import RelevantDataAgent
from agents.query_writer_agent import QueryWriterAgent
import time
from typing import Dict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedThreeAgentSystemWithProductLogic:
    """Simplified three-agent system with full data collection"""
    
    def __init__(self):
        """Initialize the simplified three-agent system"""
        print("🚀 Initializing Simplified Three-Agent System...")
        
        # Initialize agents
        self.intent_agent = IntentAgent()
        self.relevant_data_agent = RelevantDataAgent()
        self.query_writer_agent = QueryWriterAgent()
        
        print("✅ All agents initialized")
    
    def process_query(self, user_query: str) -> str:
        """Simple three-stage pipeline with data bucket"""
        try:
            start_time = time.time()
            
            # Stage 1: Intent Analysis
            print("🔍 Stage 1: Intent Analysis...")
            intent_start = time.time()
            self.intent_agent.run(user_query)  # This stores last_response_content
            intent_time = time.time() - intent_start
            
            # print(f"✅ Intent Analysis Result:")
            # print(f"  - Query Type: {intent_analysis.get('query_type', 'unknown')}")
            # print(f"  - Mentioned Tables: {intent_analysis.get('mentioned_tables', [])}")
            # print(f"  - Data Domain: {intent_analysis.get('data_domain', 'unknown')}")
            # print(f"  - Time: {intent_time:.2f}s")
            
            # Stage 2: Data Collection
            print("\n📊 Stage 2: Data Collection...")
            data_start = time.time()
            data_bucket = self.relevant_data_agent.run(user_query, self.intent_agent.last_response_content)
            data_time = time.time() - data_start
            
            print(f"✅ Data Collection Result:")
            print(f"  - Data Bucket Keys: {list(data_bucket.keys())}")
            print(f"  - Time: {data_time:.2f}s")
            
            # 验证数据bucket
            print("\n" + "="*60)
            print("🔍 VERIFYING DATA BUCKET FOR NEXT AGENT:")
            print("="*60)
            required_keys = ['query', 'intent_analysis_response', 'lineage_info', 'metadata_info', 'search_results', 'tool_results']
            for key in required_keys:
                if key in data_bucket:
                    print(f"✅ {key}: {type(data_bucket[key])} - {data_bucket[key]}")
                else:
                    print(f"❌ Missing {key}")
            print("="*60)
            
            # Stage 3: Query Writing
            print("\n🤖 Stage 3: Query Writing...")
            writer_start = time.time()
            final_answer = self.query_writer_agent.run(user_query, self.intent_agent.last_response_content, data_bucket)
            writer_time = time.time() - writer_start
            
            print(f"✅ Query Writing Result:")
            print(f"  - Time: {writer_time:.2f}s")
            
            # Total time
            total_time = time.time() - start_time
            print(f"\n⏱️ Total Processing Time: {total_time:.2f}s")
            
            return final_answer
            
        except Exception as e:
            error_msg = f"Error in process_query: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def get_system_status(self) -> dict:
        """Get system status"""
        return {
            "intent_agent": "Active",
            "relevant_data_agent": "Active", 
            "query_writer_agent": "Active with Product Logic",
            "system": "Simplified with Full Data Collection"
        }

def main():
    """Main function for simplified three-agent system"""
    print("🚀 Simplified Three-Agent SQL Assistant")
    print("=" * 70)
    
    # Initialize system
    system = OptimizedThreeAgentSystemWithProductLogic()
    
    # Show system status
    status = system.get_system_status()
    print("\n📊 System Status:")
    for agent, state in status.items():
        print(f"  - {agent}: {state}")
    
    print("\n🔄 Simplified Pipeline Flow:")
    print("  Stage 1: IntentAgent → Analyze query type and mentioned tables")
    print("  Stage 2: RelevantDataAgent → Collect full data using tools")
    print("  Stage 3: QueryWriterAgent → Generate final answer with product logic")
    
    print("\n" + "=" * 70)
    print("💬 Start chatting (type 'exit' or 'quit' to exit)")
    print("=" * 70)
    
    # Main conversation loop
    while True:
        try:
            user_input = input("\n🤔 Your question: ").strip()
            
            if user_input.lower() in ("exit", "quit", "退出"):
                print("\n👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("\n🔄 Processing...")
            
            # Process query with performance tracking
            response = system.process_query(user_input)
            
            print(f"\n🤖 Answer:")
            print("-" * 40)
            print(response)
            print("-" * 40)
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted, goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            logger.error(f"Error processing query: {e}")

if __name__ == "__main__":
    main() 