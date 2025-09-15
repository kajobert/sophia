#!/usr/bin/env python3
"""
patch_ports.py
Automaticky najde volné porty pro všechny služby (db, frontend, backend) a upraví docker-compose.yml.
"""
import socket
import re
import sys
from pathlib import Path

# Výchozí porty a rozsahy
PORTS = {
    'db':    {'container': 5432, 'host_start': 5433, 'host_end': 5499},
    'frontend': {'container': 3000, 'host_start': 3000, 'host_end': 3099},
    'backend':  {'container': 8000, 'host_start': 8000, 'host_end': 8099},
}

SERVICE_REGEX = {
    'db': r'(db:\s+[\s\S]*?ports:\s+- ")\d+:5432',
    'frontend': r'(frontend:\s+[\s\S]*?ports:\s+- ")\d+:3000',
    'backend': r'(backend:\s+[\s\S]*?ports:\s+- ")\d+:8000',
}

def find_free_port(start, end):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    raise RuntimeError(f"No free port found in range {start}-{end}")

def patch_compose_ports(compose_path, ports):
    with open(compose_path, 'r') as f:
        content = f.read()
    for service, port in ports.items():
        regex = SERVICE_REGEX[service]
        # Použij funkci pro náhradu, aby se správně předal zachycený group(1)
        def repl(match):
            return f"{match.group(1)}{port}:{PORTS[service]['container']}"
        content = re.sub(regex, repl, content, flags=re.MULTILINE)
    with open(compose_path, 'w') as f:
        f.write(content)
    print("docker-compose.yml updated:")
    for service, port in ports.items():
        print(f"  {service}: {port} -> {PORTS[service]['container']}")
    print("Shrnutí:")
    for service, port in ports.items():
        print(f"  {service} bude dostupný na localhost:{port}")

def main():
    compose_path = Path(__file__).parent.parent / "docker-compose.yml"
    if not compose_path.exists():
        print("docker-compose.yml not found", file=sys.stderr)
        sys.exit(1)
    ports = {}
    for service, cfg in PORTS.items():
        ports[service] = find_free_port(cfg['host_start'], cfg['host_end'])
    patch_compose_ports(str(compose_path), ports)

if __name__ == "__main__":
    main()
