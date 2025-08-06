# Trajectory Evaluation System Documentation

## Overview
The Trajectory Evaluation system assesses agent behavior by comparing actual agent actions against expected patterns defined in golden datasets. It evaluates tool selection, SQL generation, and table usage accuracy.

## Core Components

### 1. SimpleTrajectoryEvaluator Class
**Location:** `eval/simple_trajectory_evaluator.py`

The main evaluator that analyzes agent behavior patterns:

#### Key Functions:

**`__init__(config: TrajectoryConfig)`**
- Initializes evaluator with project configuration
- Sets up BigQuery connection for data access
- Prepares evaluation metrics tracking

**`extract_actual_trajectory(session_data: Dict[str, Any])`**
- Analyzes logged session data to understand what the agent actually did
- Extracts tool selection patterns (call_db_agent, call_ds_agent)
- Identifies SQL generation and table usage
- Returns structured trajectory data for comparison

**`_contains_sql(response: str)`**
- Detects SQL keywords in agent responses
- Uses case-insensitive pattern matching
- Identifies SQL generation capability

**`_extract_table_from_sql(response: str)`**
- Extracts table names from SQL queries using regex
- Supports multiple SQL table patterns
- Returns table name for usage tracking

**`parse_expected_trajectory(expected_trajectory: List[str])`**
- Parses golden dataset expected behaviors
- Converts text descriptions to structured format
- Prepares expected trajectory for comparison

### 2. Trajectory Evaluation Orchestrator
**Location:** `data_science/utils/trajectory_evaluator.py`

Coordinates the evaluation process:

#### Key Functions:

**`load_golden_dataset()`**
- Loads benchmark test cases from JSON file
- Provides expected behavior patterns
- Returns list of test cases for matching

**`find_matching_test_case(query: str, golden_dataset: list)`**
- Searches golden dataset for matching user queries
- Uses case-insensitive exact matching
- Returns matching test case or None

**`run_trajectory_evaluation(session_id: str, session_state, user_query: str = None)`**
- Main evaluation orchestration function
- Loads golden dataset and finds matching test case
- Extracts actual trajectory from session data
- Compares actual vs expected behavior
- Calculates evaluation scores
- Logs results to BigQuery

**`log_trajectory_evaluation(session_id: str, evaluation_result: Dict, test_case: Dict)`**
- Stores evaluation results in BigQuery
- Creates evaluation records with metrics
- Handles table creation if needed
- Provides audit trail for evaluations

## Evaluation Process

### 1. Test Case Matching
```python
# Find matching test case in golden dataset
test_case = find_matching_test_case(user_query, golden_dataset)
if not test_case:
    return None  # No evaluation if no matching test case
```

**What happens:**
- Searches golden dataset for exact query match
- Loads expected behavior patterns
- Prepares for trajectory comparison

### 2. Actual Trajectory Extraction
```python
# Extract what the agent actually did
actual_trajectory = evaluator.extract_actual_trajectory(session_dict)
```

**What happens:**
- Analyzes logged session turns
- Identifies tool selection decisions
- Detects SQL generation patterns
- Extracts table usage information

### 3. Expected Trajectory Parsing
```python
# Parse what the agent should have done
expected_trajectory = evaluator.parse_expected_trajectory(test_case['expected_trajectory'])
```

**What happens:**
- Converts golden dataset expectations to structured format
- Maps expected tool selections
- Identifies expected SQL generation requirements
- Prepares for comparison

### 4. Score Calculation
```python
# Calculate evaluation scores
evaluation_result = {
    'actual_trajectory': actual_trajectory,
    'expected_trajectory': expected_trajectory,
    'tool_selection_score': 1.0 if actual_trajectory['tool_selection'] == expected_trajectory['tool_selection'] else 0.0,
    'sql_generation_score': 1.0 if actual_trajectory['sql_generation'] == expected_trajectory['sql_generation'] else 0.0,
    'table_usage_score': 1.0 if actual_trajectory['table_used'] == test_case.get('expected_table', 'N/A') else 0.0
}
```

