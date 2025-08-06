#!/usr/bin/env python3
"""
Agent Logger for capturing session data and evaluation metrics.
"""

import os
import uuid
import time
from datetime import datetime
from typing import Dict, Any, Optional

from google.cloud import bigquery
from dotenv import load_dotenv


class AgentLogger:
    """
    logger for capturing agent sessions. this is meant to be applies to the root agent + sub-agents/tools.
    """

    def __init__(self, project_id: str, dataset_id: str):
        load_dotenv()
        # set project and dataset to insert logs to
        self.project_id = project_id or os.getenv('BQ_DATA_PROJECT_ID', 'dig-coe-genai-0548')
        self.dataset_id = dataset_id or os.getenv('BQ_DATASET_ID', 'ai_agent_dev')
        #initialize bq client
        self.client = bigquery.Client(project=self.project_id)
        # session tracking
        self.current_session_id: Optional[str] = None
        self.session_start_time: Optional[datetime] = None
        self.turn_counter = 0

        print(f"AgentLogger initialized for {self.project_id}.{self.dataset_id}")

    def start_session(self, session_id: str, user_id: str = "test_user") -> str:
        """"
        this generates and stores the session level bq table
        """
        start_time = datetime.now()

        self.current_session_id = session_id
        self.session_start_time = start_time
        self.turn_counter = 0

        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'project_id': self.project_id,
            'start_timestamp': start_time.isoformat(),
            'end_timestamp': None
        }

        table_id = f"{self.project_id}.{self.dataset_id}.sessions"
        table = self.client.get_table(table_id)

        errors = self.client.insert_rows_json(table, [session_data])
        if errors:
            print(f"Error inserting session data: {errors}")
        else:
            print(f"Session started: {session_id}")

        return session_id
    
    def log_turn(self, session_id: str, turn_data: Dict[str, Any]) -> None:
        """
        Log a turn with the provided turn data.
        
        Args:
            session_id: The session ID
            turn_data: Dictionary containing turn information including agent_type and response_source
        """
        try:
            # Log to BigQuery
            turns_table_id = f"{self.project_id}.{self.dataset_id}.turns"
            turns_table = self.client.get_table(turns_table_id)
            turn_errors = self.client.insert_rows_json(turns_table, [turn_data])
            
            if turn_errors:
                print(f"Error inserting turn data: {turn_errors}")
            else:
                agent_type = turn_data.get('agent_type', 'unknown')
                print(f"Logged turn for session {session_id} - Agent: {agent_type}")
                
        except Exception as e:
            print(f"Error logging turn: {e}")

