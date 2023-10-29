#!/bin/bash

# Vars
USER="adminuser"
VM_ADDRESS=""
PRIVATE_KEY="~/.ssh/vm1"
CRON_SCHEDULE="* * * * *"
SCRIPT_PATH=""


# Copy etl/ directory to the VM
scp -i $PRIVATE_KEY -r ../etl/ "$USER@$VM_ADDRESS:/home/$USER"

# Set up commands
ssh -i $PRIVATE_KEY "$USER@$VM_ADDRESS" <<'ENDSSH'
sudo apt update
sudo apt install -y python3 python3-pip
sudo apt-get install -y python3-dev default-libmysqlclient-dev build-essential pkg-config
cd etl/
sudo pip install -r requirements.txt
ENDSSH

# Add Cron when etl script suports update