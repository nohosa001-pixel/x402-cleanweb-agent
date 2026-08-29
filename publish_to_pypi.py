import sys
import os
import glob
import subprocess
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

# Keep only 2.2.1 in dist/
for f in glob.glob("dist/*"):
    if "2.2.1" not in f:
        try:
            os.remove(f)
            print("Removed old version:", f)
        except Exception:
            pass

user = os.getenv("TWINE_USERNAME", "__token__")
pwd = os.getenv("TWINE_PASSWORD")

env = os.environ.copy()
env["PYTHONIOENCODING"] = "utf-8"
env["TWINE_USERNAME"] = user
env["TWINE_PASSWORD"] = pwd

cmd = [
    "python",
    "-m", "twine", "upload",
    "dist/*2.2.1*",
    "--non-interactive",
    "--verbose"
]

print("Publishing v2.2.1 to PyPI...")
res = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8")
print("Return code:", res.returncode)
print("Stdout:", res.stdout)
print("Stderr:", res.stderr)
