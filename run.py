"""Entrypoint script to start the Autonomous AI Document Agent FastAPI server."""

import os
from dotenv import load_dotenv
import uvicorn

load_dotenv()

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() in ("true", "1", "yes")

    print("=" * 70)
    print(f"🚀 Autonomous AI Document Agent Server Started")
    print(f"🏠 Root Endpoint:         http://127.0.0.1:{port}/")
    print(f"📖 Swagger Documentation: http://127.0.0.1:{port}/docs")
    print(f"💓 Health Check:          http://127.0.0.1:{port}/health")
    print(f"🌐 Listening Interface:    http://{host}:{port}")
    print("=" * 70)

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
