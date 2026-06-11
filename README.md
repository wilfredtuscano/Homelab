# Homelab

Public blueprint for my homelab. Feel free to use this as a reference for your own setup.

## Network Diagram

```
ISP Modem
└── Router (192.168.1.1)
    ├── RasPi 5             192.168.1.199   → DNS, Reverse Proxy, Container Mgmt
    ├── Proxmox Server      192.168.1.200
    │   ├── VM:  TrueNAS Core 13   192.168.1.201   → NAS / ZFS Storage
    │   ├── LXC: Starr             192.168.1.202   → *arr apps + VPN downloader
    │   ├── LXC: Plex              192.168.1.203   → Plex (iGPU QuickSync) + Audiobookshelf + Calibre-web
    │   └── LXC: Cloud             192.168.1.204   → VaultWarden + Mealie + Nextcloud (MariaDB + Redis + Collabora)
    └── GMKTec Evo-X2       192.168.1.205   → Local AI (Ollama + OpenWebUI)
```

## Machines

| Machine | IP | Role | Folder |
|---|---|---|---|
| Raspberry Pi 5 | 192.168.1.199 | Pi-hole, Traefik, Portainer | [199-raspi5/](199-raspi5/) |
| Proxmox Server | 192.168.1.200 | Hypervisor | [200-proxmox/](200-proxmox/) |
| TrueNAS Core 13 (VM) | 192.168.1.201 | NAS / ZFS | [200-proxmox/201-truenas/](200-proxmox/201-truenas/) |
| LXC - Starr | 192.168.1.202 | *arr + VPN | [200-proxmox/212-lxc-starr/](200-proxmox/212-lxc-starr/) |
| LXC - Plex | 192.168.1.203 | Plex + Audiobookshelf + Calibre-web | [200-proxmox/213-lxc-plex/](200-proxmox/213-lxc-plex/) |
| LXC - Cloud | 192.168.1.204 | VaultWarden + Mealie + Nextcloud | [200-proxmox/214-lxc-cloud/](200-proxmox/214-lxc-cloud/) |
| GMKTec Evo-X2 | 192.168.1.205 | Ollama / OpenWebUI | [205-gmktek/](205-gmktek/) |

## Remote Access

Remote access is provided via **Tailscale** — no ports opened on the router. The RasPi5 acts as a subnet router, advertising `192.168.1.0/24` to the Tailscale network so all homelab machines are reachable remotely.

See [guides/tailscale.md](guides/tailscale.md) for setup instructions.

## Guides

- [Install Docker](guides/docker-install.md)
- [Set a Static IP (Ubuntu / netplan)](guides/static-ip.md)
- [SSH Setup](guides/ssh.md)
- [Mount ZFS Drives](guides/zfs-mount.md)
- [Portainer Edge Agent Setup](guides/portainer-edge-agent.md)
- [Tailscale Remote Access](guides/tailscale.md)
- [Docker in a Proxmox LXC Container](guides/lxc-docker.md)
- [Add an NVMe ZFS Pool to Proxmox](guides/zfs-nvme-pool.md)
