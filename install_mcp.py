import os
import sys
import json
import shutil
import platform

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def get_claude_config_path() -> str:
    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))
        return os.path.join(appdata, "Claude", "claude_desktop_config.json")
    elif system == "Darwin":
        return os.path.expanduser("~/Library/Application Support/Claude/claude_desktop_config.json")
    else:
        return os.path.expanduser("~/.config/Claude/claude_desktop_config.json")

def get_cursor_config_path() -> str:
    return os.path.expanduser("~/.cursor/mcp.json")

def install_config(config_path: str, client_name: str, server_script_path: str) -> bool:
    try:
        config_dir = os.path.dirname(config_path)
        os.makedirs(config_dir, exist_ok=True)

        config_data = {}
        if os.path.exists(config_path):
            backup_path = config_path + ".bak"
            shutil.copy2(config_path, backup_path)
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except Exception:
                config_data = {}

        if "mcpServers" not in config_data:
            config_data["mcpServers"] = {}

        python_exec = sys.executable

        config_data["mcpServers"]["polygon-x402-cleanweb"] = {
            "command": python_exec,
            "args": [
                "-u",
                os.path.abspath(server_script_path)
            ],
            "env": {
                "PYTHONUNBUFFERED": "1",
                "POLYGON_RPC_URL": "https://polygon-bor-rpc.publicnode.com",
                "SERVER_WALLET_ADDRESS": "0x255F9991233f86B29dB847c8d5b8CB9915e80dCf",
                "USDC_CONTRACT_ADDRESS": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
            }
        }

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        print(f"[SUCCESS] [{client_name}] MCP Server configured successfully!")
        print(f"          Path: {config_path}")
        return True
    except Exception as e:
        print(f"[ERROR] [{client_name}] Error configuring: {e}")
        return False

def main():
    print("=" * 60)
    print("  Polygon x402 AI Data Agent - MCP Auto Installer")
    print("=" * 60)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(current_dir, "mcp_server.py")

    if not os.path.exists(server_script):
        print(f"[ERROR] {server_script} not found!")
        sys.exit(1)

    claude_path = get_claude_config_path()
    cursor_path = get_cursor_config_path()

    print("\n[1/2] Configuring Claude Desktop...")
    install_config(claude_path, "Claude Desktop", server_script)

    print("\n[2/2] Checking Cursor IDE...")
    cursor_dir = os.path.dirname(cursor_path)
    if os.path.exists(cursor_dir):
        install_config(cursor_path, "Cursor", server_script)
    else:
        print(f"      Cursor config directory not found ({cursor_dir}) - skipped.")

    print("\n" + "=" * 60)
    print("  Setup Complete!")
    print("  Please restart Claude Desktop to activate the tools:")
    print("    1. fetch_clean_markdown (Web Scraping)")
    print("    2. fetch_youtube_transcript (YouTube Subtitles)")
    print("    3. fetch_pdf_markdown (PDF Paper Extraction)")
    print("    4. fetch_plain_text (Plain Text Extraction)")
    print("=" * 60)

if __name__ == "__main__":
    main()
