# Model Types Uitleg

## 📊 Classification Model - Binary (AANBEVOLEN)

### Concept
Een simpel binary classification model dat alleen bepaalt: **OK of NOK**

### Training Data Structuur
```
dataset/
├── train/
│   ├── 0_ok/           # Alle gereedschappen aanwezig
│   └── 1_nok/          # Minimaal 1 gereedschap ontbreekt
└── val/
    ├── 0_ok/
    └── 1_nok/
```

### Model Output
```python
# Voorspelling:
Class 0: OK - Werkplek compleet
Class 1: NOK - Er ontbreekt iets
```

### Voordelen
✅ Simpel te trainen (slechts 2 classes)
✅ Hogere accuracy mogelijk
✅ Snelle inferentie
✅ Minder training data nodig
✅ Robuuster tegen variaties

### Nadelen
❌ Geen details over WAT er ontbreekt
❌ Operator moet zelf kijken

### Training in Google Colab
```python
from ultralytics import YOLO

# Load pretrained model
model = YOLO('yolov8n-cls.pt')

# Train binary classifier
results = model.train(
    data='.',  # Dataset folder
    epochs=50,
    imgsz=640,
    batch=16,
    name='werkplek_binary_classifier'
)

# Validate
metrics = model.val()
print(f"Accuracy: {metrics.top1}")  # Should be high (>95%)

# Export
model.export(format='torchscript')
```

---

## 📊 Classification Model - Multi-class (LEGACY)

### Concept
Gedetailleerd classification model met **8 verschillende classes**

### Training Data Structuur
```
dataset/
├── train/
│   ├── 0_ok/
│   ├── 1_nok_alles_weg/
│   ├── 2_nok_hamer_weg/
│   ├── 3_nok_schaar_weg/
│   ├── 4_nok_schaar_sleutel_weg/
│   ├── 5_nok_sleutel_weg/
│   ├── 6_nok_alleen_sleutel/
│   └── 7_nok_hamer_sleutel_weg/
└── val/
    └── (same structure)
```

### Model Output
```python
# Voorspelling:
Class 0: OK
Class 2: NOK - Hamer weg
Class 3: NOK - Schaar weg
# etc.
```

### Voordelen
✅ Exact inzicht in WAT er ontbreekt
✅ Kan automatisch suggesties geven

### Nadelen
❌ Moeilijk te trainen (8 classes)
❌ Veel training data nodig (200+ per class)
❌ Lagere accuracy
❌ Gevoelig voor imbalance

---

## 🔍 Detection Model

### Concept
Object detection model dat **individuele objecten** detecteert met bounding boxes

### Training Data Structuur
```
dataset/
├── train/
│   ├── images/
│   │   ├── img1.jpg
│   │   └── img2.jpg
│   └── labels/
│       ├── img1.txt  # YOLO format annotations
│       └── img2.txt
└── val/
    └── (same structure)
```

### Annotation Format (YOLO)
```
# img1.txt
0 0.5 0.3 0.1 0.15  # hamer at (x,y) with (w,h)
1 0.7 0.5 0.12 0.18  # schaar
2 0.3 0.6 0.08 0.12  # sleutel
```

### Model Output
```python
# Detecties:
{
  "hamer": 1,      # 1x gedetecteerd
  "schaar": 0,     # 0x gedetecteerd ← ONTBREEKT!
  "sleutel": 1,    # 1x gedetecteerd
  "bounding_boxes": [
    {"object": "hamer", "x1": 100, "y1": 50, "x2": 200, "y2": 150},
    {"object": "sleutel", "x1": 300, "y1": 200, "x2": 380, "y2": 280}
  ]
}
```

### Backend Logic
```python
# Backend redeneert:
if schaar_count == 0:
    status = "NOK - Schaar ontbreekt"
    suggestions = ["Plaats de schaar terug"]
```

### Voordelen
✅ Zeer nauwkeurig - ziet exact waar objecten zijn
✅ Kan objecten tellen (bijv. 2 hamers = fout)
✅ Visuele feedback met bounding boxes
✅ Werkt ook met meerdere exemplaren

### Nadelen
❌ Complexer te trainen (annotations nodig)
❌ Langzamere inferentie
❌ Meer GPU geheugen nodig

### Training in Google Colab
```python
from ultralytics import YOLO

# Load pretrained detection model
model = YOLO('yolo11n.pt')

# Train object detector
results = model.train(
    data='data.yaml',  # Contains paths and class names
    epochs=100,
    imgsz=640,
    batch=16,
    name='werkplek_detector'
)

# Validate
metrics = model.val()
print(f"mAP50: {metrics.box.map50}")

# Export
model.export(format='torchscript')
```

### data.yaml voor Detection
```yaml
# Dataset paths
path: .
train: train/images
val: val/images

# Classes
names:
  0: hamer
  1: schaar
  2: sleutel

# Number of classes
nc: 3
```

---

## 🎯 Aanbeveling per Use Case

### Voor Snelle Controle
→ **Binary Classification**
- Simpel OK/NOK
- Operator kijkt zelf wat er ontbreekt
- Hoogste accuracy
- Minste training data nodig

### Voor Gedetailleerde Feedback
→ **Detection Model**
- Exact zichtbaar wat er ontbreekt
- Kan ook tellen (dubbele objecten detecteren)
- Visuele bounding boxes
- Meest informatief

### Legacy Systeem
→ **Multi-class Classification**
- Alleen gebruiken voor backwards compatibility
- Niet aanbevolen voor nieuwe projecten

---

## 🔄 Model Upload in Admin

Wanneer je een model upload, geef je aan:

```javascript
{
  "model_type": "classification",  // Of "detection"
  "workplace_id": 1,
  "version": "v1.0"
}
```

Het systeem weet dan:
- `classification` → gebruik `analyze_image()` functie
- `detection` → gebruik `analyze_image_detection()` functie

Voor Classification modellen:
- Binary model (2 classes) → automatisch CLASS_INFO_BINARY
- Multi-class model (8 classes) → automatisch CLASS_INFO_MULTICLASS

Het systeem detecteert automatisch hoeveel classes je model heeft!

---

## 📝 Training Workflow

### 1. Verzamel Data
- Maak foto's in operators interface
- Beoordeel in Admin → "Beoordelings Analyse"
- Exporteer dataset via "Training Data" tab

### 2. Train Model (Google Colab)
- Upload dataset ZIP
- Kies model type (Classification of Detection)
- Train met bovenstaande code
- Download best.pt

### 3. Upload Model
- Admin → Werkplekken Beheer
- Selecteer werkplek
- Upload Model → kies type
- Activeer model

### 4. Test
- Operators interface
- Selecteer werkplek
- Maak testfoto
- Controleer resultaat

---

## 🚀 Quick Start voor Nieuwe Werkplek

```bash
1. Admin → Werkplekken Beheer → Voeg toe
   Naam: "Werkplek A - Gereedschap"
   Items: hamer, schaar, sleutel

2. Operators → Maak 100+ foto's
   - 50x OK (alle items aanwezig)
   - 50x NOK (willekeurig items weg)

3. Admin → Beoordelings Analyse
   - Controleer alle foto's
   - Label correct (OK/NOK)

4. Admin → Training Data → Export Dataset
   - Download ZIP file

5. Google Colab → Train Binary Classifier
   - Upload ZIP
   - Train 50 epochs
   - Download best.pt

6. Admin → Werkplekken Beheer → Upload Model
   - Type: Classification
   - Upload best.pt
   - Activeer

7. Operators → Test je model!
```

Succes met trainen! 🎉
