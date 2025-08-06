#!/bin/bash

# Cloud Run deployment script for Data Science Agent
# Following the ADK documentation: https://google.github.io/adk-docs/deploy/cloud-run/#gcloud-cli

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Cloud Run deployment for Data Science Agent${NC}"

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo -e "${YELLOW}📋 Loading environment variables from .env file...${NC}"
    # Load .env file, ignoring comments and empty lines, and handling quotes properly
    set -o allexport
    source .env
    set +o allexport
else
    echo -e "${YELLOW}⚠️ No .env file found. Using existing environment variables.${NC}"
fi

# Check if required environment variables are set
check_env_var() {
    if [ -z "${!1}" ]; then
        echo -e "${RED}❌ Error: Environment variable $1 is not set${NC}"
        echo -e "${YELLOW}Please set it using: export $1=your-value${NC}"
        exit 1
    fi
}

echo -e "${YELLOW}📋 Checking required environment variables...${NC}"
check_env_var "GOOGLE_CLOUD_PROJECT"
check_env_var "GOOGLE_CLOUD_LOCATION"

# Optional environment variables with defaults
SERVICE_NAME=${SERVICE_NAME:-"data-science-agent"}
APP_NAME=${APP_NAME:-"data_science"}

echo -e "${GREEN}✅ Environment variables verified:${NC}"
echo "  - PROJECT: $GOOGLE_CLOUD_PROJECT"
echo "  - LOCATION: $GOOGLE_CLOUD_LOCATION"
echo "  - SERVICE_NAME: $SERVICE_NAME"
echo "  - APP_NAME: $APP_NAME"
echo "  - WEB_INTERFACE: Enabled (SERVE_WEB_INTERFACE=True, using ADK FastAPI)"

# Check if gcloud is authenticated
echo -e "${YELLOW}🔐 Checking gcloud authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ No active gcloud authentication found${NC}"
    echo -e "${YELLOW}Please run: gcloud auth login${NC}"
    exit 1
fi

# Set the project
echo -e "${YELLOW}🏗️ Setting gcloud project...${NC}"
gcloud config set project $GOOGLE_CLOUD_PROJECT

# Build and deploy to Cloud Run
echo -e "${YELLOW}🚀 Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $GOOGLE_CLOUD_LOCATION \
    --project $GOOGLE_CLOUD_PROJECT \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,GOOGLE_CLOUD_LOCATION=$GOOGLE_CLOUD_LOCATION,GOOGLE_GENAI_USE_VERTEXAI=$GOOGLE_GENAI_USE_VERTEXAI,ROOT_AGENT_MODEL=$ROOT_AGENT_MODEL,ANALYTICS_AGENT_MODEL=$ANALYTICS_AGENT_MODEL,BASELINE_NL2SQL_MODEL=$BASELINE_NL2SQL_MODEL,BIGQUERY_AGENT_MODEL=$BIGQUERY_AGENT_MODEL,BQML_AGENT_MODEL=$BQML_AGENT_MODEL,CHASE_NL2SQL_MODEL=$CHASE_NL2SQL_MODEL,BQ_DATASET_ID=$BQ_DATASET_ID,BQ_DATA_PROJECT_ID=$BQ_DATA_PROJECT_ID,BQ_COMPUTE_PROJECT_ID=$BQ_COMPUTE_PROJECT_ID,BQML_RAG_CORPUS_NAME=$BQML_RAG_CORPUS_NAME,CODE_INTERPRETER_EXTENSION_NAME=$CODE_INTERPRETER_EXTENSION_NAME,NL2SQL_METHOD=$NL2SQL_METHOD" \
    --service-account 737407662473-compute@developer.gserviceaccount.com \
    --memory 2Gi \
    --cpu 1 \
    --timeout 3600 \
    --max-instances 10

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Deployment successful!${NC}"
    
    # Get the service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$GOOGLE_CLOUD_LOCATION --format="value(status.url)")
    echo -e "${GREEN}🌐 Service URL: $SERVICE_URL${NC}"
    
    echo -e "${YELLOW}📋 Next steps:${NC}"
    echo "1. Test your agent by visiting: $SERVICE_URL"
    echo "2. Use the ADK UI interface for interactive testing"
    echo "3. Use curl commands for API testing (see ADK documentation)"
    
    echo -e "${YELLOW}🔧 Useful commands:${NC}"
    echo "  - View logs: gcloud run logs tail $SERVICE_NAME --region=$GOOGLE_CLOUD_LOCATION"
    echo "  - Update service: re-run this script"
    echo "  - Delete service: gcloud run services delete $SERVICE_NAME --region=$GOOGLE_CLOUD_LOCATION"
else
    echo -e "${RED}❌ Deployment failed!${NC}"
    exit 1
fi