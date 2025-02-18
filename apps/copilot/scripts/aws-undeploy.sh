#!/bin/bash
set -e

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

# Check for config file
if [ ! -f ".amplify-config.json" ]; then
    echo -e "${RED}Error: .amplify-config.json not found. Has the app been deployed?${NC}"
    exit 1
fi

# Read configuration
echo -e "${YELLOW}Reading configuration...${NC}"
APP_ID=$(jq -r '.appId' .amplify-config.json)
APP_NAME=$(jq -r '.appName' .amplify-config.json)
REGION=$(jq -r '.region' .amplify-config.json)
SAVED_PROFILE=$(jq -r '.awsProfile' .amplify-config.json)
SAVED_ACCOUNT_ID=$(jq -r '.accountId' .amplify-config.json)
SAVED_USER_ID=$(jq -r '.userId' .amplify-config.json)

if [ -z "$APP_ID" ] || [ "$APP_ID" = "null" ]; then
    echo -e "${RED}Error: Invalid app ID in configuration${NC}"
    exit 1
fi

echo -e "${YELLOW}Deployment was created with:${NC}"
echo -e "  Account ID: $SAVED_ACCOUNT_ID"
echo -e "  User ID: $SAVED_USER_ID"
echo -e "  AWS Profile: $SAVED_PROFILE"

# Warn if using different account or user
if [ "$CURRENT_ACCOUNT_ID" != "$SAVED_ACCOUNT_ID" ]; then
    echo -e "${RED}Warning: Current AWS account ($CURRENT_ACCOUNT_ID) differs from deployment account ($SAVED_ACCOUNT_ID)${NC}"
    read -p "Are you sure you want to continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Operation cancelled${NC}"
        exit 1
    fi
elif [ "$AWS_PROFILE" != "$SAVED_PROFILE" ]; then
    echo -e "${YELLOW}Warning: Current AWS profile ($AWS_PROFILE) differs from deployment profile ($SAVED_PROFILE)${NC}"
    read -p "Do you want to continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Operation cancelled${NC}"
        exit 1
    fi
fi

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
    
    # Remove configuration file
    rm -f .amplify-config.json
    echo -e "${GREEN}Removed configuration file${NC}"
    
    # Remove build spec if it exists
    if [ -f "amplify.yml" ]; then
        rm -f amplify.yml
        echo -e "${GREEN}Removed build specification file${NC}"
    fi
else
    echo -e "${RED}Failed to delete Amplify app${NC}"
    exit 1
fi

echo -e "${GREEN}Undeployment complete!${NC}" 