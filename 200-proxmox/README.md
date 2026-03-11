# 200 — Proxmox Server

**IP:** 192.168.1.200
**OS:** Proxmox VE

## Role

Hypervisor hosting all VMs.

## VMs

| VM | IP | Role | Folder |
|---|---|---|---|
| TrueNAS Core 13 | 192.168.1.201 | NAS / ZFS storage | [201-truenas/](201-truenas/) |
| Ubuntu - Starr | 192.168.1.202 | *arr apps + VPN downloader | [202-ubuntu-starr/](202-ubuntu-starr/) |
| Ubuntu - Plex | 192.168.1.203 | Plex media server | [203-ubuntu-plex/](203-ubuntu-plex/) |
