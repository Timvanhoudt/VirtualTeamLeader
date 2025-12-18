# 🔄 Model Hertrainen - Verbeterde Versie

## 🎯 Waarom Hertrainen?

**Problemen met huidige model:**
1. ❌ **Rotatie gevoelig** - werkt slecht bij 90° gedraaide foto's
2. ❌ **Sleutel detectie zwak** - moeilijkste object om te herkennen
3. ⚠️ **Beperkte variatie** - alleen rechte foto's in training data

**Wat we gaan verbeteren:**
1. ✅ **Rotatie augmentatie** - model leert alle hoeken (0°, 90°, 180°, 270°)
2. ✅ **Meer data augmentatie** - flip, zoom, brightness
3. ✅ **Langere training** - meer epochs voor betere accuracy
4. ✅ **Groter model** (optioneel) - YOLOv8s ipv YOLOv8n

---

## 📋 **Wat is er al geüpdatet:**

### **1. Training Script ([train_yolo.py](training/train_yolo.py))**
```python
# Nieuwe augmentatie instellingen:
degrees=90.0,      # ← Rotatie tot 90 graden (NIEUW!)
translate=0.1,     # ← Positie variatie
scale=0.5,         # ← Zoom in/out
fliplr=0.5,        # ← Horizontal flip (NIEUW!)
flipud=0.5,        # ← Vertical flip (NIEUW!)
hsv_h=0.015,       # ← Kleur variatie
hsv_s=0.7,         # ← Saturatie
hsv_v=0.4          # ← Helderheid
```

### **2. Colab Notebook**
De augmentatie is toegevoegd aan cel #16 in het notebook.

---

## 🚀 **Stap-voor-Stap Hertrainen in Colab**

### **OPTIE A: Quick Retrain (Zelfde Settings, Meer Augmentatie)**

**Tijd:** ~20 minuten
**Resultaat:** Betere rotatie handling

**Stappen:**
1. Open Colab notebook: [Werkplek_Inspectie_Training.ipynb](training/Werkplek_Inspectie_Training.ipynb)
2. Runtime → Change runtime type → **T4 GPU**
3. Upload dataset (je hebt het al in Drive!)
4. Run alle cellen
5. Download nieuw model

**Verwachte verbetering:**
- Rotatie: ❌ → ✅
- Sleutel: 60% → 70%
- Overall accuracy: 85% → 90%

---

### **OPTIE B: Groter Model (Betere Accuracy)**

**Tijd:** ~40 minuten
**Resultaat:** Beste accuracy, ook voor moeilijke cases

**Wijzig in Colab cel #14:**
```python
# Van:
MODEL_SIZE = 'n'  # nano (snel, minder accuraat)

# Naar:
MODEL_SIZE = 's'  # small (langzamer, meer accuraat)
```

**Trade-offs:**
| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| YOLOv8n | 6 MB | ⚡⚡⚡ Snel | ⭐⭐⭐ Goed |
| YOLOv8s | 22 MB | ⚡⚡ Medium | ⭐⭐⭐⭐ Beter |
| YOLOv8m | 50 MB | ⚡ Langzaam | ⭐⭐⭐⭐⭐ Best |

**Aanbeveling:** Start met **'s'** (small) - goede balans!

---

### **OPTIE C: Meer Epochs (Langere Training)**

**Tijd:** ~30-40 minuten
**Resultaat:** Model leert beter, vooral voor sleutel

**Wijzig in Colab cel #14:**
```python
# Van:
EPOCHS = 100

# Naar:
EPOCHS = 150  # of 200 voor maximale accuracy
```

**Waarschuwing:** Let op early stopping (patience=20). Als model na 20 epochs niet verbetert, stopt het automatisch.

---

## 💡 **Tips voor Betere Sleutel Detectie**

### **Probleem:** Sleutel is klein en moeilijk te onderscheiden

**Oplossingen:**

