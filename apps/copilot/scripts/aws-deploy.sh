#!/bin/bash
set -e

# Configuration
APP_NAME="copilot"
FRAMEWORK="React"
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

# Verify AWS credentials are valid and get account info
echo -e "${YELLOW}Verifying AWS credentials...${NC}"
ACCOUNT_INFO=$(aws sts get-caller-identity --profile $AWS_PROFILE)
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to verify AWS credentials for profile $AWS_PROFILE${NC}"
    exit 1
fi

ACCOUNT_ID=$(echo $ACCOUNT_INFO | jq -r .Account)
USER_ID=$(echo $ACCOUNT_INFO | jq -r .UserId)
USER_ARN=$(echo $ACCOUNT_INFO | jq -r .Arn)

echo -e "${GREEN}Verified AWS credentials:${NC}"
echo -e "  Account ID: $ACCOUNT_ID"
echo -e "  User ID: $USER_ID"
echo -e "  User ARN: $USER_ARN"
echo -e "  Region: $REGION"

# Confirm account
read -p "Is this the correct AWS account? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Operation cancelled${NC}"
    exit 1
fi

# Get Git repository URL
REPO_URL=$(git config --get remote.origin.url)
if [ -z "$REPO_URL" ]; then
    echo -e "${RED}Error: No Git remote URL found. Please set up your Git repository first.${NC}"
    exit 1
fi

# Convert SSH URL to HTTPS if necessary
if [[ $REPO_URL == git@* ]]; then
    REPO_URL=$(echo $REPO_URL | sed 's|git@github.com:|https://github.com/|')
fi

# Function to check if app already exists
check_app_exists() {
    aws amplify list-apps --region $REGION --profile $AWS_PROFILE --query "apps[?name=='$APP_NAME'].appId" --output text
}

# Check if app exists
echo -e "${YELLOW}Checking if Amplify app already exists...${NC}"
APP_ID=$(check_app_exists)

# Create build spec file if it doesn't exist
if [ ! -f "amplify.yml" ]; then
    cat > amplify.yml << EOL
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: dist
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
EOL
fi

if [ -n "$APP_ID" ]; then
    echo -e "${YELLOW}Amplify app '$APP_NAME' already exists with ID: $APP_ID${NC}"
else
    echo -e "${GREEN}Creating new Amplify app...${NC}"

    # Create the Amplify app
    APP_ID=$(aws amplify create-app \
        --name "$APP_NAME" \
        --region "$REGION" \
        --profile $AWS_PROFILE \
        --platform "WEB" \
        --query "app.appId" \
        --output text)

    echo -e "${GREEN}Successfully created Amplify app with ID: $APP_ID${NC}"

    # Create branch
    echo -e "${YELLOW}Creating branch configuration...${NC}"
    aws amplify create-branch \
        --app-id "$APP_ID" \
        --branch-name "$BRANCH" \
        --region "$REGION" \
        --profile $AWS_PROFILE \
        --stage "PRODUCTION"

    echo -e "${GREEN}Branch '$BRANCH' created successfully${NC}"

    # Connect repository
    echo -e "${YELLOW}Connecting Git repository...${NC}"
    aws amplify create-webhook \
        --app-id "$APP_ID" \
        --branch-name "$BRANCH" \
        --region "$REGION" \
        --profile $AWS_PROFILE \
        --description "Automated webhook for $BRANCH branch"

    aws amplify update-app \
        --app-id "$APP_ID" \
        --region "$REGION" \
        --profile $AWS_PROFILE \
        --repository "$REPO_URL" \
        --platform-oauth-token "$(git config --get credential.helper)" \
        --enable-auto-branch

    echo -e "${GREEN}Repository connected successfully${NC}"
fi

# Save app details to a config file
echo -e "${YELLOW}Saving app details to config file...${NC}"
cat > .amplify-config.json << EOL
{
    "appId": "$APP_ID",
    "appName": "$APP_NAME",
    "region": "$REGION",
    "branch": "$BRANCH",
    "accountId": "$ACCOUNT_ID",
    "userId": "$USER_ID",
    "repository": "$REPO_URL",
    "awsProfile": "$AWS_PROFILE"
}
EOL

echo -e "${GREEN}Deployment setup complete!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Go to AWS Amplify Console: https://console.aws.amazon.com/amplify/home?region=$REGION#/$APP_ID"
echo "2. Verify repository connection"
echo "3. Push changes to trigger deployment" 