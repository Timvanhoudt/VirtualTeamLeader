# 📦 Colab Training - Quick Start

Het huidige model werkt niet goed genoeg, dus we gaan opnieuw trainen in Google Colab met de nieuwe data.

## 🎯 Wat Je Nodig Hebt

1. **Dataset folder met nieuwe data** (`data/raw/`)
2. **Google account** voor Colab
3. **30 minuten tijd**

## 📝 Stappen

### 1. Dataset Voorbereiden (LOKAAL)

De dataset is al voorbereid met het `prepare_dataset.py` script:

**✅ Dataset klaar:** `data/processed/yolo_dataset/`
- Train: 168 images
- Val: 42 images  
- **7 classes defined** (class 6 "alleen sleutel" has no data yet)
  - Class 0: OK
  - Class 1: NOK - Alles weg
  - Class 2: NOK - Hamer weg
  - Class 3: NOK - Schaar weg
  - Class 4: NOK - Schaar en sleutel weg
  - Class 5: NOK - Sleutel weg
  - Class 6: NOK - Alleen sleutel (⚠️ **geen training data**)
- **ImageFolder format** (class subfolders)

### 2. Dataset Upload naar Colab

**Optie A: ZIP Upload (Aanbevolen)**

```bash
# Ga naar de project folder
cd c:\Users\Admin\VisualCode\Projects\School\RefresCO

# Zip de RAW dataset (niet processed!)
# Rechtermuisknop op data/raw folder → Send to → Compressed folder
# Geeft: data_raw.zip (~50 MB)
```

**Optie B: Google Drive**
- Upload `data/raw/` folder naar Google Drive
- Kost meer tijd maar betrouwbaarder voor grote datasets

### 3. Colab Notebook

Open: `training/Werkplek_Inspectie_Training.ipynb` in Google Colab

**⚠️ BELANGRIJK AANPASSING:**

Het notebook gebruikt het oude format. Update de dataset preparation cel:

```python
# AANGEPAST: ImageFolder format (nieuwe versie)
def create_yolo_dataset():
    """Converteer dataset naar YOLO ImageFolder format"""
    
    # Verwijder oude output
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Maak class folders (0_ok, 1_nok_alles_weg, etc.)
    for split in ['train', 'val']:
        for idx, name in enumerate(CLASS_NAMES):
            folder_name = f"{idx}_{name}"
            (OUTPUT_DIR / split / folder_name).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directory structuur aangemaakt (ImageFolder format)\n")
    
    # ... rest van de verzamel code blijft hetzelfde ...
    
    # Kopieer images naar class folders (AANGEPAST)
    for split_name, image_list in [('train', train_images), ('val', val_images)]:
        for idx, (img_path, class_id) in enumerate(image_list):
            # Bepaal class folder
            class_name = CLASS_NAMES[class_id]
            folder_name = f"{class_id}_{class_name}"
            
            # Nieuwe bestandsnaam
            new_name = f"{split_name}_{idx}_{img_path.name}"
            
            # Kopieer naar class folder
            dst_img = OUTPUT_DIR / split_name / folder_name / new_name
            shutil.copy2(img_path, dst_img)
    
    print("✅ Dataset verwerkt! (ImageFolder format)\n")
    print("ℹ️  YOLO v8 gebruikt nu automatisch de folder structuur.")
    print("   Geef alleen het OUTPUT_DIR pad mee bij training.\n")
    
    return OUTPUT_DIR  # Niet data.yaml!

# Run
dataset_path = create_yolo_dataset()
```

**Training cel aanpassen:**

```python
# AANGEPAST: data parameter
results = model.train(
    data=str(dataset_path),  # Was: data=str(data_yaml_path)
    epochs=EPOCHS,
    batch=BATCH_SIZE,
    imgsz=IMAGE_SIZE,
    device=0,  # GPU
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

### 4. Training in Colab

1. **Runtime → Change runtime type → T4 GPU** ⚡
2. Run alle cellen
3. Training duurt ~15-20 minuten
4. Check accuracy (target: >85%)
5. Download `werkplek_classifier.pt`

### 5. Model Plaatsen

```bash
# Download van Colab naar Downloads folder
# Dan:
cd c:\Users\Admin\VisualCode\Projects\School\RefresCO

# Vervang het oude model
copy werkplek_classifier.pt backend\models\werkplek_classifier.pt
```

### 6. Test Backend

```bash
cd backend
python main.py

# Check http://localhost:8000
# Test met een OK foto en een NOK foto
```

## 🔧 Alternatief: Update Bestaand Notebook

Als je het notebook wilt updaten voor volgende keer:

1. Download het aangepaste notebook van hier
2. Upload naar Colab
3. Gebruik die versie voortaan

## ✅ Checklist

- [ ] Dataset ZIP gemaakt of in Drive
- [ ] Colab geopend met GPU
- [ ] Dataset preparation code aangepast
- [ ] Training code aangepast (data parameter)
- [ ] Training gestart
- [ ] Model gedownload
- [ ] Model geplaatst in backend/models/
- [ ] Backend getest
