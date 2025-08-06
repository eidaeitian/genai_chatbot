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

"""Top level agent for data agent multi-agents.

-- it get data from database (e.g., BQ) using NL2SQL
-- then, it use NL2Py to do further data analysis as needed
"""
import os
import time
from datetime import date, datetime

from google.genai import types

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import load_artifacts
from .utils.trajectory_logger import trajectory_logger


from .sub_agents.bigquery.tools import (
    get_database_settings as get_bq_database_settings,
)
from .prompts import return_instructions_root
from .tools import call_db_agent, call_ds_agent

date_today = date.today()


def setup_before_agent_call(callback_context: CallbackContext):
    """Setup the agent."""
    print("DEBUG: setup_before_agent_call is running")
    
    if "session_id" not in callback_context.state:
        print("DEBUG: Creating new session")
        session_id = callback_context._invocation_context.session.id
        callback_context.state["session_id"] = session_id
        callback_context.state["session_start_time"] = datetime.now().isoformat()        
        # Capture the original user query from ADK user_content
        user_query = "N/A"
        if callback_context.user_content and callback_context.user_content.parts:
            user_query = callback_context.user_content.parts[0].text or "Non-text input"
        
        callback_context.state["original_user_query"] = user_query
        print(f"DEBUG: Captured original user query: '{user_query}'")
        
        #start session for logger
        print(f"DEBUG: Starting session with ID: {session_id}")
        trajectory_logger.start_session(session_id)
        trajectory_logger.original_query = user_query
    else:
        print("DEBUG: Session already exists")
        
    # setting up database settings in session.state
    if "database_settings" not in callback_context.state:
        db_settings = dict()
        db_settings["use_database"] = "BigQuery"
        callback_context.state["all_db_settings"] = db_settings

    # setting up schema in instruction
    if callback_context.state["all_db_settings"]["use_database"] == "BigQuery":
        callback_context.state["database_settings"] = get_bq_database_settings()
        schema = callback_context.state["database_settings"]["bq_ddl_schema"]

        callback_context._invocation_context.agent.instruction = (
            return_instructions_root()
            + f"""

    --------- The BigQuery schema of the relevant data with a few sample rows. ---------
    {schema}

    """
        )


def setup_after_model_call(callback_context: CallbackContext, *, llm_response):
    """Capture root agent responses when no tools/sub-agents are called."""
    print("DEBUG: after_model_callback is running")
    
    # Get the session data
    session_id = callback_context.state.get("session_id")    
    if session_id:
        try:
            
            # Extract the response text from the model response
            response_text = ""
            if hasattr(llm_response, 'parts') and llm_response.parts:
                response_text = llm_response.parts[0].text if llm_response.parts[0].text else ""
            elif hasattr(llm_response, 'text'):
                response_text = llm_response.text
            else:
                response_text = str(llm_response)
            
            # Don't end session here - let tools handle their own session ending
            # The session will be ended by the tools when they complete
            print(f"DEBUG: Direct root agent response - no tools called")
            print(f"DEBUG: Logged direct root agent response for session {session_id}")
            
        except Exception as e:
            print(f"Error logging direct root agent response: {e}")
    else:
        print("DEBUG: No session_id found in after_model_callback")
    
    # Return None to not modify the response
    return None

root_agent = Agent(
    model=os.getenv("ROOT_AGENT_MODEL"),
    name="db_ds_multiagent",
    instruction=return_instructions_root(),
    global_instruction=(
        f"""
        You are a Data Science and Data Analytics Multi Agent System.
        Todays date: {date_today}
        """
    ),
    sub_agents=[],
    tools=[
        call_db_agent,
        call_ds_agent,
        load_artifacts,
    ],
    before_agent_callback=setup_before_agent_call,
    after_model_callback=setup_after_model_call,
    generate_content_config=types.GenerateContentConfig(temperature=0.01),
)