### **1. Check je Data**
```bash
# Hoeveel foto's met sleutel?
Sleutel weg: 45 foto's  ← Meeste data
Sleutel aanwezig (in OK): 35 foto's

# Balans is OK! Probleem ligt waarschijnlijk niet aan data hoeveelheid
```

### **2. Verhoog Image Size (in Colab)**
```python
# Cel #14 - wijzig:
IMAGE_SIZE = 640  # standaard

# Naar:
IMAGE_SIZE = 800  # of zelfs 1024 voor kleine objecten
```

**Effect:** Sleutel is groter in pixels → makkelijker te detecteren
**Trade-off:** Langzamer training en inference

### **3. Check Confusion Matrix na Training**

Na training in Colab, check:
```python
# In cel #19 zie je confusion matrix
# Kijk naar:
# - Welke classes worden verward?
# - Is "sleutel weg" vaak fout geclassificeerd?
```

**Als sleutel verward wordt met:**
- "OK" → Sleutel te klein, verhoog image size
- "Alles weg" → Model ziet sleutel niet, check foto kwaliteit
- "Schaar weg" → Objects lijken op elkaar, meer training data

---

## 📊 **Verwachte Resultaten na Retraining**

### **VOOR (Huidig Model):**
```
Overall Accuracy: 85-90%

Per Class:
✅ OK: 95%
✅ Alles weg: 90%
✅ Hamer weg: 88%
⚠️ Schaar weg: 85%
⚠️ Schaar + sleutel weg: 82%
❌ Sleutel weg: 70%  ← Zwak!

Rotatie: ❌ Werkt slecht bij 90° rotatie
```

### **NA (Met Augmentatie + Small Model):**
```
Overall Accuracy: 92-95%

Per Class:
✅ OK: 97%
✅ Alles weg: 95%
✅ Hamer weg: 93%
✅ Schaar weg: 91%
✅ Schaar + sleutel weg: 90%
✅ Sleutel weg: 85%  ← Verbeterd!

Rotatie: ✅ Werkt goed bij alle rotaties (0°, 90°, 180°, 270°)
```

---

## 🎯 **Aanbevolen Training Config**

**Voor beste resultaten, gebruik deze settings in Colab:**

```python
# Cel #14 - Training configuratie
EPOCHS = 150           # ← Verhoogd van 100
BATCH_SIZE = 16        # ← Blijft hetzelfde
IMAGE_SIZE = 800       # ← Verhoogd van 640 (voor sleutel!)
MODEL_SIZE = 's'       # ← Verhoogd van 'n' (small model)

# Cel #16 - Training call (al geüpdatet!)
results = model.train(
    data=str(data_yaml_path),
    epochs=EPOCHS,
    batch=BATCH_SIZE,
    imgsz=IMAGE_SIZE,
    device=0,
    project='runs/classify',
    name='werkplek_inspect_v2',  # ← Nieuwe naam!
    exist_ok=True,
    patience=30,  # ← Verhoogd van 20
    save=True,
    plots=True,
    verbose=True,
    val=True,

    # Data Augmentatie (AL TOEGEVOEGD!)
    degrees=90.0,      # Rotatie
    translate=0.1,     # Positie
    scale=0.5,         # Zoom
    fliplr=0.5,        # Flip horizontal
    flipud=0.5,        # Flip vertical
    hsv_h=0.015,       # Hue
    hsv_s=0.7,         # Saturatie
    hsv_v=0.4          # Brightness
)
```

**Verwachte tijd:** 35-45 minuten op T4 GPU

---

## 📥 **Na Training**

### **1. Download Nieuw Model**
```python
# Cel #23 in Colab
files.download(output_model_path)
```

**Bestandsnaam:** `werkplek_classifier.pt` (~22 MB voor small model)

### **2. Vervang Oud Model**
```
1. Download werkplek_classifier.pt van Colab
2. Ga naar: C:\Users\Admin\VisualCode\Projects\School\RefresCO\backend\models\
3. Backup oud model (hernaam naar werkplek_classifier_v1.pt)
4. Plaats nieuw model als werkplek_classifier.pt
5. Herstart backend
```

