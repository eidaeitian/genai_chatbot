import uuid
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from google.cloud import bigquery
from dotenv import load_dotenv

@dataclass
class TrajectoryStep:
    step_id: str
    timestamp: datetime
    agent_type: str
    tool_called: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[str] = None
    decision_reasoning: Optional[str] = None
    sql_generated: Optional[str] = None
    table_used: Optional[str] = None
    
@dataclass
class SessionTrajectory:
    session_id: str
    original_query: str
    final_response: str
    trajectory_steps: List[TrajectoryStep]
    start_time: datetime
    end_time: datetime
    total_steps: int
    success: bool
    error_message: Optional[str] = None 

class TrajectoryLogger:
    def __init__(self, project_id: str, dataset_id: str):
        load_dotenv()
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.client = bigquery.Client(project=self.project_id)
        self.current_session_id: Optional[str] = None
        self.session_start_time: Optional[datetime] = None
        self.trajectory_steps: List[TrajectoryStep] = []
        self.original_query: Optional[str] = None

        print(f"TrajectoryLogger initialized for {self.project_id}.{self.dataset_id}")

    
    def start_session(self, session_id: str) -> str:
        # Clear any existing session state
        if self.current_session_id:
            print(f"WARNING: Starting new session {session_id} while session {self.current_session_id} was still active")
            
        self.current_session_id = session_id
        self.session_start_time = datetime.now()
        self.trajectory_steps = []
        print(f"Session started: {session_id}")
        return session_id
    
    def log_tool_call(self, agent_type: str, tool_name: str, tool_input: Dict[str, Any], tool_output: str, decision_reasoning: Optional[str] = None) -> None:
        step = TrajectoryStep(
            step_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            agent_type=agent_type,
            tool_called=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            decision_reasoning=decision_reasoning
        )
        self.trajectory_steps.append(step)
        print(f"Logged tool call: {agent_type} -> {tool_name}")

    def log_sql_generation_and_decision(self, agent_type: str, sql: str, table_used: str, decision_reasoning: str) -> None:
        step = TrajectoryStep(
            step_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            agent_type=agent_type,
            sql_generated=sql,
            table_used=table_used,
            decision_reasoning=decision_reasoning
        )
        self.trajectory_steps.append(step)
        print(f"Logged SQL generation: {agent_type} --> table: {table_used}")

    def log_decision_and_reasoning(self, agent_type: str, decision_reasoning: str) -> None:
        if not self.current_session_id:
            print(f"WARNING: Attempting to log decision without active session: {agent_type}")
            return
            
        step = TrajectoryStep(
            step_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            agent_type=agent_type,
            decision_reasoning=decision_reasoning
        )
        self.trajectory_steps.append(step)
        print(f"Logged decision: {agent_type} --> {decision_reasoning} (session: {self.current_session_id}, total steps: {len(self.trajectory_steps)})")

    def end_session(self, final_response: str, success: bool = True, 
                   error_message: Optional[str] = None, clear_session: bool = True) -> SessionTrajectory:
        """End session and return complete trajectory"""
        if not self.session_start_time:
            raise ValueError("No session started")
        
        # Prevent multiple session endings
        if not self.current_session_id:
            print("Session already ended, skipping duplicate end_session call")
            return None
        
        session_trajectory = SessionTrajectory(
            session_id=self.current_session_id,
            original_query=self.original_query or "N/A",
            final_response=final_response,
            trajectory_steps=self.trajectory_steps,
            start_time=self.session_start_time,
            end_time=datetime.now(),
            total_steps=len(self.trajectory_steps),
            success=success,
            error_message=error_message
        )

        session_data = {
        'session_id': self.current_session_id,
        'original_query': self.original_query or "N/A",
        'final_response': final_response,
        'start_time': self.session_start_time.isoformat(),
        'end_time': datetime.now().isoformat(),
        'total_steps': len(self.trajectory_steps),
        'success': success,
        'error_message': error_message
        }

        sessions_table_id = f"{self.project_id}.{self.dataset_id}.session_trajectories"
        sessions_table = self.client.get_table(sessions_table_id)
    
        session_errors = self.client.insert_rows_json(sessions_table, [session_data])
        if session_errors:
            print(f"Error logging session to BigQuery: {session_errors}")

        ## session step level
        for step in self.trajectory_steps:  # These are already TrajectoryStep objects
            step_data = {
            'step_id': step.step_id,
            'session_id': self.current_session_id,
            'timestamp': step.timestamp.isoformat(),
            'agent_type': step.agent_type,
            'tool_called': step.tool_called,
            'tool_input': str(step.tool_input),
            'tool_output': step.tool_output,
            'decision_reasoning': step.decision_reasoning,
            'sql_generated': step.sql_generated,
            'table_used': step.table_used
            }
        
            steps_table_id = f"{self.project_id}.{self.dataset_id}.trajectory_steps"
            steps_table = self.client.get_table(steps_table_id)
        
            step_errors = self.client.insert_rows_json(steps_table, [step_data])
            if step_errors:
                print(f"Error logging trajectory step: {step_errors}")
    
        print(f"Session ended: {self.current_session_id} with {len(self.trajectory_steps)} steps")
        
        # Debug: Print details of each step being logged
        if self.trajectory_steps:
            print(f"DEBUG: Logging {len(self.trajectory_steps)} trajectory steps:")
            for i, step in enumerate(self.trajectory_steps):
                print(f"  Step {i+1}: {step.agent_type} -> {step.tool_called or 'SQL generation'}")
        else:
            print("DEBUG: No trajectory steps to log")
        
        # Only clear session state if explicitly requested (for evaluation loops)
        if clear_session:
            session_id = self.current_session_id
            self.current_session_id = None
            self.session_start_time = None
            self.trajectory_steps = []
            self.original_query = None
        else:
            # For evaluation loops, keep the session active but clear the steps for the next question
            self.trajectory_steps = []
            print(f"DEBUG: Kept session {self.current_session_id} active for next question")
        
        return session_trajectory

    def force_end_session(self) -> None:
        """Force end the current session and clear all state - used for evaluation loop completion"""
        if self.current_session_id:
            print(f"Force ending session: {self.current_session_id}")
            self.current_session_id = None
            self.session_start_time = None
            self.trajectory_steps = []
            self.original_query = None
        else:
            print("No active session to force end")

# Create a global instance
trajectory_logger = TrajectoryLogger(
    project_id="dig-coe-genai-0548", 
    dataset_id="ai_agent_dev"
)