**What happens:**
- Compares actual vs expected tool selection
- Evaluates SQL generation accuracy
- Assesses table usage correctness
- Calculates binary success scores

## Integration Points

### 1. Session Completion Trigger
**Location:** `data_science/agent.py:90` - `setup_after_model_call()`

```python
# Trigger trajectory evaluation after session completes
from .utils.trajectory_evaluator import run_trajectory_evaluation

evaluation_result = run_trajectory_evaluation(
    session_id=session_id,
    session_state=callback_context.state,
    user_query=user_query
)
```

**What happens:**
- Triggers evaluation when session ends
- Passes session data and user query
- Executes evaluation pipeline
- Logs results for analysis

### 2. BigQuery Data Access
**Location:** `data_science/utils/trajectory_evaluator.py:118`

```python
# Fetch turns from BigQuery if not in session state
query = f"""
SELECT * FROM `dig-coe-genai-0548.ai_agent_dev.turns` 
WHERE session_id = '{session_dict['session_id']}'
ORDER BY turn_number
"""
```

**What happens:**
- Retrieves logged turns from BigQuery
- Converts BigQuery results to evaluation format
- Ensures complete session data for analysis
- Handles data access errors gracefully

## Evaluation Metrics

### 1. Tool Selection Accuracy
- **Metric:** Binary score (1.0 = correct, 0.0 = incorrect)
- **Evaluation:** Compares actual tool choice vs expected
- **Examples:** call_db_agent vs call_ds_agent selection

### 2. SQL Generation Accuracy
- **Metric:** Binary score (1.0 = SQL generated when expected, 0.0 = incorrect)
- **Evaluation:** Checks if SQL was generated when required
- **Detection:** SQL keyword pattern matching

### 3. Table Usage Accuracy
- **Metric:** Binary score (1.0 = correct table, 0.0 = incorrect)
- **Evaluation:** Compares actual table vs expected table
- **Extraction:** Regex-based table name extraction

## Golden Dataset Structure

### Test Case Format
```json
{
  "query": "Show me the top 10 users by revenue",
  "expected_tool_use": [{"tool_name": "call_db_agent"}],
  "expected_table": "user_revenue_table",
  "expected_trajectory": [
    "tool_selection: call_db_agent",
    "sql_generation: yes"
  ]
}
```

### Expected Trajectory Elements
- **tool_selection:** Which tool should be used (call_db_agent, call_ds_agent)
- **sql_generation:** Whether SQL should be generated (yes/no)
- **expected_table:** Which table should be accessed

## BigQuery Integration

### Trajectory Evaluations Table
- `evaluation_id`: Primary key
- `session_id`: Links to session
- `test_query`: Original test query
- `expected_tool`: Expected tool selection
- `actual_tool`: Actual tool used
- `expected_table`: Expected table
- `actual_table`: Actual table used
- `sql_generated`: Whether SQL was generated
- `tool_selection_correct`: Tool selection accuracy
- `table_usage_correct`: Table usage accuracy
- `sql_generation_correct`: SQL generation accuracy
- `evaluation_timestamp`: When evaluation ran
- `evaluator_config`: Evaluation configuration

## Error Handling

The evaluation system implements robust error handling:
- **Missing Test Cases:** Graceful handling when no matching test case found
- **Data Access Errors:** Fallback mechanisms for BigQuery access issues
- **Parsing Errors:** Robust parsing with error recovery
- **Session State Errors:** Default values for missing session data

## Performance Considerations

- **Lazy Loading:** Golden dataset loaded only when needed
- **Caching:** Session data cached for repeated access
- **Batch Processing:** Efficient BigQuery operations
- **Memory Management:** Minimal data retention

## Debugging and Monitoring

The evaluation system provides comprehensive debugging:
- Test case matching confirmations
- Trajectory extraction details
- Score calculation breakdowns
- Error details with context
- Performance metrics

This trajectory evaluation system ensures agent behavior meets expected standards and provides quantitative metrics for continuous improvement. 