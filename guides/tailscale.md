# Tailscale Remote Access

Tailscale is used for secure remote access to the homelab without opening any ports on the router. The Raspberry Pi 5 acts as a **subnet router**, advertising the entire `192.168.1.0/24` LAN to the Tailscale network so all homelab machines are reachable remotely.

## How it works

- Install Tailscale only on RasPi5 (not every machine)
- RasPi5 advertises `192.168.1.0/24` as a subnet route
- Any device in your Tailscale network can reach all `192.168.1.x` hosts
- No ports opened on router/firewall — Tailscale connections are outbound-only
- MagicDNS lets you reach machines by hostname (e.g. `dnspi`, `starr`)

## Setup — RasPi5 (subnet router)

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Enable IPv4 and IPv6 forwarding (required for subnet routing)
echo 'net.ipv4.ip_forward = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
echo 'net.ipv6.conf.all.forwarding = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
sudo sysctl -p /etc/sysctl.d/99-tailscale.conf

# Advertise subnet
sudo tailscale up --advertise-routes=192.168.1.0/24
```

### Fix UDP GRO forwarding (performance)

```bash
# Apply now
sudo ethtool -K eth0 rx-udp-gro-forwarding on rx-gro-list off

# Make persistent across reboots
sudo tee /etc/systemd/system/tailscale-ethtool.service << 'EOF'
[Unit]
Description=Tailscale ethtool fix

[Service]
Type=oneshot
ExecStart=/sbin/ethtool -K eth0 rx-udp-gro-forwarding on rx-gro-list off

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable --now tailscale-ethtool.service
```

## Setup — Tailscale Admin Console

1. Go to [login.tailscale.com](https://login.tailscale.com)
2. **Machines** → RasPi5 → `...` → **Edit route settings** → enable `192.168.1.0/24`
3. **DNS** tab → Add nameserver pointing to RasPi5's Tailscale IP → check **Restrict to domain** → enter `local.wilfredtuscano.com`
   - This routes homelab DNS queries through Pi-hole only when connected to Tailscale

## Setup — Client Devices

**macOS (App Store app):**
Tailscale menu bar icon → **Use Tailscale subnets** (enable)

**Android:**
Tailscale app → Settings → **Use Tailscale subnets** (enable)

**Linux/CLI:**
```bash
tailscale up --accept-routes
```

## Accessing services remotely

Once connected to Tailscale on your client device:

- Reach any homelab machine by LAN IP: `192.168.1.202`, `192.168.1.203`, etc.
- Reach services by subdomain: `https://pihole.local.wilfredtuscano.com` (requires split DNS configured above)
- MagicDNS hostnames also work: `ssh dnspi`, `ping starr`

## Security notes

- Only devices you explicitly approve in the admin console can join your tailnet
- Tailscale ACLs can restrict which devices access which subnets if needed
- Traffic is encrypted end-to-end via WireGuard
- No Cloudflare proxy involved — safe for media streaming
