# Agent Logger System Documentation

## Overview
The AgentLogger system provides comprehensive logging capabilities for the Data Science Agent workflow. It captures all agent interactions, user queries, and responses in BigQuery for analysis, evaluation, and debugging.

## Core Components

### 1. AgentLogger Class
**Location:** `data_science/utils/agent_logger.py`

The AgentLogger is the central logging component that handles:
- Session initialization and tracking
- Turn-by-turn interaction logging
- BigQuery integration for persistent storage

#### Key Functions:

**`__init__(project_id: str, dataset_id: str)`**
- Initializes BigQuery client connection
- Sets up project and dataset configuration
- Prepares session tracking variables

**`start_session(session_id: str, user_id: str = "test_user")`**
- Creates new session records in BigQuery
- Initializes session metadata (start time, user ID)
- Returns session ID for tracking

**`log_turn(session_id: str, turn_data: Dict[str, Any])`**
- Logs individual agent interactions to BigQuery
- Captures user input, agent response, timestamps
- Handles errors gracefully with fallback logging

## Integration Points

### 1. Session Initialization
**Location:** `data_science/agent.py:40` - `setup_before_agent_call()`

```python
# Logger integration in session setup
from .utils.agent_logger import AgentLogger
logger = AgentLogger(project_id="dig-coe-genai-0548", dataset_id="ai_agent_dev")
logger.start_session(session_id, user_id="test_user")
```

**What happens:**
- Creates new session when user starts conversation
- Captures original user query using ADK pattern
- Initializes session state with metadata
- Sets up BigQuery logging infrastructure

### 2. Database Agent Logging
**Location:** `data_science/tools.py:29` - `call_db_agent()`

```python
# Logger integration in database tool
from .utils.agent_logger import AgentLogger
logger = AgentLogger(project_id="dig-coe-genai-0548", dataset_id="ai_agent_dev")

turn_data = {
    'turn_id': str(uuid.uuid4()),
    'session_id': session_id,
    'turn_number': turn_counter,
    'user_input': question,
    'agent_response': str(db_agent_output),
    'response_timestamp': datetime.now().isoformat(),
    'success_indicator': True
}

logger.log_turn(session_id, turn_data)
```

**What happens:**
- Logs SQL generation and database queries
- Captures NL2SQL conversion results
- Records database table access patterns
- Tracks SQL accuracy for evaluation

### 3. Data Science Agent Logging
**Location:** `data_science/tools.py:72` - `call_ds_agent()`

```python
# Logger integration in data science tool
from .utils.agent_logger import AgentLogger
logger = AgentLogger(project_id="dig-coe-genai-0548", dataset_id="ai_agent_dev")

turn_data = {
    'turn_id': str(uuid.uuid4()),
    'session_id': session_id,
    'turn_number': turn_counter,
    'user_input': question,
    'agent_response': str(ds_agent_output),
    'response_timestamp': datetime.now().isoformat(),
    'success_indicator': True
}

logger.log_turn(session_id, turn_data)
```

**What happens:**
- Logs Python analysis and insights
- Captures NL2Py conversion results
- Records data analysis patterns
- Tracks analysis accuracy for evaluation

### 4. Root Agent Response Logging
**Location:** `data_science/agent.py:90` - `setup_after_model_call()`

```python
# Logger integration in root agent callback
from .utils.agent_logger import AgentLogger
logger = AgentLogger(project_id="dig-coe-genai-0548", dataset_id="ai_agent_dev")

turn_data = {
    'turn_id': str(uuid.uuid4()),
    'session_id': session_id,
    'turn_number': turn_counter,
    'user_input': 'DIRECT_ROOT_RESPONSE',
    'agent_response': response_text,
    'agent_type': 'root',
    'response_source': 'direct_llm_response',
    'response_timestamp': datetime.now().isoformat()
}

logger.log_turn(session_id, turn_data)
```

**What happens:**
- Logs direct root agent responses
- Captures final user-facing outputs
- Records tool selection decisions
- Triggers trajectory evaluation

## Data Flow

### Session Lifecycle
1. **Session Start:** User query → `setup_before_agent_call()` → Logger initialization
2. **Tool Execution:** Agent decision → Tool call → Logger turn capture
3. **Response Generation:** Tool output → Response formatting → Logger final capture
4. **Evaluation Trigger:** Session completion → Trajectory evaluation → Results logging

### Turn Data Structure
Each logged turn contains:
- `turn_id`: Unique identifier for the interaction
- `session_id`: Links to parent session
- `turn_number`: Sequential order in conversation
- `user_input`: Original user query or tool input
- `agent_response`: Agent's response or tool output
- `agent_type`: Type of agent (root, db_agent, ds_agent)
- `response_source`: Source of response (direct_llm_response, tool_call)
- `response_timestamp`: ISO timestamp of interaction
- `success_indicator`: Boolean success flag
- `error_message`: Error details if applicable

## BigQuery Tables

### Sessions Table
- `session_id`: Primary key
- `user_id`: User identifier
- `start_timestamp`: Session start time
- `end_timestamp`: Session end time (nullable)

### Turns Table
- `turn_id`: Primary key
- `session_id`: Foreign key to sessions
- `turn_number`: Sequential order
- `user_input`: User query text
- `agent_response`: Agent response text
- `agent_type`: Agent type identifier
- `response_source`: Response source identifier
- `response_timestamp`: Interaction timestamp
- `success_indicator`: Success boolean
- `error_message`: Error text (nullable)

## Error Handling

The logger implements robust error handling:
- **BigQuery Connection Errors:** Graceful fallback with error logging
- **Data Validation:** Type checking and format validation
- **Session State Errors:** Fallback to default values
- **Network Timeouts:** Retry logic for transient failures

## Performance Considerations

- **Async Logging:** Non-blocking BigQuery operations
- **Batch Operations:** Efficient bulk data insertion
- **Connection Pooling:** Reuse BigQuery client connections
- **Memory Management:** Minimal state retention

## Monitoring and Debugging

The logger provides comprehensive debugging information:
- Session creation confirmations
- Turn logging confirmations
- Error details with stack traces
- Performance metrics (response times)
- Success/failure indicators

This logging system ensures complete visibility into agent behavior, enabling evaluation, debugging, and continuous improvement of the data science agent workflow. 