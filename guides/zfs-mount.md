# Mount ZFS / NFS Shares (fstab)

Mount a NFS share exported from TrueNAS on a Linux VM and persist it across reboots.

## Install NFS client

```bash
sudo apt install -y nfs-common
```

## Add to /etc/fstab

```
192.168.1.201:/mnt/<pool>/<dataset>  /mnt/media  nfs  defaults  0  0
```

## Apply without rebooting

```bash
sudo mount -a
```
