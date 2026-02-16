#!/usr/bin/env python3
"""Generate VAPID keys and write them to .env file."""
import os
from py_vapid import Vapid

vapid = Vapid()
vapid.generate_keys()

private_key = vapid.private_pem().strip()
public_key = vapid.public_key.strip() if isinstance(vapid.public_key, str) else vapid.public_key

# Try the b64 encoded applicationServerKey format
import base64
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

raw_pub = vapid._private_key.public_key().public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
app_server_key = base64.urlsafe_b64encode(raw_pub).rstrip(b"=").decode()

# Private key in DER urlsafe-b64 format (for pywebpush)
from cryptography.hazmat.primitives.serialization import NoEncryption

raw_priv = vapid._private_key.private_bytes(
    Encoding.DER,
    format=__import__("cryptography.hazmat.primitives.serialization", fromlist=["PrivateFormat"]).PrivateFormat.PKCS8,
    encryption_algorithm=NoEncryption(),
)

# Actually pywebpush wants PEM or the raw number — let's use PEM
priv_pem = vapid._private_key.private_bytes(
    Encoding.PEM,
    format=__import__("cryptography.hazmat.primitives.serialization", fromlist=["PrivateFormat"]).PrivateFormat.PKCS8,
    encryption_algorithm=NoEncryption(),
).decode()

env_path = os.path.join(os.path.dirname(__file__), ".env")

# Read existing or start from example
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        content = f.read()
else:
    example = os.path.join(os.path.dirname(__file__), ".env.example")
    with open(example, "r") as f:
        content = f.read()

# Write .env with keys embedded inline (single-line private key won't work for PEM,
# so we save PEM to a file and reference it, OR use the raw integer approach)
# pywebpush accepts the PEM file content directly — we'll store the path
pem_path = os.path.join(os.path.dirname(__file__), "private_key.pem")
with open(pem_path, "w") as f:
    f.write(priv_pem)

# Update .env
lines = []
found_priv = found_pub = False
for line in content.splitlines():
    if line.startswith("VAPID_PRIVATE_KEY="):
        lines.append(f"VAPID_PRIVATE_KEY={pem_path}")
        found_priv = True
    elif line.startswith("VAPID_PUBLIC_KEY="):
        lines.append(f"VAPID_PUBLIC_KEY={app_server_key}")
        found_pub = True
    else:
        lines.append(line)

if not found_priv:
    lines.append(f"VAPID_PRIVATE_KEY={pem_path}")
if not found_pub:
    lines.append(f"VAPID_PUBLIC_KEY={app_server_key}")

with open(env_path, "w") as f:
    f.write("\n".join(lines) + "\n")

print("VAPID keys generated!")
print(f"  Private key PEM: {pem_path}")
print(f"  Public key (applicationServerKey): {app_server_key}")
print(f"  Written to: {env_path}")
