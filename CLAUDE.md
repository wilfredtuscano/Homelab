# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a public homelab blueprint repository. It is intended to document and version-control homelab infrastructure configuration (e.g., Docker Compose services, configuration files, scripts).

## Conventions

- `.env` files and `data/` / `volumes/` directories are gitignored — never commit secrets or runtime data.
- Keep configurations declarative and reproducible.
