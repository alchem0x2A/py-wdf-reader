from pathlib import Path
import os

curdir = Path(__file__).parent
imgdir = curdir / "img"
if not imgdir.is_dir():
    os.makedirs(imgdir, exist_ok=True)
