#!/usr/bin/env python
import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

# Test loading .env
env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
print(f"Attempting to load .env from: {env_file}")
print(f".env file exists: {os.path.exists(env_file)}")
print(f".env absolute path: {os.path.abspath(env_file)}\n")

# Load .env
load_dotenv(env_file, verbose=True)

print("\n✅ Loaded environment variables:")
print(f"DB_HOST: {os.getenv('DB_HOST')}")
print(f"DB_USER: {os.getenv('DB_USER')}")
print(f"DB_PASSWORD: {os.getenv('DB_PASSWORD')}")
print(f"DB_NAME: {os.getenv('DB_NAME')}")
print(f"PORT: {os.getenv('PORT')}")
