#!/bin/bash

echo "🚀 Starting Flask Server Files API..."

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
python -c "
import time
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

while True:
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'stark_invoice'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres'),
            host=os.getenv('DB_HOST', 'db'),
            port=os.getenv('DB_PORT', '5432')
        )
        conn.close()
        print('✅ Database is ready!')
        break
    except psycopg2.OperationalError:
        print('⏳ Database not ready, retrying in 2 seconds...')
        time.sleep(2)
"

# Initialize database
echo "🔧 Initializing database..."
python setup_docker.py

# Show machine IP addresses
echo "📍 Machine IP Information:"
python -c "
import socket
import subprocess
import os

def get_local_ip():
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return 'Unable to determine'

def get_container_ip():
    try:
        # Get container's IP address
        result = subprocess.run(['hostname', '-i'], capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return 'Unable to determine'

local_ip = get_local_ip()
container_ip = get_container_ip()
port = os.getenv('PORT', '8888')

print(f'🖥️  Host Machine IP: {local_ip}')
print(f'🐳 Container IP: {container_ip}')
print(f'🌐 Access URLs:')
print(f'   • http://localhost:{port}')
print(f'   • http://127.0.0.1:{port}')
if local_ip != 'Unable to determine':
    print(f'   • http://{local_ip}:{port} (from other devices on network)')
print(f'   • Container internal: http://{container_ip}:{port}')
print()
"

# Start the Flask server
echo "🌐 Starting Flask server..."
python server.py 