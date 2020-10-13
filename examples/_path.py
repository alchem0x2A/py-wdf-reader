from pathlib import Path
import os
try:
    import pytest
except ImportError:
    #print("No pytest")
    pass

curdir = Path(__file__).parent
imgdir = curdir / "img"
if not imgdir.is_dir():
    os.makedirs(imgdir, exist_ok=True)
