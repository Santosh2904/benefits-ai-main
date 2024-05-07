#!/bin/bash

# Check for Ubuntu and install Git
if [ -f /etc/lsb-release ]; then
    echo "Detected Ubuntu system."
    sudo apt update
    sudo apt install git -y
fi

# Check for Amazon Linux and install pip
if [ -f /etc/system-release ]; then
    echo "Detected Amazon Linux system."
    sudo yum install python3-pip -y
fi

# Clone the repository
git clone https://github.com/Santosh2904/benefits-ai-main

# Change directory to the API folder
cd benefits-ai-main/api

# Install requirements from requirements.txt
sudo pip3 install -r requirements.txt

echo "Installation and setup completed, running server"

uvicorn app:app --host 0.0.0.0 --port 8000

