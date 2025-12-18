# 🚀 COLAB NOTEBOOK - Code Updates

## Quick Copy-Paste voor Colab

Gebruik het bestaande `Werkplek_Inspectie_Training.ipynb` en vervang deze 2 cellen:

---

## CEL 1: Dataset Preparation (vervang hele functie)

```python
# Dataset configuratie
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
```

```python
# Prepareer dataset - ImageFolder format
def create_yolo_dataset():
    """Converteer naar YOLO ImageFolder format"""
    
    # Verwijder oude output
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Maak class folders: 0_ok, 1_nok_alles_weg, etc.
    for split in ['train', 'val']:
        for idx, name in enumerate(CLASS_NAMES):
            folder_name = f"{idx}_{name}"
            (OUTPUT_DIR / split / folder_name).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directory structuur (ImageFolder)\n")
    
    # Verzamel images
    all_images = []
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
    
    for folder_name, class_id in CLASS_MAPPING.items():
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
            print(f"⚠️  Folder niet gevonden: {folder_name}")
            continue
        
        images = [f for f in folder_path.glob('*') if f.suffix.lower() in image_extensions]
        print(f"✅ {folder_name}: {len(images)} afbeeldingen (class {class_id})")
        
        for img_path in images:
            all_images.append((img_path, class_id))
    
    # Shuffle en split
    random.seed(42)
    random.shuffle(all_images)
    
    split_idx = int(len(all_images) * TRAIN_SPLIT)
    train_images = all_images[:split_idx]
    val_images = all_images[split_idx:]
    
    print(f"\n✅ Split: {len(train_images)} train, {len(val_images)} val\n")
    
    # Kopieer naar class folders
    for split_name, image_list in [('train', train_images), ('val', val_images)]:
        for idx, (img_path, class_id) in enumerate(image_list):
            class_name = CLASS_NAMES[class_id]
            folder_name = f"{class_id}_{class_name}"
            new_name = f"{split_name}_{idx}_{img_path.name}"
            dst_img = OUTPUT_DIR / split_name / folder_name / new_name
            shutil.copy2(img_path, dst_img)
    
    print("✅ Dataset klaar! (ImageFolder format)")
    return OUTPUT_DIR

# Run
print("🚀 Start preprocessing...\n")
dataset_path = create_yolo_dataset()
print(f"\n✅ Dataset pad: {dataset_path}")
```

---

## CEL 2: Training (wijzig alleen data parameter)

Zoek de training cel en wijzig:

**OUD:**
```python
results = model.train(
    data=str(data_yaml_path),  # ❌ OUDE MANIER
    epochs=EPOCHS,
    ...
)
```

**NIEUW:**
```python
results = model.train(
    data=str(dataset_path),  # ✅ NIEUWE MANIER (ImageFolder)
    epochs=EPOCHS,
    batch=BATCH_SIZE,
    imgsz=IMAGE_SIZE,
    device=0,
    project='runs/classify',
    name='werkplek_inspect',
    exist_ok=True,
    patience=20,
    save=True,
    plots=True,
    verbose=True,
    val=True
)
```

---

## Dat is het!

Upload `dataset_raw.zip`, run alle cellen, en je bent klaar! 🎉
