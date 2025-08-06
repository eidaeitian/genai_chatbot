# Cloud Run Deployment Guide

This guide shows how to deploy your Data Science Agent to Google Cloud Run using the ADK framework.

## Prerequisites

1. **Google Cloud CLI**: Install and configure gcloud
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Required IAM Permissions**:
   - Cloud Run Admin
   - Cloud Build Editor
   - Artifact Registry Writer
   - Service Account User

## Environment Variables

### Using .env File (Recommended)

**Security-First Approach**: The deployment script reads environment variables from your local `.env` file during deployment and passes them securely to Cloud Run via the `--set-env-vars` flag. The `.env` file itself is **never included** in the Docker container, ensuring sensitive information stays secure.

**How it works:**
1. 📋 Deployment script loads `.env` file locally
2. 🚀 Variables are passed to Cloud Run via `gcloud` command
3. 🔒 Container receives variables as Cloud Run environment variables
4. 🛡️ `.env` file never leaves your local machine
5. ⚡ Uses official ADK FastAPI approach with `get_fast_api_app()` for optimal performance

Your `.env` file should contain:

```bash
# The .env file should contain:
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_PROJECT="your-project-id"
GOOGLE_CLOUD_LOCATION="us-central1"
NL2SQL_METHOD="BASELINE"
BQ_COMPUTE_PROJECT_ID="your-project-id"
BQ_DATA_PROJECT_ID="your-project-id"
BQ_DATASET_ID="ai_agent_dev"
BQML_RAG_CORPUS_NAME="projects/.../ragCorpora/..."
CODE_INTERPRETER_EXTENSION_NAME=""
ROOT_AGENT_MODEL="gemini-2.5-flash"
ANALYTICS_AGENT_MODEL="gemini-2.5-flash"
BIGQUERY_AGENT_MODEL="gemini-2.5-flash"
BASELINE_NL2SQL_MODEL="gemini-2.5-flash"
CHASE_NL2SQL_MODEL="gemini-2.5-flash"
BQML_AGENT_MODEL="gemini-2.5-flash"
```

### Manual Environment Variables (Alternative)

If you prefer to set environment variables manually instead of using the `.env` file:

```bash
# Required
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"  # or your preferred region

# Optional deployment settings
export SERVICE_NAME="data-science-agent"
export APP_NAME="data_science"

# See .env file for complete list of agent configuration variables
```

## Deployment

### Quick Deployment

The deployment script automatically loads environment variables from your `.env` file:

```bash
./deploy_cloudrun.sh
```

**Note:** 
- Make sure your `.env` file contains all the required environment variables before running the deployment script
- The `.env` file stays on your local machine and is never included in the Docker container
- Environment variables are securely passed to Cloud Run during deployment

**Optional:** Test your environment variables are loaded correctly:
```bash
./test_env_loading.sh
```

### Manual Deployment

If you prefer to run the gcloud command manually:

```bash
gcloud run deploy data-science-agent \
    --source . \
    --region $GOOGLE_CLOUD_LOCATION \
    --project $GOOGLE_CLOUD_PROJECT \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,GOOGLE_CLOUD_LOCATION=$GOOGLE_CLOUD_LOCATION,GOOGLE_GENAI_USE_VERTEXAI=True" \
    --memory 2Gi \
    --cpu 1 \
    --timeout 3600 \
    --max-instances 10
```

## Project Structure

The deployment setup includes:

```
data-science/
├── data_science/          # Your agent code
│   ├── __init__.py        # Imports agent module
│   ├── agent.py           # Main agent with root_agent variable
│   └── ...                # Other agent modules
├── main.py                # Cloud Run entrypoint (FastAPI with ADK)
├── requirements.txt       # Python dependencies (includes uvicorn)
├── Dockerfile             # Container configuration
├── .dockerignore          # Files to exclude from Docker build
├── .env                   # Environment variables (NOT in container, used by deploy script)
├── deploy_cloudrun.sh     # Deployment script
├── test_env_loading.sh    # Test script to verify .env loading
└── CLOUD_RUN_DEPLOYMENT.md # This guide
```

## Testing Your Deployment

### UI Testing

The agent is deployed with the web UI enabled by default (`SERVE_WEB_INTERFACE=True` in `main.py`). 

**Key Features of this Deployment:**
- ✅ Uses official ADK FastAPI approach with `get_fast_api_app()`
- ✅ Automatic agent discovery from directory structure
- ✅ Built-in session management with SQLite backend
- ✅ CORS configuration for cross-origin requests
- ✅ Production-ready with uvicorn ASGI server

After deployment, visit the service URL to access the ADK web interface:
- Select your agent from the dropdown
- Type a message to test the agent
- View execution details and responses

### API Testing

Use curl to test the API endpoints:

```bash
# Set your service URL
export APP_URL="https://your-service-url"

# List available apps
curl -X GET $APP_URL/list-apps

# Create a session
curl -X POST $APP_URL/apps/data_science/users/user_123/sessions/session_abc \
    -H "Content-Type: application/json" \
    -d '{"state": {}}'

# Run the agent
curl -X POST $APP_URL/run_sse \
    -H "Content-Type: application/json" \
    -d '{
        "app_name": "data_science",
        "user_id": "user_123",
        "session_id": "session_abc",
        "new_message": {
            "role": "user",
            "parts": [{"text": "What insights can you provide from our data?"}]
        },
        "streaming": false
    }'
```

## Monitoring and Maintenance

### View Logs
```bash
gcloud run logs tail data-science-agent --region=$GOOGLE_CLOUD_LOCATION
```

### Update Service
Re-run the deployment script or gcloud command with your changes.

### Delete Service
```bash
gcloud run services delete data-science-agent --region=$GOOGLE_CLOUD_LOCATION
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Ensure gcloud is authenticated and has proper permissions
2. **Memory Limits**: Increase memory allocation if needed (`--memory 4Gi`)
3. **Timeout Issues**: Increase timeout if processing takes longer (`--timeout 7200`)
4. **Environment Variables**: Check that all required environment variables are set
5. **.env File Issues**: 
   - Run `./test_env_loading.sh` to verify .env file is loaded correctly
   - Ensure no syntax errors in .env file (no unquoted special characters)
   - Check that .env file is in the correct directory (`data-science/.env`)

### Debug Commands

```bash
# Check service status
gcloud run services describe data-science-agent --region=$GOOGLE_CLOUD_LOCATION

# View recent logs
gcloud run logs tail data-science-agent --region=$GOOGLE_CLOUD_LOCATION --limit=50

# Test locally (optional)
docker build -t data-science-agent .
docker run -p 8080:8080 -e GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT data-science-agent
```

## Security Considerations

- The deployment allows unauthenticated access (`--allow-unauthenticated`)
- For production, consider removing this flag and implementing proper authentication
- Environment variables may contain sensitive information - use Secret Manager for production deployments

## Next Steps

1. Configure custom domains if needed
2. Set up monitoring and alerting
3. Implement proper authentication for production use
4. Consider using Cloud Run Jobs for batch processing tasks