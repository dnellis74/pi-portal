#!/bin/bash
set -e
set -x
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
#read -p "Is this the correct AWS account? (y/N) " -n 1 -r
#echo
#if [[ ! $REPLY =~ ^[Yy]$ ]]; then
#    echo -e "${YELLOW}Operation cancelled${NC}"
#    exit 1
#fi

# Get Git repository URL and credentials
REPO_URL=$(git config --get remote.origin.url)
if [ -z "$REPO_URL" ]; then
    echo -e "${RED}Error: No Git remote URL found. Please set up your Git repository first.${NC}"
    exit 1
fi

# Convert SSH URL to HTTPS if necessary
if [[ $REPO_URL == git@* ]]; then
    REPO_URL=$(echo $REPO_URL | sed 's|git@github.com:|https://github.com/|')
fi

echo -e "${GREEN}Using repository URL: $REPO_URL${NC}"

# Check for GitHub token (required for AWS Amplify API)
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}Error: GITHUB_TOKEN environment variable not set${NC}"
    echo -e "${YELLOW}Even though you have local Git access, AWS Amplify's API requires a GitHub token${NC}"
    echo -e "${YELLOW}Please create a token with 'repo' and 'admin:repo_hook' permissions at:${NC}"
    echo -e "${YELLOW}https://github.com/settings/tokens${NC}"
    echo -e "Then set it with: export GITHUB_TOKEN=your_token_here"
    exit 1
fi

# Get Git credentials
GIT_USERNAME=$(git config --get user.name)
GIT_EMAIL=$(git config --get user.email)
if [ -z "$GIT_USERNAME" ] || [ -z "$GIT_EMAIL" ]; then
    echo -e "${RED}Error: Git user.name or user.email not configured.${NC}"
    echo -e "Please configure with:"
    echo -e "  git config --global user.name \"Your Name\""
    echo -e "  git config --global user.email \"your.email@example.com\""
    exit 1
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

    # Create the Amplify app with repository
    APP_ID=$(aws amplify create-app \
        --name "$APP_NAME" \
        --region "$REGION" \
        --profile $AWS_PROFILE \
        --platform "WEB" \
        --repository "$REPO_URL" \
        --oauth-token "$GITHUB_TOKEN" \
        --query "app.appId" \
        --output text)

    echo -e "${GREEN}Successfully created Amplify app with ID: $APP_ID${NC}"
    echo -e "${YELLOW}Note: You will need to authorize AWS Amplify in your GitHub account through the AWS Console${NC}"
    echo -e "${YELLOW}Visit: https://console.aws.amazon.com/amplify/home?region=$REGION#/$APP_ID${NC}"
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
echo -e "${YELLOW}Creating initial deployment...${NC}"

# Function to check if branch already exists
check_branch_exists() {
    aws amplify list-branches --app-id "$APP_ID" --region "$REGION" --profile "$AWS_PROFILE" --query "branches[?branchName=='$BRANCH'].branchName" --output text
}

# Check if branch exists
BRANCH_EXISTS=$(check_branch_exists)
if [ -z "$BRANCH_EXISTS" ]; then
    echo -e "${YELLOW}Creating branch '$BRANCH'...${NC}"
    aws amplify create-branch --app-id "$APP_ID" --branch-name "$BRANCH" --region "$REGION" --profile "$AWS_PROFILE"
    echo -e "${GREEN}Branch '$BRANCH' created successfully.${NC}"
else
    echo -e "${YELLOW}Branch '$BRANCH' already exists.${NC}"
fi

# Start the initial deployment
aws amplify start-job \
    --app-id "$APP_ID" \
    --branch-name "$BRANCH" \
    --job-type "RELEASE" \
    --region "$REGION" \
    --profile $AWS_PROFILE

echo -e "${GREEN}Initial deployment started!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Monitor deployment: https://console.aws.amazon.com/amplify/home?region=$REGION#/$APP_ID"
echo "2. After deployment completes, your app will be available at:"
echo "   https://$BRANCH.$APP_ID.amplifyapp.com"
