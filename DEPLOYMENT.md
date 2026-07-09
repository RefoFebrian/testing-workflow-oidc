# Odoo Deployment Guide

This guide covers how to deploy your containerized Odoo module to a Linux server (e.g., Ubuntu).

## 1. Prerequisites
### Linux Server (Production)
On your target server, ensure **Docker** and **Docker Compose** are installed:
```bash
# Update and install docker
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
# Start docker
sudo systemctl enable --now docker
# Add user to docker group (optional, avoids sudo)
sudo usermod -aG docker $USER
```
*Log out and log back in for group changes to take effect.*

### Mac OS
1.  **Install Docker Desktop**: Download and install `Docker.dmg` from [Docker for Mac](https://docs.docker.com/desktop/install/mac-install/).
2.  **Verify**: Open Terminal and run:
    ```bash
    docker --version
    docker-compose --version
    ```

### Windows
1.  **Install Docker Desktop**: Download and install from [Docker for Windows](https://docs.docker.com/desktop/install/windows-install/).
2.  **WSL 2**: Ensure "Use WSL 2 based engine" is checked in Settings > General.
3.  **Verify**: Open PowerShell or Command Prompt and run:
    ```bash
    docker --version
    docker-compose --version
    ```

## 2. Transfer Files
You need to move your project files to the server. You can use **Git** (recommended) or **SCP**.

### Option A: Using Git (Recommended)
1.  Push your local code to a private repository (GitHub/GitLab).
2.  Clone it on the server:
    ```bash
    git clone https://github.com/your-repo/tdm_teto.git
    cd tdm_teto
    ```

### Option B: Using SCP
Copy the files directly from your computer:
```bash
scp -r ~/development/odoo/customs-addons/tdm_teto user@your-server-ip:~/
```

## 3. Configure Production Environment

### Create .env
On the server, create the `.env` file with your **Production** database credentials:
```bash
cp .env.template .env
nano .env
```
Fill in the details:
```ini
HOST=your-aurora-db-instance...
USER=odoo
PASSWORD=your-complex-password
PORT=5432
```

### Configure odoo.conf
Edit `odoo.conf` to set a strong Master Password:
```bash
nano odoo.conf
```
```ini
[options]
admin_passwd = YourSuperSecretMasterPassword!
...
```

## 4. Build and Run
Build the container on the server:
```bash
docker-compose up --build -d
```

## 5. Verify Status
Check that the container is running:
```bash
docker-compose ps
docker-compose logs -f web
```

## 6. Access Odoo
Open your browser and navigate to your server's IP:
`http://your-server-ip:8069`

> [!TIP]
> **Production Security**:
> For a real production environment, you should put Odoo behind a generic Reverse Proxy (like Nginx or Traefik) to handle SSL (HTTPS).

## 7. Maintenance & Updates
When you push new changes to the server, choose the correct action based on what changed:

| If you changed... | Action Required | Command |
| :--- | :--- | :--- |
| **Python Code** (`.py`) | Restart Container | `docker-compose restart web` |
| **Views / XML** (`.xml`) | Upgrade Module | Login to Odoo > Apps > Search Module > Click **Upgrade** |
| **Dependencies** (`requirements.txt`) | Rebuild Image | `docker-compose up --build -d` |
| **Config** (`odoo.conf` / `.env`) | Restart Container | `docker-compose restart web` |
