"""
Script om het bestaande Colab notebook aan te passen
Leest Werkplek_Inspectie_Training.ipynb en maakt een updated versie
"""

import json
from pathlib import Path

# Lees origineel notebook
notebook_path = Path("Werkplek_Inspectie_Training.ipynb")
output_path = Path("Werkplek_Inspectie_Training_UPDATED.ipynb")

print(f"📖 Reading: {notebook_path}")
with open(notebook_path, 'r', encoding='utf-8') as f:
    notebook = json.load(f)

print(f"✅ Loaded notebook with {len(notebook['cells'])} cells")

# Nieuwe dataset preparation code (ImageFolder format)
new_dataset_prep_code = """# Dataset configuratie
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
]"""

new_dataset_function = """# Prepareer dataset - ImageFolder format
def create_yolo_dataset():
    \\"\\"\\"Converteer naar YOLO ImageFolder format\\"\\"\\"
    
    # Verwijder oude output
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Maak class folders: 0_ok, 1_nok_alles_weg, etc.
    for split in ['train', 'val']:
        for idx, name in enumerate(CLASS_NAMES):
            folder_name = f"{idx}_{name}"
            (OUTPUT_DIR / split / folder_name).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directory structuur (ImageFolder)\\\\n")
    
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
    
    print(f"\\\\n✅ Split: {len(train_images)} train, {len(val_images)} val\\\\n")
    
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
print("🚀 Start preprocessing...\\\\n")
dataset_path = create_yolo_dataset()
print(f"\\\\n✅ Dataset pad: {dataset_path}")"""

# Zoek de juiste cellen en update ze
updated_count = 0

for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source_text = ''.join(cell['source'])
        
        # Update dataset configuratie cel (CLASS_MAPPING)
        if 'CLASS_MAPPING' in source_text and 'Afbeeldingen OK' in source_text:
            print(f"🔧 Updating cell {i}: Dataset configuration")
            cell['source'] = [line + '\n' for line in new_dataset_prep_code.split('\n')]
            updated_count += 1
        
        # Update dataset function cel (create_yolo_dataset)
        elif 'def create_yolo_dataset' in source_text:
            print(f"🔧 Updating cell {i}: Dataset preparation function")
            cell['source'] = [line + '\n' for line in new_dataset_function.split('\n')]
            updated_count += 1
        
        # Update training cel (data parameter)
        elif 'model.train(' in source_text and 'data=' in source_text:
            print(f"🔧 Updating cell {i}: Training call")
            # Vervang data=str(data_yaml_path) met data=str(dataset_path)
            new_source = source_text.replace('data=str(data_yaml_path)', 'data=str(dataset_path)')
            new_source = new_source.replace('data_yaml_path', 'dataset_path')
            cell['source'] = [line + '\n' for line in new_source.split('\n')]
            updated_count += 1

print(f"\n✅ Updated {updated_count} cells")

# Schrijf updated notebook
print(f"💾 Writing: {output_path}")
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=2, ensure_ascii=False)

print(f"\n🎉 SUCCESS!")
print(f"✅ Created: {output_path}")
print(f"\n📋 Next steps:")
print(f"   1. Upload {output_path} to Google Colab")
print(f"   2. Runtime -> GPU (T4)")
print(f"   3. Upload dataset_raw.zip")
print(f"   4. Run all cells")
