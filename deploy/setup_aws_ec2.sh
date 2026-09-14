#!/bin/bash
# Production AWS EC2 Provisioning Script for Financial Research Agent

set -e

echo "=== 1. Updating System Packages ==="
sudo apt-get update -y
sudo apt-get upgrade -y

echo "=== 2. Installing Docker & Docker Compose ==="
sudo apt-get install -y ca-certificates curl gnupg lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Enable Docker without sudo
sudo usermod -aG docker $USER

echo "=== 3. Configuring UFW Firewall ==="
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8501/tcp
sudo ufw allow 8000/tcp
sudo ufw --force enable

echo "=== 4. Setting Up Auto-Restart Systemd Service ==="
cat << 'EOF' | sudo tee /etc/systemd/system/financial-agent.service
[Unit]
Description=Financial Research Agent Docker Stack
Requires=docker.service
After=docker.service

[Service]
Restart=always
WorkingDirectory=/home/ubuntu/Finacialresearchagent
ExecStart=/usr/bin/docker compose up
ExecStop=/usr/bin/docker compose down

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable financial-agent.service

echo "=== AWS EC2 Provisioning Complete! ==="

