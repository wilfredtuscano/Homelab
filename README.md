# Homelab

Public blueprint for my homelab. Feel free to use this as a reference for your own setup.

## Network Diagram

```
ISP Modem
└── Router (192.168.1.1)
    ├── RasPi 5             192.168.1.199   → DNS, Reverse Proxy, Container Mgmt
    ├── Proxmox Server      192.168.1.200
    │   ├── VM: TrueNAS Core 13   192.168.1.201   → NAS / ZFS Storage
    │   ├── VM: Ubuntu - Starr    192.168.1.202   → *arr apps + VPN downloader
    │   ├── VM: Ubuntu - Plex     192.168.1.203   → Plex Media Server
    │   └── VM: Ubuntu - Cloud    192.168.1.204   → VaultWarden, Nextcloud (planned)
    └── GMKTec Evo-X2       192.168.1.205   → Local AI (Ollama + OpenWebUI)
```

## Machines

| Machine | IP | Role | Folder |
|---|---|---|---|
| Raspberry Pi 5 | 192.168.1.199 | Pi-hole, Traefik, Portainer | [199-raspi5/](199-raspi5/) |
| Proxmox Server | 192.168.1.200 | Hypervisor | [200-proxmox/](200-proxmox/) |
| TrueNAS Core 13 (VM) | 192.168.1.201 | NAS / ZFS | [200-proxmox/201-truenas/](200-proxmox/201-truenas/) |
| Ubuntu - Starr (VM) | 192.168.1.202 | *arr + VPN | [200-proxmox/202-ubuntu-starr/](200-proxmox/202-ubuntu-starr/) |
| Ubuntu - Plex (VM) | 192.168.1.203 | Plex | [200-proxmox/203-ubuntu-plex/](200-proxmox/203-ubuntu-plex/) |
| Ubuntu - Cloud (VM) | 192.168.1.204 | VaultWarden, Nextcloud (planned) | [200-proxmox/204-cloud/](200-proxmox/204-cloud/) |
| GMKTec Evo-X2 | 192.168.1.205 | Ollama / OpenWebUI | [205-gmktek/](205-gmktek/) |

## Remote Access

Remote access is provided via **Tailscale** — no ports opened on the router. The RasPi5 acts as a subnet router, advertising `192.168.1.0/24` to the Tailscale network so all homelab machines are reachable remotely.

See [guides/tailscale.md](guides/tailscale.md) for setup instructions.

## Guides

- [Install Docker](guides/docker-install.md)
- [Set a Static IP (Ubuntu / netplan)](guides/static-ip.md)
- [Mount ZFS Drives](guides/zfs-mount.md)
- [Tailscale Remote Access](guides/tailscale.md)
