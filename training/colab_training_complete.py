"""
🚀 WERKPLEK INSPECTIE AI - COLAB TRAINING SCRIPT
Complete training pipeline voor Google Colab

INSTRUCTIES:
1. Upload dit bestand naar Colab
2. Runtime -> Change runtime type -> GPU (T4)
3. Run alle cellen (Runtime -> Run all)
4. Download werkplek_classifier.pt aan het eind

OF: Copy-paste deze hele code in 1 cel in een nieuw Colab notebook
"""

# ============================================================================
# CEL 1: Setup & Imports
# ============================================================================

print("=" * 60)
print("🔧 WERKPLEK INSPECTIE AI - TRAINING")
print("=" * 60)

# Check GPU
print("\n📊 GPU Check:")
import subprocess
subprocess.run(["nvidia-smi"])

# Install dependencies
print("\n📦 Installing packages...")
import subprocess
subprocess.run(["pip", "install", "-q", "ultralytics", "opencv-python", "pillow"])

# Imports
import os
import shutil
from pathlib import Path
import random
from ultralytics import YOLO
import torch

print(f"\n✅ PyTorch: {torch.__version__}")
print(f"✅ CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"✅ GPU: {torch.cuda.get_device_name(0)}")

# ============================================================================
# CEL 2: Upload Dataset
# ============================================================================

print("\n" + "=" * 60)
print("📤 DATASET UPLOAD")
print("=" * 60)

# KIES EEN OPTIE:

# OPTIE A: Google Drive (als je dataset al in Drive hebt)
USE_DRIVE = False  # Zet op True als je Drive gebruikt

if USE_DRIVE:
    from google.colab import drive
    drive.mount('/content/drive')
    
    # PAS AAN NAAR JOUW LOCATIE!
    DATASET_SOURCE = '/content/drive/MyDrive/AI afbeeldingen'
    
    print(f"\n📁 Copying from Drive: {DATASET_SOURCE}")
    shutil.copytree(DATASET_SOURCE, '/content/dataset_raw')
    print("✅ Dataset copied from Drive")

else:
    # OPTIE B: ZIP Upload
    from google.colab import files
    import zipfile
    
    print("\n📁 Upload your dataset_raw.zip file:")
    uploaded = files.upload()
    
    for filename in uploaded.keys():
        if filename.endswith('.zip'):
            print(f"\n📦 Extracting {filename}...")
            with zipfile.ZipFile(filename, 'r') as zip_ref:
                zip_ref.extractall('/content')
            print(f"✅ {filename} extracted")
            
            # Check wat er geextract is
            if Path('/content/dataset_raw').exists():
                print("✅ Found /content/dataset_raw")
            elif Path('/content/data/raw').exists():
                print("📁 Renaming /content/data/raw to /content/dataset_raw")
                shutil.move('/content/data/raw', '/content/dataset_raw')

# Verify
print("\n📂 Dataset contents:")
subprocess.run(["ls", "-la", "/content/dataset_raw"])

# ============================================================================
# CEL 3: Dataset Preparation (ImageFolder)
# ============================================================================

print("\n" + "=" * 60)
print("🔧 DATASET PREPARATION")
print("=" * 60)

# Config
RAW_DATA_DIR = Path("/content/dataset_raw")
OUTPUT_DIR = Path("/content/yolo_dataset")
TRAIN_SPLIT = 0.8

# 7 Classes
CLASS_MAPPING = {
    "Afbeeldingen OK": 0,
    "Afbeeldingen NOK alles weg": 1,
    "Afbeeldingen NOK hamer weg": 2,
    "Afbeeldingen NOK schaar weg": 3,
    "Afbeeldingen NOK schaar en sleutel weg": 4,
    "Afbeeldingen NOK sleutel weg": 5,
    "Afbeeldingen NOK alleen sleutel": 6
}

CLASS_NAMES = [
    "ok",
    "nok_alles_weg",
    "nok_hamer_weg",
    "nok_schaar_weg",
    "nok_schaar_sleutel_weg",
    "nok_sleutel_weg",
    "nok_alleen_sleutel"
]

print(f"\n📋 Classes: {len(CLASS_NAMES)}")
for idx, name in enumerate(CLASS_NAMES):
    print(f"   {idx}: {name}")

# Prepare dataset function
def create_yolo_dataset():
    """Convert to YOLO ImageFolder format"""
    
    # Remove old output
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create class folders: 0_ok, 1_nok_alles_weg, etc.
    print("\n🗂️  Creating directory structure...")
    for split in ['train', 'val']:
        for idx, name in enumerate(CLASS_NAMES):
            folder_name = f"{idx}_{name}"
            (OUTPUT_DIR / split / folder_name).mkdir(parents=True, exist_ok=True)
    
    print("✅ ImageFolder structure created\n")
    
    # Collect images
    all_images = []
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
    
    print("📸 Collecting images:")
    for folder_name, class_id in CLASS_MAPPING.items():
        # Try different locations
        possible_paths = [
            RAW_DATA_DIR / folder_name,
            RAW_DATA_DIR / "AI afbeeldingen" / folder_name,
        ]
        
        folder_path = None
        for path in possible_paths:
            if path.exists():
                folder_path = path
                break
        
        if not folder_path:
            print(f"   ⚠️  Not found: {folder_name}")
            continue
        
        images = [f for f in folder_path.glob('*') if f.suffix.lower() in image_extensions]
        print(f"   ✅ {folder_name}: {len(images)} images (class {class_id})")
        
        for img_path in images:
            all_images.append((img_path, class_id))
    
    if not all_images:
        raise ValueError("❌ No images found! Check your dataset structure.")
    
    # Shuffle and split
    random.seed(42)
    random.shuffle(all_images)
    
    split_idx = int(len(all_images) * TRAIN_SPLIT)
    train_images = all_images[:split_idx]
    val_images = all_images[split_idx:]
    
    print(f"\n📊 Dataset split:")
    print(f"   Train: {len(train_images)} images")
    print(f"   Val:   {len(val_images)} images")
    print(f"   Total: {len(all_images)} images\n")
    
    # Copy to class folders
    print("📁 Organizing images into class folders...")
    for split_name, image_list in [('train', train_images), ('val', val_images)]:
        for idx, (img_path, class_id) in enumerate(image_list):
            class_name = CLASS_NAMES[class_id]
            folder_name = f"{class_id}_{class_name}"
            new_name = f"{split_name}_{idx}_{img_path.name}"
            dst_img = OUTPUT_DIR / split_name / folder_name / new_name
            shutil.copy2(img_path, dst_img)
    
    print("✅ Dataset ready! (ImageFolder format)")
    return OUTPUT_DIR

# Run preparation
print("\n🚀 Starting dataset preparation...\n")
dataset_path = create_yolo_dataset()
print(f"\n✅ Dataset path: {dataset_path}")

# Verify
print("\n📂 Verify structure:")
subprocess.run(["ls", "-la", str(OUTPUT_DIR / "train")])

# ============================================================================
# CEL 4: Train YOLO Model
# ============================================================================

print("\n" + "=" * 60)
print("🚀 YOLO TRAINING")
print("=" * 60)

# Training config
EPOCHS = 100
BATCH_SIZE = 16
IMAGE_SIZE = 640
MODEL_SIZE = 'n'  # 'n' (nano), 's' (small), 'm' (medium)

print(f"\n🎯 Configuration:")
print(f"   Epochs:     {EPOCHS}")
print(f"   Batch size: {BATCH_SIZE}")
print(f"   Image size: {IMAGE_SIZE}")
print(f"   Model:      YOLOv8{MODEL_SIZE}-cls")
print(f"   Device:     GPU (0)" if torch.cuda.is_available() else "   Device:     CPU")

# Load model
print(f"\n📥 Loading YOLOv8{MODEL_SIZE}-cls...")
model = YOLO(f'yolov8{MODEL_SIZE}-cls.pt')
print("✅ Model loaded")

# TRAIN!
print("\n" + "=" * 60)
print("🚀 STARTING TRAINING")
print("=" * 60 + "\n")

results = model.train(
    data=str(dataset_path),  # ImageFolder path
    epochs=EPOCHS,
    batch=BATCH_SIZE,
    imgsz=IMAGE_SIZE,
    device=0 if torch.cuda.is_available() else 'cpu',
    project='runs/classify',
    name='werkplek_inspect',
    exist_ok=True,
    patience=20,  # Early stopping
    save=True,
    plots=True,
    verbose=True,
    val=True
)

print("\n" + "=" * 60)
print("✅ TRAINING COMPLETED!")
print("=" * 60)

# ============================================================================
# CEL 5: Evaluation
# ============================================================================

print("\n" + "=" * 60)
print("📊 EVALUATION")
print("=" * 60)

# Metrics
metrics = model.val()
print(f"\n🎯 Results:")
print(f"   Top-1 Accuracy: {metrics.top1:.2%}")
print(f"   Top-5 Accuracy: {metrics.top5:.2%}")

# Show plots
from IPython.display import Image, display

print("\n📈 Training Plots:\n")
results_dir = 'runs/classify/werkplek_inspect'

plots = [
    ('Results', 'results.png'),
    ('Confusion Matrix', 'confusion_matrix.png'),
    ('Val Predictions', 'val_batch0_pred.jpg')
]

for title, filename in plots:
    plot_path = os.path.join(results_dir, filename)
    if os.path.exists(plot_path):
        print(f"\n{title}:")
        display(Image(filename=plot_path, width=800))
    else:
        print(f"⚠️  {filename} not found")

# ============================================================================
# CEL 6: Download Model
# ============================================================================

print("\n" + "=" * 60)
print("⬇️  MODEL DOWNLOAD")
print("=" * 60)

# Copy best model
best_model_path = 'runs/classify/werkplek_inspect/weights/best.pt'
output_model = '/content/werkplek_classifier.pt'

if os.path.exists(best_model_path):
    shutil.copy2(best_model_path, output_model)
    
    size_mb = os.path.getsize(output_model) / (1024 * 1024)
    print(f"\n✅ Model saved: werkplek_classifier.pt")
    print(f"   Size: {size_mb:.1f} MB")
    print(f"   Accuracy: {metrics.top1:.2%}")
    
    # Download
    print("\n📥 Downloading model...")
    from google.colab import files
    files.download(output_model)
    print("✅ Model downloaded!")
    
    print("\n" + "=" * 60)
    print("🎉 ALL DONE!")
    print("=" * 60)
    print("\n📝 Next steps:")
    print("   1. Place werkplek_classifier.pt in: backend/models/")
    print("   2. Test: cd backend && python main.py")
    print("   3. Run frontend: cd frontend && npm start")
    
else:
    print(f"❌ Best model not found at: {best_model_path}")

# Optional: Save to Drive
try:
    drive_output = '/content/drive/MyDrive/werkplek_classifier.pt'
    shutil.copy2(output_model, drive_output)
    print(f"\n✅ Also saved to Drive: {drive_output}")
except:
    print("\n💾 Tip: Mount Drive to auto-backup the model")
