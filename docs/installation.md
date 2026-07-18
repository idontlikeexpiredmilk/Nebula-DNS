# Installation Guide

## Requirements

- Python 3.12+
- Linux environment (tested on Raspberry Pi OS)

## Install

```bash
chmod +x install.sh
./install.sh
```

## Manual Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m dnsserver.main
```
