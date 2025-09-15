#!/usr/bin/env python3
import socket
import os
import sys

def find_free_port(start=5432, end=5500):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    raise RuntimeError('No free port found in range.')

def patch_compose(port):
    compose_path = 'docker-compose.yml'
    with open(compose_path, 'r') as f:
        lines = f.readlines()
    new_lines = []
    for line in lines:
        if '5432:5432' in line:
            new_lines.append(f'      - "{port}:5432"\n')
        else:
            new_lines.append(line)
    with open(compose_path, 'w') as f:
        f.writelines(new_lines)
    print(f"docker-compose.yml updated: DB port {port} -> 5432")

def main():
    port = find_free_port()
    patch_compose(port)
    print(f"You can now run: docker compose up --build\nDB will be available on localhost:{port}")

if __name__ == "__main__":
    main()
