"""
Dataset preparation script voor YOLOv8 Object Detection
Converts CVAT export (images + labels) to YOLO folder structure
"""

import shutil
from pathlib import Path
import random
import yaml

# Configuratie
RAW_DATA_DIR = Path("../data/raw")
OUTPUT_DIR = Path("../data/processed/yolo_dataset")
TRAIN_SPLIT = 0.8  # 80% training, 20% validation

# Classes (moet matchen met je CVAT obj.names)
CLASS_NAMES = [
    "schaar",
    "sleutel",
    "whiteboard"
]

def setup_directories():
    """Maak YOLO directory structuur"""
    if OUTPUT_DIR.exists():
        try:
            shutil.rmtree(OUTPUT_DIR)
        except Exception as e:
            print(f"Kon oude directory niet verwijderen: {e}")

    # Create standard YOLO structure
    (OUTPUT_DIR / "train/images").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "train/labels").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "val/images").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "val/labels").mkdir(parents=True, exist_ok=True)
            
    print("✓ Directory structuur aangemaakt (images/labels format)")

def find_image_label_pairs(raw_dir):
    """Zoek recursief naar paren van images en .txt labels"""
    pairs = []
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
    
    # Zoek alle images
    for img_path in raw_dir.rglob('*'):
        if img_path.suffix.lower() in image_extensions:
            # Zoek bijbehorende label file
            # 1. Check zelfde folder
            lbl_path = img_path.with_suffix('.txt')
            
            if not lbl_path.exists():
                # 2. Check als er een 'labels' folder is, of 'obj_train_data' logica (CVAT)
                # Voor nu, we zoeken gewoon recursief naar bestandsnaam
                candidates = list(raw_dir.rglob(img_path.stem + '.txt'))
                if candidates:
                    lbl_path = candidates[0]
            
            if lbl_path.exists():
                pairs.append((img_path, lbl_path))
            else:
                print(f"⚠ Warning: Geen label gevonden voor {img_path.name}")
                
    return pairs

def process_dataset():
    """Verwerk dataset"""
    setup_directories()
    
    print(f"🔍 Zoeken naar data in: {RAW_DATA_DIR.resolve()}")
    pairs = find_image_label_pairs(RAW_DATA_DIR)
    
    print(f"✓ Gevonden correcte paren: {len(pairs)}")
    if not pairs:
        print("❌ Geen data gevonden! Zorg dat images en .txt files in data/raw staan.")
        return

    # Shuffle en split
    random.seed(42)
    random.shuffle(pairs)

    split_idx = int(len(pairs) * TRAIN_SPLIT)
    train_set = pairs[:split_idx]
    val_set = pairs[split_idx:]

    print(f"\n✓ Dataset split: {len(train_set)} train, {len(val_set)} val")

    # Kopieer bestanden
    def copy_files(dataset, split_name):
        for img, lbl in dataset:
            shutil.copy2(img, OUTPUT_DIR / split_name / "images" / img.name)
            shutil.copy2(lbl, OUTPUT_DIR / split_name / "labels" / lbl.name)

    copy_files(train_set, 'train')
    copy_files(val_set, 'val')

    # Create data.yaml
    create_yaml()
    
    print(f"✓ Dataset verwerkt en opgeslagen in: {OUTPUT_DIR}")

def create_yaml():
    """Maak data.yaml voor lokale training"""
    yaml_data = {
        'path': str(OUTPUT_DIR.resolve()),
        'train': 'train/images',
        'val': 'val/images',
        'names': {i: name for i, name in enumerate(CLASS_NAMES)}
    }
    
    with open(OUTPUT_DIR / 'data.yaml', 'w') as f:
        yaml.dump(yaml_data, f)
    
    print("✓ data.yaml aangemaakt")

if __name__ == "__main__":
    print("🚀 Start dataset preprocessing (Object Detection)...\n")
    process_dataset()
    print("\n✅ Klaar! Run nu het training script of upload naar Colab.")
