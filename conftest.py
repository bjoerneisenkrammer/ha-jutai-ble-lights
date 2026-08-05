"""Pytest configuration and shared fixtures."""

import sys
from pathlib import Path

# Ensure the repo root is on sys.path so custom_components can be imported
repo_root = Path(__file__).parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
