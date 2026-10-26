# Scoped access for automation agents

How automated operators get exactly the privileges they need on a host, and no more.

Applies to any non-human identity that logs in over SSH to run maintenance — a scheduled job,
a script on a workstation, or an AI coding agent driving the lab.

## The problem with the obvious approaches

**`NOPASSWD: ALL`.** Turns every automation bug into a root incident. If the agent is ever
confused, wrong, or steered by input it cannot authenticate, the blast radius is the whole host.

**Docker group membership.** Frequently proposed as "scoped" access. It is not. The Docker socket
is root-equivalent:

```bash
docker run -v /:/host alpine chroot /host   # root shell, no sudo involved
```

Any identity in the `docker` group is root on that host with an extra step. A model that treats
the docker group as a limited privilege is decorative.

**A sudo rule with a wildcard.** `NOPASSWD: /usr/bin/apt-get *` looks narrow and is not, because
several common binaries execute arbitrary commands when handed the right flags:

```bash
sudo apt-get -o APT::Update::Pre-Invoke::=/bin/sh update    # root shell
```

Anywhere the agent controls the argument vector, assume it controls the outcome.

## The pattern: pin the routine, not the tool

Maintenance work is nearly always a **fixed routine**, not open-ended tool use. So grant the
routine.

1. Write the routine as a script owned `root:root`, mode `0755`, in `/usr/local/sbin/`.
   The agent's own account must not be able to modify it.
2. The script takes **no arguments**, or only arguments validated against a strict allowlist.
3. Grant sudo on that script alone, with the argument vector fully pinned.

```
Cmnd_Alias STACK_UPDATE = /usr/local/sbin/stack-update
homelab-ops ALL=(root) NOPASSWD: STACK_UPDATE
```

The agent can now perform the whole routine — including operations that are individually
root-equivalent, like `docker compose up -d` — while being unable to do anything else with them.

The property that matters:

> **Widening what the agent can do requires a human to edit a root-owned file.** The agent cannot
> grant itself more, regardless of what it is asked to do or what ends up in its context.

The cost is rigidity: novel situations fall outside the script. That is the intended trade. Novel
work is supervised work — a human runs it, or extends the script deliberately.

## Keep the scripts in version control

Store each host's scripts in this repo under `<host>/scripts/` and deploy from there rather than
hand-editing files on each machine. One reviewable place shows what every agent on every host is
permitted to do, and changes to agent authority show up in diffs.

Deploy via a staging directory the agent owns, so "install a file into a privileged location"
stays a reviewed operation:

```bash
rsync <host>/scripts/stack-update <host>:/srv/staging/
ssh <host> 'sudo install -o root -g root -m 0755 /srv/staging/stack-update /usr/local/sbin/'
```

## What does not need sudo

Read-only operations usually have a non-root path. Prefer it — an unprivileged capability cannot
be abused into a privileged one.

| Need | Do NOT grant | Use instead |
|---|---|---|
| Service state | `sudo systemctl status` | `systemctl status` works unprivileged |
| Service logs | `sudo journalctl` | membership of `systemd-journal` |
| Container logs | docker group | a socket proxy exposing read-only endpoints |
| Disk / process stats | `sudo df`, `sudo ps` | already world-readable |

## Account setup

```bash
# System account: no password, key-only, dedicated uid outside the human range
sudo useradd --create-home --shell /bin/bash --uid 3101 --user-group homelab-ops
sudo passwd --lock homelab-ops
sudo usermod --append --groups systemd-journal homelab-ops

# Its own key — never reuse a human's
sudo install -d -o homelab-ops -g homelab-ops -m 0700 /home/homelab-ops/.ssh
```

Restrict the key to the network it should ever arrive from, in `authorized_keys`:

```
from="192.168.1.0/24",no-agent-forwarding,no-port-forwarding,no-X11-forwarding ssh-ed25519 AAAA... homelab-ops
```

Use the **same uid on every host** the identity exists on. Numeric ids are what NFS compares;
a mismatch produces permission failures that are tedious to diagnose.

## Validate before installing

A malformed sudoers file can lock out sudo entirely. Always check first:

```bash
sudo visudo -cf /path/to/staged-file      # must print "parsed OK"
sudo install -o root -g root -m 0440 /path/to/staged-file /etc/sudoers.d/homelab-ops
```

Keep a root shell open in a second terminal until you have confirmed the new file works.

## Verify the boundary, not just the capability

Testing that the agent *can* do its job is half the check. Also confirm it **cannot** exceed it:

```bash
sudo -n /usr/local/sbin/stack-update     # expected: runs
sudo -n /bin/bash                        # expected: refused
sudo -n apt-get install anything         # expected: refused
sudo -n systemctl restart docker         # expected: refused
sudo -l                                  # review the full effective grant
```

A rule that grants more than intended usually looks correct until enumerated with `sudo -l`.
