# 🔧 Werkplek Inspectie AI

AI-powered werkplek controle systeem voor kwaliteitscontrole taken.

## 📋 Overzicht

Deze applicatie gebruikt YOLO AI om werkplekken te inspecteren en automatisch te detecteren of taken correct zijn uitgevoerd.

**3-staps proces:**
1. **Foto maken** → AI bepaalt OK/NOK
2. **Probleem detectie** → Wat ontbreekt er?
3. **Suggesties** → Hoe te herstellen

**Features:**
- ✅ Automatische OK/NOK classificatie
- 🔍 Detectie van ontbrekende items
- 💡 Herstel suggesties
- 🔒 Privacy: automatische gezichtsblur
- 📱 Tablet/mobile friendly
- 📷 Camera integratie

## 🏗️ Project Structuur

```
RefresCO/
├── backend/           # FastAPI backend
│   ├── main.py       # API server
│   ├── models/       # Getrainde YOLO modellen
│   └── utils/        # Face blur & helpers
├── frontend/         # React frontend
│   ├── src/
│   └── public/
├── data/
│   ├── raw/          # Originele dataset (211 foto's)
│   ├── processed/    # Verwerkte data voor training
│   └── annotations/  # Labels
├── training/         # Training scripts
│   ├── prepare_dataset.py
│   └── train_yolo.py
└── README.md
```

## 🚀 Installatie & Setup

### 1. Backend Setup

```bash
cd backend

# Installeer dependencies
pip install -r requirements.txt
```

### 2. Dataset Voorbereiden

```bash
cd training

# Converteer dataset naar YOLO format
python prepare_dataset.py
```

**Output:**
- Train/val split (80/20)
- YOLO compatible folder structuur
- data.yaml configuratie

### 3. Model Trainen

```bash
# Train het YOLO classificatie model
python train_yolo.py
```

**Training configuratie:**
- Model: YOLOv8n-cls (nano, snel)
- Epochs: 100
- Batch size: 16
- Image size: 640x640
- Early stopping: 20 epochs patience

**Verwachte training tijd:**
- GPU: ~15-20 minuten
- CPU: ~2-3 uur

**Output:**
- Getraind model: `backend/models/werkplek_classifier.pt`
- Training plots: `training/runs/classify/werkplek_inspect/`
- Metrics: accuracy, loss curves

### 4. Frontend Setup

```bash
cd frontend

# Installeer dependencies
npm install

# Start development server
npm start
```

Frontend draait op: http://localhost:3000

### 5. Backend Starten

```bash
cd backend

# Start FastAPI server
python main.py
```

API draait op: http://localhost:8000

**API Endpoints:**
- `GET /` - Health check
- `GET /api/classes` - Haal alle classes op
- `POST /api/inspect` - Inspecteer werkplek foto
- `POST /api/compare` - Vergelijk met referentie

## 📊 Dataset Info

**Huidige dataset: 211 foto's**

| Categorie | Aantal | Type |
|-----------|--------|------|
| ✅ OK (compleet) | 35 | OK |
| ❌ Alles weg | 24 | NOK |
| ❌ Hamer weg | 36 | NOK |
| ❌ Schaar weg | 36 | NOK |
| ❌ Schaar + sleutel weg | 35 | NOK |
| ❌ Sleutel weg | 45 | NOK |

**Classes (6 totaal):**
- Class 0: OK
- Class 1: NOK - Alles weg
- Class 2: NOK - Hamer weg
- Class 3: NOK - Schaar weg
- Class 4: NOK - Schaar en sleutel weg
- Class 5: NOK - Sleutel weg

## 🎯 Gebruik

### Via Frontend (Aanbevolen)

1. Open http://localhost:3000
2. Selecteer situatie (Zeef, Werkbank, etc.)
3. Maak foto met tablet camera OF upload foto
4. Klik "Volgende Controle"
5. Bekijk resultaten:
   - Stap 1: OK/NOK status
   - Stap 2: Wat is er NOK (indien van toepassing)
   - Stap 3: Herstel suggesties

