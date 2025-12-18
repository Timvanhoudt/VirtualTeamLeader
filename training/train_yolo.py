"""
YOLO Training Script voor Werkplek Inspectie
Traint een YOLO classificatie model voor OK/NOK detectie
"""

from ultralytics import YOLO
from pathlib import Path
import torch

# Configuratie
DATA_DIR = Path("../data/processed/yolo_dataset")
MODEL_OUTPUT_DIR = Path("../backend/models")
EPOCHS = 100
BATCH_SIZE = 16
IMAGE_SIZE = 640

def check_gpu():
    """Check of GPU beschikbaar is"""
    if torch.cuda.is_available():
        print(f"✓ GPU beschikbaar: {torch.cuda.get_device_name(0)}")
        return 'cuda'
    else:
        print("⚠ Geen GPU gevonden, training op CPU (langzamer)")
        return 'cpu'

def train_classification_model():
    """Train YOLO classificatie model voor OK/NOK + defect type"""

    print("="*60)
    print("YOLO CLASSIFICATIE MODEL TRAINING")
    print("="*60)

    device = check_gpu()

    # Start met YOLOv8 classificatie model
    print("\n📥 Laden van YOLOv8n-cls model...")
    model = YOLO('yolov8n-cls.pt')  # Nano model (snel, geschikt voor start)

    print(f"\n🎯 Dataset: {DATA_DIR}")
    print(f"📊 Epochs: {EPOCHS}")
    print(f"📦 Batch size: {BATCH_SIZE}")
    print(f"🖼️  Image size: {IMAGE_SIZE}")
    print(f"💻 Device: {device}")

    # Train het model
    print("\n🚀 Start training...\n")

    results = model.train(
        data=str(DATA_DIR),
        epochs=EPOCHS,
        batch=BATCH_SIZE,
        imgsz=IMAGE_SIZE,
        device=device,
        workers=0,  # Fix voor Windows multiprocessing issues
        project='runs/classify',
        name='werkplek_inspect',
        exist_ok=True,
        patience=20,  # Early stopping na 20 epochs zonder verbetering
        save=True,
        plots=True,
        verbose=True,
        # Data Augmentatie voor rotatie-resistentie
        degrees=90.0,      # Rotatie tot 90 graden
        translate=0.1,     # Translatie
        scale=0.5,         # Zoom in/out
        fliplr=0.5,        # Horizontal flip
        flipud=0.5,        # Vertical flip
        hsv_h=0.015,       # Hue variatie
        hsv_s=0.7,         # Saturatie variatie
        hsv_v=0.4          # Brightness variatie
    )

    print("\n✅ Training voltooid!")

    # Evalueer het model
    print("\n📊 Evaluatie op validatie set...")
    metrics = model.val()

    print(f"\n✓ Top-1 Accuracy: {metrics.top1:.2%}")
    print(f"✓ Top-5 Accuracy: {metrics.top5:.2%}")

    # Exporteer het beste model
    best_model_path = Path('runs/classify/werkplek_inspect/weights/best.pt')
    if best_model_path.exists():
        MODEL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = MODEL_OUTPUT_DIR / 'werkplek_classifier.pt'

        import shutil
        shutil.copy2(best_model_path, output_path)

        print(f"\n✓ Beste model opgeslagen: {output_path}")
        print(f"  Model accuraatheid: {metrics.top1:.2%}")

    return model, metrics

def test_model(model_path=None):
    """Test het getrainde model op enkele voorbeelden"""

    if model_path is None:
        model_path = MODEL_OUTPUT_DIR / 'werkplek_classifier.pt'

    if not Path(model_path).exists():
        print(f"⚠ Model niet gevonden: {model_path}")
        return

    print("\n" + "="*60)
    print("MODEL TEST")
    print("="*60)

    model = YOLO(model_path)

    # Test op enkele validatie afbeeldingen
    # Zoek recursief omdat we nu subfolders hebben
    val_dir = Path("../data/processed/yolo_dataset/val")

    if val_dir.exists():
        test_images = list(val_dir.rglob('*.jpg'))[:5]  # Test eerste 5 (recursive search)

        print(f"\n🧪 Test op {len(test_images)} afbeeldingen:\n")

        for img_path in test_images:
            results = model(img_path)

            for result in results:
                top_class = result.probs.top1
                confidence = result.probs.top1conf.item()
                class_name = result.names[top_class]

                print(f"📸 {img_path.name}")
                print(f"   Voorspelling: {class_name}")
                print(f"   Zekerheid: {confidence:.2%}\n")

if __name__ == "__main__":
    # Check of dataset bestaat
    if not DATA_DIR.exists():
        print(f"❌ Dataset folder niet gevonden: {DATA_DIR}")
        print("   Run eerst: python prepare_dataset.py")
        exit(1)

    print("\n🎓 YOLO Training voor Werkplek Inspectie\n")

    # Train het model
    model, metrics = train_classification_model()

    # Test het model
    test_model()

    print("\n" + "="*60)
    print("🎉 TRAINING COMPLEET!")
    print("="*60)
    print("\nVolgende stappen:")
    print("1. Check de training plots in: runs/classify/werkplek_inspect/")
    print("2. Het beste model staat in: backend/models/werkplek_classifier.pt")
    print("3. Start de backend API: cd backend && python main.py")
    print("="*60)
