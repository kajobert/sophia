#!/usr/bin/env python3
"""
patch_frontend_port.py
Automaticky najde volný port na hostiteli a upraví docker-compose.yml pro frontend službu.
"""
import socket
import yaml
import re
import sys
from pathlib import Path

def find_free_port(start=3000, end=3999):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    raise RuntimeError("No free port found in range 3000-3999")

def patch_compose_frontend_port(compose_path, new_port):
    with open(compose_path, 'r') as f:
        content = f.read()
    # Najdi řádek s portem pro frontend
    new_content = re.sub(r'(frontend:\s+[\s\S]*?ports:\s+- ")\d+:3000("[\s\S]*?container_name: sophia-frontend)',
                        rf'\1{new_port}:3000\2', content, flags=re.MULTILINE)
    with open(compose_path, 'w') as f:
        f.write(new_content)
    print(f"docker-compose.yml updated: Frontend port -> {new_port}")
    print(f"Frontend bude dostupný na http://localhost:{new_port}")

def main():
    compose_path = Path(__file__).parent.parent / "docker-compose.yml"
    if not compose_path.exists():
        print("docker-compose.yml not found", file=sys.stderr)
        sys.exit(1)
    free_port = find_free_port()
    patch_compose_frontend_port(str(compose_path), free_port)

if __name__ == "__main__":
    main()