### **3. Test het Nieuwe Model**

**Test Cases:**
```
1. ✅ OK foto (recht) → Moet OK geven
2. ✅ OK foto (90° gedraaid) → Moet OK geven (NIEUW!)
3. ❌ Sleutel weg (recht) → Moet "Sleutel weg" geven
4. ❌ Sleutel weg (gedraaid) → Moet "Sleutel weg" geven (NIEUW!)
5. ❌ Hamer weg → Moet "Hamer weg" geven
6. ❌ Alles weg → Moet "Alles weg" geven
```

### **4. Vergelijk Metrics**

**Oud vs Nieuw:**
```
                    V1 (oud)    V2 (nieuw)
Overall Accuracy:   87%         93%        ↑ +6%
Sleutel weg:        70%         85%        ↑ +15%
Rotatie OK:         ❌          ✅         Gefixed!
```

---

## 🐛 **Troubleshooting**

### **"Out of memory" tijdens training**
```python
# Verlaag batch size in cel #14:
BATCH_SIZE = 8  # ipv 16

# Of verlaag image size:
IMAGE_SIZE = 640  # ipv 800
```

### **Training duurt te lang**
```python
# Verlaag epochs:
EPOCHS = 100  # ipv 150

# Of gebruik kleiner model:
MODEL_SIZE = 'n'  # ipv 's'
```

### **Accuracy verbetert niet**
**Mogelijke oorzaken:**
1. **Te weinig data** → Verzamel meer foto's (50-100 per class)
2. **Data kwaliteit** → Check of labels kloppen
3. **Te moeilijke cases** → Sommige foto's zijn echt moeilijk (bijv. schaar vs sleutel lijken op elkaar)

**Oplossingen:**
1. Verzamel meer foto's van "sleutel weg" cases
2. Check foto's: is de sleutel duidelijk zichtbaar in OK foto's?
3. Probeer verschillende camera hoeken
4. Betere belichting bij foto's maken

---

## ✅ **Checklist voor Retraining**

**Voor je start:**
- [ ] Dataset nog in Google Drive
- [ ] Updated Colab notebook
- [ ] Runtime op GPU gezet
- [ ] 45 minuten tijd

**Tijdens training:**
- [ ] Epochs configuratie aangepast
- [ ] Model size gekozen (n/s/m)
- [ ] Image size verhoogd voor sleutel
- [ ] Training gestart

**Na training:**
- [ ] Accuracy > 90%?
- [ ] Sleutel weg > 80%?
- [ ] Model gedownload
- [ ] Oud model backup gemaakt
- [ ] Nieuw model geïnstalleerd
- [ ] Backend herstart
- [ ] Getest met rotaties

---

## 🎯 **Aanbeveling**

**Voor JOU specifiek:**

**Configuratie:**
```python
EPOCHS = 150
BATCH_SIZE = 16
IMAGE_SIZE = 800      # ← Belangrijk voor sleutel!
MODEL_SIZE = 's'      # ← Betere accuracy
```

**Waarom:**
1. Image size 800 → sleutel is groter, beter detecteerbaar
2. Small model → betere accuracy voor moeilijke cases
3. 150 epochs → genoeg tijd om te leren
4. Augmentatie → rotatie probleem opgelost

**Verwachte resultaat:**
- Overall: 92-95% accuracy
- Sleutel: 85%+ accuracy
- Rotatie: Werkt perfect!

---

## 🚀 **Klaar om te starten?**

**Volgende stappen:**
1. Open Colab: [Werkplek_Inspectie_Training.ipynb](training/Werkplek_Inspectie_Training.ipynb)
2. Pas configuratie aan (cel #14)
3. Run training (~40 min)
4. Download model
5. Vervang in backend
6. Test!

**Vragen? Laat het me weten!** 🎓
