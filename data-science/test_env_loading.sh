#!/bin/bash

# Test script to verify .env file loading
# This helps debug environment variable issues

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🧪 Testing .env file loading...${NC}"

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo -e "${GREEN}📋 Loading environment variables from .env file...${NC}"
    set -o allexport
    source .env
    set +o allexport
    
    echo -e "${GREEN}✅ Key environment variables loaded:${NC}"
    echo "  GOOGLE_CLOUD_PROJECT: $GOOGLE_CLOUD_PROJECT"
    echo "  GOOGLE_CLOUD_LOCATION: $GOOGLE_CLOUD_LOCATION"
    echo "  ROOT_AGENT_MODEL: $ROOT_AGENT_MODEL"
    echo "  ANALYTICS_AGENT_MODEL: $ANALYTICS_AGENT_MODEL"
    echo "  BQ_DATASET_ID: $BQ_DATASET_ID"
    echo "  BQ_DATA_PROJECT_ID: $BQ_DATA_PROJECT_ID"
    echo "  NL2SQL_METHOD: $NL2SQL_METHOD"
    echo "  GOOGLE_GENAI_USE_VERTEXAI: $GOOGLE_GENAI_USE_VERTEXAI"
    
    # Check if required variables are set
    if [ -z "$GOOGLE_CLOUD_PROJECT" ] || [ -z "$GOOGLE_CLOUD_LOCATION" ]; then
        echo -e "${RED}❌ Missing required environment variables!${NC}"
        exit 1
    else
        echo -e "${GREEN}✅ All required environment variables are set!${NC}"
    fi
else
    echo -e "${RED}❌ .env file not found!${NC}"
    exit 1
fi