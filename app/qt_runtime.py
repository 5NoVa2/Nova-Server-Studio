"""Refresh Python's module lookup after installing Qt into a new directory."""
import importlib
import os
import sys


def configure_rendering():
    """Use the software renderer proven to work on Nova's target PC."""
    os.environ['QT_QUICK_BACKEND'] = 'software'
    os.environ['QSG_RHI_BACKEND'] = 'software'


def activate_runtime(directory):
    path = str(directory)
    if path not in sys.path:
        sys.path.insert(0, path)
    # A lookup before pip creates this directory caches a missing path finder.
    # Installing files does not clear that cache automatically.
    sys.path_importer_cache.pop(path, None)
    importlib.invalidate_caches()
