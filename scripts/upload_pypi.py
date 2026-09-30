import os
import sys
import glob
from dotenv import load_dotenv

# Ensure UTF-8 console output on Windows
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

load_dotenv(override=True)

# Set twine credentials from .env
os.environ["TWINE_USERNAME"] = os.getenv("TWINE_USERNAME", "__token__")
os.environ["TWINE_PASSWORD"] = os.getenv("TWINE_PASSWORD", "")

dist_files = sorted(glob.glob("dist/*"))
print(f"📦 Files to upload: {dist_files}")

if not dist_files:
    print("❌ No files found in dist/")
    sys.exit(1)

import twine.commands.upload

args = ["--disable-progress-bar"] + dist_files
print("🚀 Launching twine upload...")
twine.commands.upload.main(args)
print("✅ Upload completed successfully!")
