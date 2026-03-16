# Install Docker (Ubuntu / Debian)

## 1. Remove old versions

```bash
sudo apt remove docker docker-engine docker.io containerd runc
```

## 2. Install dependencies

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release
```

## 3. Add Docker's GPG key and repo

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

## 4. Install Docker Engine

```bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

## 5. Add your user to the docker group

```bash
sudo usermod -aG docker $USER
newgrp docker
```

## 6. Verify

```bash
docker run hello-world
docker compose version
```
