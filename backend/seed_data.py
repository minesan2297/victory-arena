"""Wrapper cầu nối — gọi vào scripts/seed_data.py."""
import sys
import os

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from seed_data import seed_database

if __name__ == "__main__":
    seed_database()
