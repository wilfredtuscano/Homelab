# SSH Setup

## Enable SSH server on Ubuntu

```bash
sudo apt update && sudo apt install -y openssh-server
sudo systemctl enable --now ssh
```

Verify it's running:
```bash
sudo systemctl status ssh
```

## Generate an SSH key on Mac (one-time)

If you don't already have a key:
```bash
ssh-keygen -t ed25519 -C "your@email.com"
```

Press Enter to accept the default path (`~/.ssh/id_ed25519`). Set a passphrase when prompted.

Your public key is at `~/.ssh/id_ed25519.pub`.

## Copy your public key to a VM

```bash
ssh-copy-id user@192.168.1.x
```

After this, SSH login will use your key instead of a password.

## Recommended: disable password authentication

Once your key is copied to all VMs, disable password login on each:

```bash
sudo nano /etc/ssh/sshd_config
```

Set:
```
PasswordAuthentication no
```

Then restart SSH:
```bash
sudo systemctl restart ssh
```

> Only do this after confirming key-based login works, or you may lock yourself out.
