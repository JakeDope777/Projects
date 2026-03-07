"""
Shared fixtures for business analysis tests.
"""

import sys
import os
import pytest

# Ensure the backend app is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
