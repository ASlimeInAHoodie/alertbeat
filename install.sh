#!/bin/bash

## CONFIG
ZIP_URL="https://github.com/ASlimeInAHoodie/alertbeat/raw/refs/heads/main/venv.tar.gz"
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
# Get path to virtualenv
VIRTUALENV=$(which virtualenv)
# All commands ran with user:
sudo -u "$USERNAME" "$VIRTUALENV" "/home/$USERNAME/app"
# Get the app venv
sudo -u "$USERNAME" curl "$ZIP_URL" -o "/home/$USERNAME/venv.tar.gz"
# Unpack
sudo -u "$USERNAME" tar -xzvf "/home/$USERNAME/venv.tar.gz" -C "/home/$USERNAME/app"
# Remove
sudo -u "$USERNAME" rm "/home/$USERNAME/venv.tar.gz"
# In source install requirements
sudo -u "$USERNAME" bash -c "source /home/$USERNAME/app/bin/activate && pip install --requirement /home/$USERNAME/app/requirements.txt"

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
