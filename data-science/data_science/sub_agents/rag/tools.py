# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""RAG tools for retrieving private knowledge using Vertex AI."""

from google.adk.tools.tool_context import ToolContext
from ...utils.reference_guide_RAG import rag_response


def call_rag_tool(
    query: str,
    tool_context: ToolContext,
) -> str:
    """Retrieves relevant private knowledge using Vertex AI RAG.
    
    Args:
        query: The user's question to search for relevant knowledge
        tool_context: The tool context
        
    Returns:
        str: Retrieved knowledge and enhanced response
    """
    try:
        # Get RAG response from Vertex AI
        rag_result = rag_response(query)
        
        # Store RAG result in context for potential use by other agents
        tool_context.state["rag_result"] = rag_result
        
        return f"""
**RAG Knowledge Retrieved:**

{rag_result}

**Enhanced Response:**
Based on the retrieved knowledge, here's the answer to your question: {query}

The above information was retrieved from our private knowledge base using Vertex AI RAG technology.
        """
        
    except Exception as e:
        return f"Error retrieving RAG knowledge: {str(e)}" 