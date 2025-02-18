#!/bin/bash
set -e

# Configuration
APP_NAME="copilot"
BRANCH="main"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check AWS Profile
if [ -z "$AWS_PROFILE" ]; then
    echo -e "${RED}Error: AWS_PROFILE must be set${NC}"
    exit 1
else
    echo -e "${GREEN}Using AWS Profile: $AWS_PROFILE${NC}"
fi

# Check for AWS credentials file
if [ ! -f ~/.aws/credentials ]; then
    echo -e "${RED}Error: AWS credentials not found in ~/.aws/credentials${NC}"
    echo -e "Please ensure you have AWS credentials configured in your home directory"
    exit 1
fi

# Check if the specified profile exists
if ! aws configure list-profiles | grep -q "^${AWS_PROFILE}$"; then
    echo -e "${RED}Error: AWS Profile '$AWS_PROFILE' not found in ~/.aws/credentials${NC}"
    echo -e "Available profiles:"
    aws configure list-profiles
    exit 1
fi

# Get region from AWS profile, defaulting to us-west-2
REGION=$(aws configure get region --profile $AWS_PROFILE)
if [ -z "$REGION" ]; then
    echo -e "${YELLOW}No region found in AWS profile, defaulting to us-west-2${NC}"
    REGION="us-west-2"
fi

# Verify AWS credentials and get account info
echo -e "${YELLOW}Verifying AWS credentials...${NC}"
ACCOUNT_INFO=$(aws sts get-caller-identity --profile $AWS_PROFILE)
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to verify AWS credentials for profile $AWS_PROFILE${NC}"
    exit 1
fi

CURRENT_ACCOUNT_ID=$(echo $ACCOUNT_INFO | jq -r .Account)
CURRENT_USER_ID=$(echo $ACCOUNT_INFO | jq -r .UserId)
CURRENT_USER_ARN=$(echo $ACCOUNT_INFO | jq -r .Arn)

echo -e "${GREEN}Current AWS credentials:${NC}"
echo -e "  Account ID: $CURRENT_ACCOUNT_ID"
echo -e "  User ID: $CURRENT_USER_ID"
echo -e "  User ARN: $CURRENT_USER_ARN"
echo -e "  Region: $REGION"

# Check for amplify.yml
if [ ! -f "amplify.yml" ]; then
    echo -e "${RED}Error: amplify.yml not found. Is this an Amplify project?${NC}"
    exit 1
fi

# Function to check if app exists
check_app_exists() {
    aws amplify list-apps --region $REGION --profile $AWS_PROFILE --query "apps[?name=='$APP_NAME'].appId" --output text
}

# Get app ID
echo -e "${YELLOW}Looking up Amplify app...${NC}"
APP_ID=$(check_app_exists)

if [ -z "$APP_ID" ]; then
    echo -e "${RED}Error: No Amplify app named '$APP_NAME' found in region $REGION${NC}"
    exit 1
fi

echo -e "${YELLOW}Found Amplify app:${NC}"
echo -e "  App Name: $APP_NAME"
echo -e "  App ID: $APP_ID"
echo -e "  Region: $REGION"

# Confirm deletion
echo -e "${RED}WARNING: This will delete the Amplify app '$APP_NAME' ($APP_ID) and all its resources${NC}"
read -p "Are you sure you want to continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Operation cancelled${NC}"
    exit 1
fi

# Delete the app
echo -e "${YELLOW}Deleting Amplify app...${NC}"
if aws amplify delete-app --app-id "$APP_ID" --region "$REGION" --profile $AWS_PROFILE; then
    echo -e "${GREEN}Successfully deleted Amplify app${NC}"
    
    # Remove build spec
    rm -f amplify.yml
    echo -e "${GREEN}Removed build specification file${NC}"
    
    # Remove config file if it exists
    if [ -f ".amplify-config.json" ]; then
        rm -f .amplify-config.json
        echo -e "${GREEN}Removed configuration file${NC}"
    fi
else
    echo -e "${RED}Failed to delete Amplify app${NC}"
    exit 1
fi

echo -e "${GREEN}Undeployment complete!${NC}" 