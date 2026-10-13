import sys
import os

# Automatically ensure project root is on sys.path for all pytest executions
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
