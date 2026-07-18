#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

python3 --version
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

mkdir -p logs cache blocklists config
cp config/config.yaml.example config/config.yaml 2>/dev/null || true

# Get the full path to the virtual environment and script
VENV_PYTHON="${ROOT_DIR}/.venv/bin/python"

cat > /etc/systemd/system/dnsserver.service <<EOF
[Unit]
Description=Lightweight DNS Filtering Server
After=network.target

[Service]
WorkingDirectory=${ROOT_DIR}
ExecStart=${VENV_PYTHON} -m dnsserver.main --config ${ROOT_DIR}/config/config.yaml
Restart=on-failure
User=root
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload >/dev/null 2>&1 || true
systemctl enable dnsserver.service >/dev/null 2>&1 || true

echo "Installation complete."
echo "To start the service: systemctl start dnsserver"
