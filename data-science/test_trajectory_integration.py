#!/usr/bin/env python3
"""
Test script to verify trajectory evaluation integration.
"""

import sys
import os

# Add the data_science module to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'data_science'))

from data_science.utils.trajectory_evaluator import run_trajectory_evaluation


def test_trajectory_evaluation():
    """Test trajectory evaluation with sample session data."""
    
    # Sample session data that mimics what the agent would produce
    session_state = {
        "session_id": "test_session_456",
        "turns": [
            {
                "agent_type": "root",
                "user_input": "How many visitors did we have onsite in the last 3 weeks?",
                "agent_response": "I'll use the database agent to query the weekly active users data. call_db_agent"
            },
            {
                "agent_type": "db_agent",
                "user_input": "How many visitors did we have onsite in the last 3 weeks?",
                "agent_response": "SELECT report_starts, sum(users) FROM `dig-coe-genai-0548.ai_agent_dev.weekly_active_users_agg` WHERE report_starts >= DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 3 WEEK), WEEK(Monday)) AND product = 'enterprise' GROUP BY ALL ORDER BY 1"
            }
        ]
    }
    
    print("🧪 Testing trajectory evaluation integration...")
    
    # Run trajectory evaluation
    result = run_trajectory_evaluation(
        session_id="test_session_456",
        session_state=session_state,
        user_query="How many visitors did we have onsite in the last 3 weeks?"
    )
    
    if result:
        print("✅ Trajectory evaluation test passed!")
        print(f"   Tool selection score: {result['tool_selection_score']}")
        print(f"   SQL generation score: {result['sql_generation_score']}")
        print(f"   Table usage score: {result['table_usage_score']}")
    else:
        print("❌ Trajectory evaluation test failed!")
    
    return result is not None


if __name__ == "__main__":
    success = test_trajectory_evaluation()
    if success:
        print("\n🎉 Integration test successful! Trajectory evaluation is ready to use.")
    else:
        print("\n💥 Integration test failed. Check the logs above.") 