### Via API (Direct)

```python
import requests

# Upload en analyseer foto
with open('test_foto.jpg', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:8000/api/inspect',
        files=files,
        data={'blur_faces': 'true'}
    )

results = response.json()
print(f"Status: {results['step1_classification']['result']}")
print(f"Zekerheid: {results['step1_classification']['confidence']:.2%}")

if results['step1_classification']['status'] == 'nok':
    print(f"Probleem: {results['step2_analysis']['description']}")
    for suggestion in results['step3_suggestions']:
        print(f"- {suggestion['action']}")
```

## 🔒 Privacy

**Automatische gezichtsblur:**
- Gebruikt OpenCV Haar Cascade voor face detection
- Blur strength: 99 (zeer sterk)
- Processeert voor opslag en analyse
- GDPR compliant

## 🎓 Ontwikkeling

### Nieuw model trainen met eigen data

1. **Voeg foto's toe** aan `data/raw/` in folders:
   ```
   data/raw/
   ├── Afbeeldingen OK/
   ├── Afbeeldingen NOK [type defect]/
   └── ...
   ```

2. **Update class mapping** in `training/prepare_dataset.py`:
   ```python
   CLASS_MAPPING = {
       "Afbeeldingen OK": 0,
       "Nieuwe categorie": 6,
       # ...
   }
   ```

3. **Run preprocessing**: `python training/prepare_dataset.py`

4. **Train nieuw model**: `python training/train_yolo.py`

### Model verbeteren

**Meer data:**
- Verzamel meer foto's per categorie
- Target: minimaal 50-100 per class

**Data augmentatie:**
- Rotatie, flip, brightness
- Voeg toe in `train_yolo.py`

**Groter model:**
- Verander `yolov8n-cls.pt` → `yolov8s-cls.pt` (small)
- Meer accuracy, langzamer inference

**Hyperparameters tunen:**
- Epochs verhogen
- Learning rate aanpassen
- Batch size optimaliseren

## 📁 Belangrijke Files

| File | Beschrijving |
|------|-------------|
| `backend/main.py` | FastAPI server met alle endpoints |
| `backend/utils/face_blur.py` | Privacy face blur utility |
| `training/prepare_dataset.py` | Dataset preprocessing |
| `training/train_yolo.py` | YOLO training script |
| `frontend/src/App.js` | Hoofd React component |
| `data/processed/yolo_dataset/data.yaml` | YOLO config |

## 🐛 Troubleshooting

**Model niet gevonden:**
```bash
# Check of model bestaat
ls backend/models/werkplek_classifier.pt

# Zo niet, train eerst:
cd training && python train_yolo.py
```

**Camera werkt niet:**
- Check browser permissions (HTTPS vereist voor camera access)
- Test op localhost werkt meestal

**Training te langzaam:**
- Gebruik GPU (CUDA)
- Of verlaag epochs/batch size
- Of gebruik kleinere image size (320)

**Lage accuracy:**
- Meer training data verzamelen
- Langere training (meer epochs)
- Check data quality (labels correct?)

## 📝 To-Do / Toekomstige Features

- [ ] Object detection ipv classificatie (bounding boxes)
- [ ] Multi-object tracking
- [ ] Historische data opslag
- [ ] Dashboard met statistieken
- [ ] Exporteer rapporten (PDF)
- [ ] Multi-taal ondersteuning
- [ ] User management / login
- [ ] Mobile app (React Native)

## 👨‍💻 Tech Stack

**Backend:**
- Python 3.8+
- FastAPI
- Ultralytics YOLO v8
- OpenCV
- PyTorch

**Frontend:**
- React 18
- React Webcam
- Axios

**AI/ML:**
- YOLOv8n-cls (classificatie)
- OpenCV Haar Cascade (face detection)

## 📄 Licentie

School project - Vrij te gebruiken voor educatieve doeleinden

## 🎉 Credits

Gebouwd met Claude Code AI Assistant
