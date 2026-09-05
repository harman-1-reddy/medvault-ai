import sys
import os
import uvicorn

# Ensure backend folder is in python path
backend_dir = os.path.join(os.path.dirname(__file__), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    print("=" * 70)
    print(" [MedVault AI] - Clinical Intelligence & Medical Record Platform")
    print("=" * 70)
    print(" - Backend: FastAPI 2.4.0 Engine")
    print(" - Multimodal Ingestion: PDF & Text Laboratory Parser with Strict Provenance")
    print(" - Safety Engine: Grounded Reference-Range Checker & Cross-Record Reconciler")
    print(" - Web Dashboard URL: http://127.0.0.1:8000")
    print("=" * 70)
    print(" Starting Uvicorn Web Server...")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
