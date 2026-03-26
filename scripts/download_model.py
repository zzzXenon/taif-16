
from huggingface_hub import snapshot_download
import os

model_id = "BAAI/bge-m3"
print(f"Starting download for: {model_id}")
print("This may take some time given the size (~1-2GB)...")

try:
    # resume_download=True is deprecated in newer versions but handled safely, 
    # usually default behavior handles resuming if files exist.
    local_dir = snapshot_download(repo_id=model_id)
    print(f"\nSUCCESS! Model downloaded to: {local_dir}")
    print("You can now run 'python baseline-rag.py'")
except Exception as e:
    print(f"\nERROR: Download failed.")
    print(e)
