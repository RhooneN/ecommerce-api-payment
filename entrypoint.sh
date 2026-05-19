#!/bin/sh

echo "Waiting for Consul..."

export HOST_IP=$(hostname -i)

until python - <<EOF
import urllib.request
try:
    urllib.request.urlopen("http://consul:8500/v1/status/leader")
except:
    raise SystemExit(1)
EOF
do
  sleep 1
done

echo "Registering service in Consul..."

python - <<EOF
import json, urllib.request, os

data = json.dumps({
        "name": "payment",
        "address": "payment",
        "port": 8005,
        "check": {
            "http": f"http://payment:8005/health/",
            "interval": "10s"
    }
}).encode()

req = urllib.request.Request(
    "http://consul:8500/v1/agent/service/register",
    data=data,
    headers={"Content-Type": "application/json"},
    method="PUT"
)

urllib.request.urlopen(req)
EOF

echo "Starting Gunicorn..."

exec gunicorn --bind 0.0.0.0:8005 payment.wsgi:application