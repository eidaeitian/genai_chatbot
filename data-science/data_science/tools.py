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

from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool

from .sub_agents import ds_agent, db_agent

## importing trajectory logger
try:
    from .utils.trajectory_logger import trajectory_logger
    print("SUCCESS: Imported trajectory_logger from trajectory_logger module")
except Exception as e:
    print(f"ERROR importing trajectory_logger: {e}")


async def call_db_agent(
    question: str,
    tool_context: ToolContext,
):
    """Tool to call database (nl2sql) agent."""
    print("DEBUG: call_db_agent was called!")
    
    print(
        "\n call_db_agent.use_database:"
        f' {tool_context.state["all_db_settings"]["use_database"]}'
    )
    ## make sure logger is initiated correctly
    print(f"DEBUG: trajectory_logger.current_session_id = {trajectory_logger.current_session_id}")
    print(f"DEBUG: trajectory_logger.trajectory_steps count = {len(trajectory_logger.trajectory_steps)}")
    print(f"DEBUG: After logging, trajectory_steps count = {len(trajectory_logger.trajectory_steps)}")


    agent_tool = AgentTool(agent=db_agent)

    ## log the initial tool call
    trajectory_logger.log_tool_call(
        agent_type="root",
        tool_name="call_db_agent",
        tool_input={"question": question},
        tool_output="N/A"  # Will be updated after execution
        ) 

    db_agent_output = await agent_tool.run_async(
        args={"request": question}, tool_context=tool_context
    )
    tool_context.state["db_agent_output"] = db_agent_output

    ## log the tool output
    trajectory_logger.log_tool_call(
        agent_type="root",
        tool_name="final_response",
        tool_input={"question": question},
        tool_output=str(db_agent_output)  # The complete response with explanation
        )
    
    try:
        session_trajectory = trajectory_logger.end_session(
        final_response=str(db_agent_output),
        success=True,
        clear_session=False  # Keep session active for evaluation loop
    )
        print(f"Trajectory session ended: {len(session_trajectory.trajectory_steps)} steps logged")
    except Exception as e:
        print(f"Error ending trajectory session: {e}")
    
    return db_agent_output


async def call_ds_agent(
    question: str,
    tool_context: ToolContext,
):
    """Tool to call data science (nl2py) agent."""
    print("DEBUG: call_ds_agent was called!")

    if question == "N/A":
        return tool_context.state["db_agent_output"]
    
    ## make sure logger is initiated correctly
    print(f"DEBUG: trajectory_logger.current_session_id = {trajectory_logger.current_session_id}")
    print(f"DEBUG: trajectory_logger.trajectory_steps count = {len(trajectory_logger.trajectory_steps)}")
    print(f"DEBUG: After logging, trajectory_steps count = {len(trajectory_logger.trajectory_steps)}")

    input_data = tool_context.state["query_result"]

    question_with_data = f"""
  Question to answer: {question}

  Actual data to analyze prevoius quesiton is already in the following:
  {input_data}

  """

    agent_tool = AgentTool(agent=ds_agent)

    ## log the initial tool call
    trajectory_logger.log_tool_call(
        agent_type="root",
        tool_name="call_ds_agent",
        tool_input={"question": question},
        tool_output="N/A"  # Will be updated after execution
        ) 

    ds_agent_output = await agent_tool.run_async(
        args={"request": question_with_data}, tool_context=tool_context
    )
    tool_context.state["ds_agent_output"] = ds_agent_output

    ## log the tool output
    trajectory_logger.log_tool_call(
        agent_type="root",
        tool_name="final_response",
        tool_input={"question": question},
        tool_output=str(ds_agent_output)  # The complete response with explanation
        )
    
    # End trajectory session after successful execution
    try:
        session_trajectory = trajectory_logger.end_session(
            final_response=str(ds_agent_output),
            success=True,
            clear_session=False  # Keep session active for evaluation loop
        )
        print(f"Trajectory session ended: {len(session_trajectory.trajectory_steps)} steps logged")
    except Exception as e:
        print(f"Error ending trajectory session: {e}")
        
    return ds_agent_output
