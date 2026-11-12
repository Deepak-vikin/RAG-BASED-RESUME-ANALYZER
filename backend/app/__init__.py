import sys
import os

# Automatically add backend directory and root directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))  # backend/app
backend_dir = os.path.dirname(current_dir)                 # backend
project_root = os.path.dirname(backend_dir)                # project root

for p in [backend_dir, project_root]:
    if p not in sys.path:
        sys.path.insert(0, p)
