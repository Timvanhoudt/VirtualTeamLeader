
print("Checking imports...")
try:
    import fastapi
    print("✅ fastapi ok")
except ImportError as e:
    print(f"❌ fastapi failed: {e}")

try:
    import uvicorn
    print("✅ uvicorn ok")
except ImportError as e:
    print(f"❌ uvicorn failed: {e}")

try:
    import numpy
    print("✅ numpy ok")
except ImportError as e:
    print(f"❌ numpy failed: {e}")

try:
    import cv2
    print("✅ cv2 (opencv) ok")
except ImportError as e:
    print(f"❌ cv2 (opencv) failed: {e}")

try:
    import torch
    print("✅ torch ok")
except ImportError as e:
    print(f"❌ torch failed: {e}")

try:
    import ultralytics
    print("✅ ultralytics ok")
except ImportError as e:
    print(f"❌ ultralytics failed: {e}")
