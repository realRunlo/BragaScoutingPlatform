#!/bin/bash

# Vars
USER=""
VM_ADDRESS=""
PRIVATE_KEY=""

# Set up commands
ssh -i $PRIVATE_KEY "$USER@$VM_ADDRESS" <<'ENDSSH'
sudo apt update
sudo apt-get install -y python3-dev default-libmysqlclient-dev build-essential pkg-config libpq-dev
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install -y python3.10
sudo apt install -y python3.10-distutils
wget https://bootstrap.pypa.io/get-pip.py
sudo python3.10 get-pip.py
cd etl/
sudo pip3.10 install -r requirements.txt
ENDSSH
