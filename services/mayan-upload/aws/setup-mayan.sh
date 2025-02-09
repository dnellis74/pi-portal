#!/bin/bash
set -e  # Exit on error

# 🔹 Configuration Variables
AWS_REGION="us-west-2"
INSTANCE_TYPE="t3.medium"
AMI_ID="ami-00c257e12d6828491"
KEY_NAME="mayan-key"
SECURITY_GROUP="mayan-sg"
INSTANCE_NAME="mayan-server"
DOMAIN="yourdomain.com"
USE_HTTPS=false

echo "🚀 Setting up AWS resources in $AWS_REGION..."

# Check if instance already exists
EXISTING_INSTANCE_ID=$(aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=$INSTANCE_NAME" "Name=instance-state-name,Values=running,pending" \
    --query "Reservations[0].Instances[0].InstanceId" \
    --region "$AWS_REGION" \
    --output text)

if [[ "$EXISTING_INSTANCE_ID" != "None" && -n "$EXISTING_INSTANCE_ID" ]]; then
    echo "🔍 Found existing Mayan instance: $EXISTING_INSTANCE_ID"
    INSTANCE_ID=$EXISTING_INSTANCE_ID
else
    # 🔹 Step 1: Create SSH Key Pair (If it doesn't exist)
    if ! aws ec2 describe-key-pairs --key-names "$KEY_NAME" --region "$AWS_REGION" >/dev/null 2>&1; then
        echo "🔑 Creating new SSH key pair: $KEY_NAME..."
        aws ec2 create-key-pair \
            --key-name "$KEY_NAME" \
            --query 'KeyMaterial' \
            --output text \
            --region "$AWS_REGION" > "${KEY_NAME}.pem"
        chmod 400 "${KEY_NAME}.pem"
        echo "✅ SSH key pair created and saved to ${KEY_NAME}.pem"
    else
        echo "✅ Using existing SSH key pair: $KEY_NAME"
    fi

    # 🔹 Step 2: Create Security Group (If it doesn't exist)
    SECURITY_GROUP_ID=$(aws ec2 describe-security-groups --group-names "$SECURITY_GROUP" --region "$AWS_REGION" --query "SecurityGroups[0].GroupId" --output text 2>/dev/null || echo "")

    if [[ -z "$SECURITY_GROUP_ID" ]]; then
        echo "🔒 Creating security group: $SECURITY_GROUP..."
        SECURITY_GROUP_ID=$(aws ec2 create-security-group --group-name "$SECURITY_GROUP" --description "Mayan EDMS SG" --region "$AWS_REGION" --query "GroupId" --output text)

        aws ec2 authorize-security-group-ingress --group-id "$SECURITY_GROUP_ID" --protocol tcp --port 22 --cidr 0.0.0.0/0 --region "$AWS_REGION"
        aws ec2 authorize-security-group-ingress --group-id "$SECURITY_GROUP_ID" --protocol tcp --port 80 --cidr 0.0.0.0/0 --region "$AWS_REGION"
        aws ec2 authorize-security-group-ingress --group-id "$SECURITY_GROUP_ID" --protocol tcp --port 443 --cidr 0.0.0.0/0 --region "$AWS_REGION"
    else
        echo "✅ Using existing security group: $SECURITY_GROUP ($SECURITY_GROUP_ID)"
    fi

    # 🔹 Step 3: Create EC2 Instance with Public IP
    echo "🚀 Creating new EC2 instance..."
    INSTANCE_ID=$(aws ec2 run-instances \
        --image-id "$AMI_ID" \
        --instance-type "$INSTANCE_TYPE" \
        --key-name "$KEY_NAME" \
        --security-group-ids "$SECURITY_GROUP_ID" \
        --associate-public-ip-address \
        --region "$AWS_REGION" \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
        --query "Instances[0].InstanceId" \
        --output text)

    echo "⏳ Waiting for EC2 instance ($INSTANCE_ID) to start..."
    aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$AWS_REGION"
fi

# 🔹 Step 4: Get Public IP
INSTANCE_IP=$(aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --query "Reservations[0].Instances[0].PublicIpAddress" \
    --output text)

echo "🌍 EC2 instance is up at: $INSTANCE_IP"
echo "⏳ Waiting for SSH to be ready..."

# Wait for SSH to be ready
MAX_ATTEMPTS=30
ATTEMPT=1
while ! ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 ubuntu@"$INSTANCE_IP" echo "SSH ready" > /dev/null 2>&1; do
    if [ $ATTEMPT -ge $MAX_ATTEMPTS ]; then
        echo "❌ Timeout waiting for SSH to be ready"
        exit 1
    fi
    echo "Attempt $ATTEMPT/$MAX_ATTEMPTS: SSH not ready yet, waiting..."
    sleep 10
    ATTEMPT=$((ATTEMPT + 1))
done

echo "✅ SSH is ready"

# 🔹 Step 5a: Download and Edit Docker Compose File Locally

# Download the file locally
echo "⬇️ Downloading Mayan EDMS Docker Compose file locally..."
curl -O https://gitlab.com/mayan-edms/mayan-edms/-/raw/master/docker/docker-compose.yml
curl https://gitlab.com/mayan-edms/mayan-edms/-/raw/master/docker/.env -O

# Fix the postgres backup date mask issue (escape % characters)
echo "🛠 Modifying docker-compose.yml locally..."
sed -i.bak 's/\$(date/\$\$(date/g' docker-compose.yml
# fix the restart command
sed -i.bak 's/^\([[:space:]]*restart:[[:space:]]*\)no/\1"no"/' docker-compose.yml
# <-- New modification: change default host port from 80 to 8000 -->
sed -i.bak 's/\${MAYAN_FRONTEND_HTTP_PORT:-80}/\${MAYAN_FRONTEND_HTTP_PORT:-8000}/g' docker-compose.yml
# fix the rabbitmq timeout issue
#sed -i.bak 's/^\([[:space:]]*\)RABBITMQ_SERVER_ADDITIONAL_ERL_ARGS:.*$/\1RABBITMQ_SERVER_ADDITIONAL_ERL_ARGS: "--rabbit consumer_timeout 1800000"/' docker-compose.yml


# (Optional) If you also have an override file to copy, repeat the above for it.
# For example:
# curl -O https://example.com/path/to/docker-compose.override.yml
# sed -i.bak '/pg_dump.*$(date/s/%/\\%/g' docker-compose.override.yml

# 🔹 Step 5b: Copy the Modified Files to the EC2 Instance

echo "🚢 Copying docker-compose.yml to remote host..."
ssh -o StrictHostKeyChecking=no -i "${KEY_NAME}.pem" ubuntu@"$INSTANCE_IP" "mkdir -p ~/mayan"
scp -o StrictHostKeyChecking=no -i "${KEY_NAME}.pem" docker-compose.yml ubuntu@"$INSTANCE_IP":~/mayan/docker-compose.yml
scp -o StrictHostKeyChecking=no -i "${KEY_NAME}.pem" .env ubuntu@"$INSTANCE_IP":~/mayan/.env

# If you have a docker-compose.override.yml file, copy it as well:
# scp -o StrictHostKeyChecking=no -i "${KEY_NAME}.pem" docker-compose.override.yml ubuntu@"$INSTANCE_IP":~/mayan/docker-compose.override.yml

# 🔹 Step 6: Install and Setup Mayan EDMS on EC2
ssh -t -o StrictHostKeyChecking=no -i "${KEY_NAME}.pem" ubuntu@"$INSTANCE_IP" <<'EOF'
    set -e
    set -x
    echo "🚀 Updating system and installing dependencies..."
    sudo apt update && sudo apt upgrade -y
    sudo apt install -y docker.io docker-compose nginx certbot python3-certbot-nginx

    echo "🔧 Adding user to Docker group (logout required to take effect)..."
    sudo usermod -aG docker $USER

    echo "📂 Setting up Mayan EDMS directory..."
    mkdir -p ~/mayan && cd ~/mayan

    # The docker-compose.yml file has already been copied over.
    echo "🚢 Running Docker Compose..."
    docker compose up -d

    echo "🌐 Setting up Nginx reverse proxy for Mayan..."
    sudo tee /etc/nginx/sites-available/mayan > /dev/null <<EOT
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOT
    sudo ln -s /etc/nginx/sites-available/mayan /etc/nginx/sites-enabled/
    sudo systemctl restart nginx

    if [ "$USE_HTTPS" = true ]; then
        echo "🔒 Setting up HTTPS with Let's Encrypt..."
        sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m your@email.com
    fi


    echo "🔄 Enabling Mayan to restart on reboot..."
    (crontab -l 2>/dev/null; echo "@reboot cd ~/mayan && docker-compose up -d") | crontab -
    echo "🎉 Mayan EDMS is now running!"
EOF

# 🔹 Step 7: Display Access Information
echo "✅ Mayan EDMS is now running on: http://$INSTANCE_IP"
if [ "$USE_HTTPS" = true ]; then
    echo "🔒 HTTPS enabled at: https://$DOMAIN"
fi
