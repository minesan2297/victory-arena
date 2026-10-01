"""Wrapper cầu nối — gọi vào scripts/seed_demo_bookings.py."""
import sys
import os

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from seed_demo_bookings import seed_demo_bookings

if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    seed_demo_bookings(limit)
