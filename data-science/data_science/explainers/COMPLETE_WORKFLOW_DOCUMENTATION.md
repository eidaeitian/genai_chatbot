# Complete Data Science Agent Workflow Documentation

## Overview
This document provides a high-level overview of how the Data Science Agent system works from start to finish, showing the complete data flow from user input to final response, including logging and evaluation systems.

## System Architecture

```
User Input → Session Setup → Agent Processing → Tool Execution → Response Generation → Evaluation
     ↓              ↓              ↓              ↓              ↓              ↓
  Query Capture → Logger Init → Tool Selection → Turn Logging → Final Logging → Trajectory Eval
```

## Complete Workflow: Start to Finish

### Phase 1: User Input and Session Initialization
**Trigger:** User sends query to agent
**Location:** `data_science/agent.py:40` - `setup_before_agent_call()`

**What happens:**
1. **User Query Capture:** Uses ADK pattern to capture original user input
2. **Session Creation:** Generates unique session ID and initializes session state
3. **Logger Setup:** Initializes AgentLogger with BigQuery connection
4. **Database Configuration:** Sets up BigQuery schema and agent instructions
5. **Metadata Storage:** Stores session start time, turn counter, and user query

**Key Components:**
- Session ID generation from ADK context
- User query extraction from `callback_context.user_content`
- BigQuery logger initialization
- Database settings configuration

### Phase 2: Agent Processing and Tool Selection
**Trigger:** Root agent receives user query
**Location:** `data_science/agent.py` - Root agent processing

**What happens:**
1. **Query Analysis:** Root agent analyzes user intent
2. **Tool Selection:** Decides which tool to use (call_db_agent, call_ds_agent)
3. **Context Preparation:** Prepares query context for selected tool
4. **Tool Execution:** Calls appropriate sub-agent or tool

**Key Components:**
- Root agent decision making
- Tool selection logic
- Context preparation for sub-agents

### Phase 3: Database Agent Execution (if selected)
**Trigger:** Root agent calls call_db_agent tool
**Location:** `data_science/tools.py:29` - `call_db_agent()`

**What happens:**
1. **NL2SQL Conversion:** Converts natural language to SQL query
2. **Database Query:** Executes SQL against BigQuery tables
3. **Result Processing:** Processes and formats query results
4. **Turn Logging:** Logs database interaction to BigQuery
5. **State Update:** Stores database output in session state

**Key Components:**
- NL2SQL agent execution
- SQL generation and execution
- Result formatting
- Turn logging with AgentLogger

### Phase 4: Data Science Agent Execution (if selected)
**Trigger:** Root agent calls call_ds_agent tool
**Location:** `data_science/tools.py:72` - `call_ds_agent()`

**What happens:**
1. **Data Context:** Uses results from previous database query
2. **NL2Py Conversion:** Converts natural language to Python analysis
3. **Analysis Execution:** Runs Python code for data analysis
4. **Insight Generation:** Creates insights and visualizations
5. **Turn Logging:** Logs analysis interaction to BigQuery
6. **State Update:** Stores analysis output in session state

**Key Components:**
- NL2Py agent execution
- Python code generation and execution
- Data analysis and insights
- Turn logging with AgentLogger

### Phase 5: Response Generation and Final Logging
**Trigger:** Root agent generates final response
**Location:** `data_science/agent.py:90` - `setup_after_model_call()`

**What happens:**
1. **Response Formatting:** Formats final response for user
2. **Direct Response Logging:** Logs root agent response to BigQuery
3. **Evaluation Trigger:** Initiates trajectory evaluation
4. **Session Completion:** Marks session as complete

**Key Components:**
- Final response generation
- Root agent response logging
- Trajectory evaluation trigger
- Session completion handling

### Phase 6: Trajectory Evaluation
**Trigger:** Session completion
**Location:** `data_science/utils/trajectory_evaluator.py:109` - `run_trajectory_evaluation()`

**What happens:**
1. **Golden Dataset Loading:** Loads benchmark test cases
2. **Test Case Matching:** Finds matching test case for user query
3. **Actual Trajectory Extraction:** Analyzes what agent actually did
4. **Expected Trajectory Parsing:** Gets expected behavior from test case
5. **Score Calculation:** Compares actual vs expected behavior
6. **Results Logging:** Stores evaluation results in BigQuery

**Key Components:**
- Golden dataset matching
- Trajectory analysis
- Score calculation
- Evaluation results logging

## Data Flow Through Components

### 1. Logger Integration Points

**Session Start:**
```python
# data_science/agent.py:40
logger = AgentLogger(project_id="dig-coe-genai-0548", dataset_id="ai_agent_dev")
logger.start_session(session_id, user_id="test_user")
```

