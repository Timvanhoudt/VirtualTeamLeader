"""
Quick setup test script
Controleert of alles correct is geïnstalleerd
"""

import sys
from pathlib import Path

def check_python_version():
    """Check Python version"""
    print("🐍 Python versie check...")
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")

    if version.major >= 3 and version.minor >= 8:
        print("   ✅ Python versie OK (3.8+)")
        return True
    else:
        print("   ❌ Python 3.8+ vereist")
        return False

def check_dependencies():
    """Check required packages"""
    print("\n📦 Dependencies check...")

    required = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'ultralytics': 'YOLO',
        'cv2': 'OpenCV',
        'PIL': 'Pillow',
        'numpy': 'NumPy',
        'torch': 'PyTorch'
    }

    missing = []

    for module, name in required.items():
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} niet gevonden")
            missing.append(name)

    if missing:
        print(f"\n   Installeer ontbrekende packages:")
        print(f"   cd backend && pip install -r requirements.txt")
        return False

    return True

def check_project_structure():
    """Check project folders"""
    print("\n📁 Project structuur check...")

    required_dirs = [
        'backend',
        'backend/models',
        'backend/utils',
        'frontend',
        'frontend/src',
        'data',
        'data/raw',
        'data/processed',
        'training'
    ]

    all_exist = True

    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"   ✅ {dir_path}")
        else:
            print(f"   ❌ {dir_path} niet gevonden")
            all_exist = False

    return all_exist

def check_dataset():
    """Check dataset"""
    print("\n📸 Dataset check...")

    raw_data = Path('data/raw')

    if not raw_data.exists():
        print("   ❌ data/raw folder niet gevonden")
        return False

    image_count = 0
    for ext in ['.jpg', '.jpeg', '.png']:
        image_count += len(list(raw_data.rglob(f'*{ext}')))

    print(f"   📊 Totaal afbeeldingen: {image_count}")

    if image_count > 0:
        print("   ✅ Dataset gevonden")
        return True
    else:
        print("   ⚠️  Geen afbeeldingen gevonden")
        return False

def check_model():
    """Check trained model"""
    print("\n🤖 Model check...")

    model_path = Path('backend/models/werkplek_classifier.pt')

    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024 * 1024)
        print(f"   ✅ Model gevonden ({size_mb:.1f} MB)")
        return True
    else:
        print("   ⚠️  Model nog niet getraind")
        print("   Train eerst: cd training && python train_yolo.py")
        return False

def main():
    """Run all checks"""
    print("="*60)
    print("🔍 WERKPLEK INSPECTIE AI - SETUP CHECK")
    print("="*60)

    checks = [
        ("Python versie", check_python_version),
        ("Dependencies", check_dependencies),
        ("Project structuur", check_project_structure),
        ("Dataset", check_dataset),
        ("Trained model", check_model)
    ]

    results = {}

    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results[name] = False

    # Summary
    print("\n" + "="*60)
    print("📊 SAMENVATTING")
    print("="*60)

    for name, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {name}")

    print("="*60)

    # Next steps
    print("\n📝 VOLGENDE STAPPEN:")
    print("="*60)

    if not results["Dependencies"]:
        print("1. Installeer dependencies:")
        print("   cd backend && pip install -r requirements.txt")

    if results["Dataset"] and not results["Trained model"]:
        print("2. Prepareer dataset:")
        print("   cd training && python prepare_dataset.py")
        print("\n3. Train model:")
        print("   python train_yolo.py")

    if all([results["Dependencies"], results["Trained model"]]):
        print("✅ Alles is klaar!")
        print("\n🚀 Start de applicatie:")
        print("\n   Terminal 1 - Backend:")
        print("   cd backend && python main.py")
        print("\n   Terminal 2 - Frontend:")
        print("   cd frontend && npm install && npm start")
        print("\n   Open: http://localhost:3000")

    print("="*60)

if __name__ == "__main__":
    main()
