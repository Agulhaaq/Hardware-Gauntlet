"""Entry point for python -m hwscan with dynamic patch overlay support."""

import sys
from hwscan.core.update_channel import init_patch_loader

# Dynamically load any active modular hot-patch before importing main modules
init_patch_loader()

from hwscan.cli import main

if __name__ == "__main__":
    main()