**Database Tool:**
```python
# data_science/tools.py:29
logger = AgentLogger(project_id="dig-coe-genai-0548", dataset_id="ai_agent_dev")
logger.log_turn(session_id, turn_data)
```

**Data Science Tool:**
```python
# data_science/tools.py:72
logger = AgentLogger(project_id="dig-coe-genai-0548", dataset_id="ai_agent_dev")
logger.log_turn(session_id, turn_data)
```

**Root Agent Response:**
```python
# data_science/agent.py:90
logger = AgentLogger(project_id="dig-coe-genai-0548", dataset_id="ai_agent_dev")
logger.log_turn(session_id, turn_data)
```

### 2. Evaluation Integration Points

**Trajectory Evaluation Trigger:**
```python
# data_science/agent.py:90
from .utils.trajectory_evaluator import run_trajectory_evaluation
evaluation_result = run_trajectory_evaluation(
    session_id=session_id,
    session_state=callback_context.state,
    user_query=user_query
)
```

**SQL Accuracy Evaluation:**
```python
# eval/sql_accuracy_evaluator.py
sql_evaluator = SQLAccuracyEvaluator(config)
extracted_sql = sql_evaluator.extract_sql_from_response(str(db_agent_output))
comparison = sql_evaluator.sql_comparison(extracted_sql, reference_sql)
```

## BigQuery Data Flow

### 1. Sessions Table
- **Created:** Session initialization
- **Updated:** Session completion
- **Purpose:** Session-level metadata and tracking

### 2. Turns Table
- **Created:** Each agent interaction
- **Updated:** Real-time during session
- **Purpose:** Turn-by-turn interaction logging

### 3. Trajectory Evaluations Table
- **Created:** After session completion
- **Updated:** Evaluation results
- **Purpose:** Trajectory evaluation metrics

### 4. SQL Evaluations Table
- **Created:** After SQL generation
- **Updated:** SQL accuracy analysis
- **Purpose:** SQL quality metrics

## Complete Example Flow

### User Query: "Show me the top 10 users by revenue"

**Step 1: Session Setup**
- User query captured: "Show me the top 10 users by revenue"
- Session ID generated: `session_12345`
- Logger initialized with BigQuery connection
- Session record created in BigQuery

**Step 2: Agent Processing**
- Root agent analyzes query intent
- Determines database query is needed
- Selects `call_db_agent` tool

**Step 3: Database Agent Execution**
- NL2SQL converts query to SQL
- SQL executed: `SELECT user_id, revenue FROM users ORDER BY revenue DESC LIMIT 10`
- Results processed and formatted
- Turn logged to BigQuery with SQL generation details

**Step 4: Response Generation**
- Root agent formats final response
- Response: "Here are the top 10 users by revenue: [results]"
- Final turn logged to BigQuery
- Trajectory evaluation triggered

**Step 5: Trajectory Evaluation**
- Golden dataset searched for matching test case
- Test case found with expected trajectory
- Actual trajectory extracted: tool_selection=call_db_agent, sql_generation=true
- Expected trajectory: tool_selection=call_db_agent, sql_generation=true
- Scores calculated: tool_selection_score=1.0, sql_generation_score=1.0
- Results logged to BigQuery

## Key Integration Points

### 1. ADK Framework Integration
- Uses ADK callback patterns for session management
- Leverages ADK state management for session data
- Integrates with ADK tool execution framework

### 2. BigQuery Integration
- Persistent logging of all interactions
- Real-time data access for evaluation
- Scalable storage for large-scale analysis

### 3. Evaluation System Integration
- Automatic evaluation after session completion
- Comprehensive metrics collection
- Continuous improvement feedback loop

## Error Handling and Resilience

### 1. Logger Error Handling
- BigQuery connection failures handled gracefully
- Fallback logging mechanisms
- Session state error recovery

### 2. Evaluation Error Handling
- Missing test cases handled gracefully
- Data access errors with fallback mechanisms
- Parsing errors with robust recovery

### 3. Tool Execution Error Handling
- Tool execution failures logged
- Error messages captured in turn data
- Success indicators for monitoring

## Performance Considerations

### 1. Async Operations
- Non-blocking BigQuery operations
- Efficient tool execution
- Parallel evaluation processing

### 2. Data Management
- Minimal session state retention
- Efficient BigQuery queries
- Optimized evaluation algorithms

### 3. Scalability
- Horizontal scaling with multiple agents
- BigQuery auto-scaling
- Efficient data partitioning

This complete workflow ensures comprehensive logging, evaluation, and monitoring of the data science agent system while maintaining high performance and reliability. 