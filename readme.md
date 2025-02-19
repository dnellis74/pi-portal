# Policy Intelligence monorepo

* /apps: For user-facing applications.
* /services: For backend services.
* /packages: For shared libraries or utilities


## Copilot App

### Building the Copilot App

1. **Navigate to the project root:**
   ```bash
   cd /path/to/your/project
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Build the app:**
   ```bash
   npm run build:copilot
   ```

   This will compile the TypeScript code and bundle the app using Vite. The output will be in the `apps/copilot/dist` directory.

### Deploying the Copilot App to AWS Amplify

1. **Ensure you have AWS CLI installed and configured:**
   - Install AWS CLI:
     ```bash
     pip install awscli
     ```
   - Configure AWS credentials:
     ```bash
     aws configure
     ```

2. **Set the necessary environment variables:**
   - Set your AWS profile:
     ```bash
     export AWS_PROFILE=your-profile-name
     ```
   - Set your GitHub token:
     ```bash
     export GITHUB_TOKEN=your-github-token
     ```

3. **Run the deployment script:**
   ```bash
   ./infrastructure/scripts/aws-deploy.sh
   ```

   This script will create an Amplify app if it doesn't exist, connect it to your GitHub repository, and start the initial deployment.

4. **Monitor the deployment:**
   - Visit the AWS Amplify Console to monitor the deployment progress and authorize AWS Amplify in your GitHub account if needed.

5. **Access your deployed app:**
   - Once the deployment is complete, your app will be available at the URL provided by AWS Amplify. 