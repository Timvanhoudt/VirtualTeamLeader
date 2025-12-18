"""
Dataset preparation script voor YOLO training
Converteert de folder structuur naar YOLO format
"""

import os
import shutil
from pathlib import Path
import random
from PIL import Image

# Configuratie
RAW_DATA_DIR = Path("../data/raw")
OUTPUT_DIR = Path("../data/processed/yolo_dataset")
TRAIN_SPLIT = 0.8  # 80% training, 20% validation

# Class mapping
CLASS_MAPPING = {
    "Afbeeldingen OK": 0,
    "Afbeeldingen NOK alles weg": 1,
    "Afbeeldingen NOK hamer weg": 2,
    "Afbeeldingen NOK schaar weg": 3,
    "Afbeeldingen NOK schaar en sleutel weg": 4,
    "Afbeeldingen NOK sleutel weg": 5,
    "Afbeeldingen NOK alleen sleutel": 6  # NIEUW - voor betere sleutel detectie
}

CLASS_NAMES = [
    "ok",
    "nok_alles_weg",
    "nok_hamer_weg",
    "nok_schaar_weg",
    "nok_schaar_sleutel_weg",
    "nok_sleutel_weg",
    "nok_alleen_sleutel"  # NIEUW
]

def create_directory_structure():
    """Maak YOLO directory structuur voor classificatie"""
    # Verwijder oude output als die bestaat om conflicten te voorkomen
    if OUTPUT_DIR.exists():
        try:
            shutil.rmtree(OUTPUT_DIR)
        except Exception as e:
            print(f"Kon oude directory niet verwijderen: {e}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    for split in ['train', 'val']:
        # Maak class folders aan
        for idx, name in enumerate(CLASS_NAMES):
            # Gebruik prefix om volgorde te garanderen: 0_ok, 1_nok_alles_weg, etc.
            folder_name = f"{idx}_{name}"
            (OUTPUT_DIR / split / folder_name).mkdir(parents=True, exist_ok=True)
            
    print("✓ Directory structuur aangemaakt (ImageFolder format)")

def get_image_files(folder_path):
    """Haal alle afbeeldingen op uit een folder"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
    files = []
    for file in folder_path.glob('*'):
        if file.suffix.lower() in image_extensions:
            files.append(file)
    return files

def process_dataset():
    """Verwerk de dataset en split in train/val"""

    create_directory_structure()

    all_images = []

    # Verzamel alle afbeeldingen met hun class labels
    for folder_name, class_id in CLASS_MAPPING.items():
        folder_path = RAW_DATA_DIR / folder_name

        if not folder_path.exists():
            print(f"⚠ Folder niet gevonden: {folder_name}")
            continue

        images = get_image_files(folder_path)
        print(f"✓ {folder_name}: {len(images)} afbeeldingen (class {class_id})")

        for img_path in images:
            all_images.append((img_path, class_id))

    # Shuffle en split
    random.seed(42)
    random.shuffle(all_images)

    split_idx = int(len(all_images) * TRAIN_SPLIT)
    train_images = all_images[:split_idx]
    val_images = all_images[split_idx:]

    print(f"\n✓ Dataset split: {len(train_images)} train, {len(val_images)} val")

    # Kopieer images naar de juiste class folders
    for split_name, image_list in [('train', train_images), ('val', val_images)]:
        for idx, (img_path, class_id) in enumerate(image_list):
            
            # Bepaal doel folder naam
            class_name = CLASS_NAMES[class_id]
            folder_name = f"{class_id}_{class_name}"
            
            # Nieuwe unieke bestandsnaam
            new_name = f"{split_name}_{idx}_{img_path.name}"
            
            # Kopieer
            dst_img = OUTPUT_DIR / split_name / folder_name / new_name
            shutil.copy2(img_path, dst_img)

    print(f"✓ Dataset verwerkt en opgeslagen in: {OUTPUT_DIR}")

def create_data_yaml():
    """Niet strikt nodig voor standaard classification, maar handig voor info"""
    pass

def print_summary():
    """Print dataset statistieken"""
    print("\n" + "="*50)
    print("DATASET SAMENVATTING")
    print("="*50)

    for split in ['train', 'val']:
        img_dir = OUTPUT_DIR / split / 'images'
        if img_dir.exists():
            count = len(list(img_dir.glob('*')))
            print(f"{split.upper()}: {count} afbeeldingen")

    print("\nCLASSES:")
    for idx, name in enumerate(CLASS_NAMES):
        print(f"  {idx}: {name}")
    print("="*50)

if __name__ == "__main__":
    print("🚀 Start dataset preprocessing...\n")
    process_dataset()
    print_summary()
    print("\n✅ Klaar! Dataset is klaar voor YOLO training.")
