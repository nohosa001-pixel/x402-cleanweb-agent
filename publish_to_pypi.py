import sys
import os
import glob
import shutil
import subprocess
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

# Clean previous build artifacts
for d in ["dist", "build"]:
    if os.path.exists(d):
        shutil.rmtree(d, ignore_errors=True)
        print(f"Cleaned {d}/")

for egg in glob.glob("*.egg-info"):
    shutil.rmtree(egg, ignore_errors=True)
    print(f"Cleaned {egg}")

# 1. Build Package
print("\n[1/3] Building Wheel & Source Distribution for v2.5.0...")
build_res = subprocess.run([sys.executable, "-m", "build"], capture_output=True, text=True, encoding="utf-8")
if build_res.returncode != 0:
    print("[ERROR] Build failed:")
    print(build_res.stderr)
    sys.exit(1)
print(build_res.stdout)

# 2. Check Package with Twine
print("\n[2/3] Checking distribution files with Twine...")
check_res = subprocess.run([sys.executable, "-m", "twine", "check", "dist/*"], capture_output=True, text=True, encoding="utf-8")
print(check_res.stdout)
if check_res.returncode != 0:
    print("[ERROR] Twine check failed:", check_res.stderr)
    sys.exit(1)

# 3. Publish to PyPI
user = os.getenv("TWINE_USERNAME", "__token__")
pwd = os.getenv("TWINE_PASSWORD")

if not pwd:
    print("[ERROR] TWINE_PASSWORD not set in .env")
    sys.exit(1)

env = os.environ.copy()
env["PYTHONIOENCODING"] = "utf-8"
env["TWINE_USERNAME"] = user
env["TWINE_PASSWORD"] = pwd

cmd = [
    sys.executable,
    "-m", "twine", "upload",
    "dist/*",
    "--non-interactive",
    "--verbose"
]

print("\n[3/3] Uploading v2.5.0 to PyPI...")
res = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8")
print("Return code:", res.returncode)
print("Stdout:", res.stdout)
if res.stderr:
    print("Stderr:", res.stderr)

if res.returncode == 0:
    print("\n🎉 [SUCCESS] x402-cleanweb-agent v2.5.0 published to PyPI successfully!")
else:
    print("\n❌ [ERROR] PyPI upload failed.")
    sys.exit(res.returncode)
