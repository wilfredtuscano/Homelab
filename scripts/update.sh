#!/bin/bash
# Update all Docker stacks across all homelab machines.
# Requires SSH key-based auth to be set up on each machine.
# Usage: ./scripts/update.sh

set -e

MACHINES=(
  "dnspi@192.168.1.199"
  "starr@192.168.1.202"
  "plex@192.168.1.203"
  "cloud@192.168.1.204"
  "gmktek@192.168.1.205"
)

UPDATE_CMD='
find ~/docker -name "docker-compose.y*ml" | while read f; do
  dir=$(dirname "$f")
  echo "--> $dir"
  cd "$dir" && docker compose pull && docker compose up -d
  cd ~
done
docker image prune -f
'

for machine in "${MACHINES[@]}"; do
  echo ""
  echo "======================================"
  echo " $machine"
  echo "======================================"
  ssh "$machine" "$UPDATE_CMD"
done

echo ""
echo "All machines updated."
