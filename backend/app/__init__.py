import sys
import os

# Ensure backend directory is in sys.path so 'import app' and 'from app.xxx'
# always resolve whether invoked from repository root or backend/ directory.
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
