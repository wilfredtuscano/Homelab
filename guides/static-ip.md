# Set a Static IP (Ubuntu Server / netplan)

Preferred method: set a DHCP reservation on the router by MAC address, so the router always hands out the same IP. This avoids touching each machine's network config.

## Option A: DHCP Reservation on Router (recommended)

1. Find the MAC address of the machine:
   ```bash
   ip link show
   ```
2. Log in to your router admin UI.
3. Find the DHCP lease table, locate the machine, and create a reservation binding the MAC to the desired IP.

## Option B: Static IP via netplan

Use this if you cannot use router-side reservations.

1. Find your netplan config file:
   ```bash
   ls /etc/netplan/
   ```

2. Edit the file (e.g., `/etc/netplan/00-installer-config.yaml`):
   ```yaml
   network:
     version: 2
     ethernets:
       eth0:                       # replace with your interface name (ip link show)
         dhcp4: no
         addresses:
           - 192.168.1.XXX/24
         routes:
           - to: default
             via: 192.168.1.1
         nameservers:
           addresses:
             - 192.168.1.199       # Pi-hole
             - 1.1.1.1             # fallback
   ```

3. Apply:
   ```bash
   sudo netplan apply
   ```

4. Verify:
   ```bash
   ip addr show eth0
   ping 192.168.1.1
   ```
