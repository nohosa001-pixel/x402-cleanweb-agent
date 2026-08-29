"""
CleanWeb Studio (x402-cleanweb-agent) Entrypoint.
Exposes the modular FastAPI application from app.main.
"""

import uvicorn
from app.main import app

def main():
    """Runs the FastAPI server locally."""
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)

if __name__ == "__main__":
    main()
