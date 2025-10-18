#!/bin/bash

## CONFIG
ZIP_URL="https://github.com/ASlimeInAHoodie/alertbeat/blob/main/venv.tar.gz"
USERNAME="alertbeat"

## PRIVILEGES
if [ "$(id -u)" -ne 0 ]
then
    echo "Requires root privileges."
    exit 1
fi
##

## DEPENDENCIES
apt update;
apt install python3-virtualenv -y;
##

## ACCOUNT
if id "$USERNAME" &>/dev/null
then
    echo "User $USERNAME already exists."
    exit 1
fi

# Generate random password hash for new user
password=$(head /dev/urandom | tr -dc 'A-Za-z0-9_@#%&*' | head -c 16)
# Hash password
hashed_password=$(openssl passwd -1 "$password")

# Create
useradd "$USERNAME" --shell /sbin/nologin --create-home --password "$hashed_password"
# Edit group (OPTIONAL BUT NEEDED FOR NGINX)
usermod -aG adm "$USERNAME"


echo "User $USERNAME created."
##

## VIRTUAL ENVIRONMENT
# Become new user
sudo -u "$USERNAME" /bin/bash
# All commands until exit are ran as new user:
# Go to home
cd ~
# Generate virtual environment
virtualenv app
# Enter it
cd app
# Get venv
curl "$ZIP_URL" -o venv.tar.gz
# Unpack
tar -xzvf venv.tar.gz
# Remove
rm venv.tar.gz
# Enter source
source bin/activate
# Install requirements
pip install --requirement requirements.txt
# return to root
exit

## SERVICE
# Create service
cat <<EOF > /etc/systemd/system/alertbeat.service
[Unit]
Description=Run ALERTBEAT with python in a virtual environment

[Service]
Type=simple
User=$USERNAME
ExecStart=/home/$USERNAME/app/bin/python /home/$USERNAME/app/main.py
WorkingDirectory=/home/$USERNAME/app
Restart=always

[Install]
WantedBy=multi-user.target
EOF
# Reload daemon
systemctl daemon-reload
# Enable service
systemctl enable alertbeat.service
# Start service
systemctl start alertbeat.service
# Get status of service
systemctl status alertbeat.service
