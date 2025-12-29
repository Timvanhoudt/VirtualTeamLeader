# 🚀 Google Colab Training Guide

Complete stap-voor-stap instructies voor het trainen van je YOLO model in Google Colab.

## 🎯 Waarom Colab?

✅ **Gratis GPU** (15x sneller dan CPU!)
✅ **Geen lokale installatie** nodig
✅ **Training in ~15-20 minuten** ipv 2-3 uur
✅ **Geen GPU op je eigen PC** nodig

---

## 📋 Voor je Begint

**Wat je nodig hebt:**
1. Google account
2. Je dataset folder: `AI afbeeldingen` (211 foto's)
3. Het notebook: `Werkplek_Inspectie_Training.ipynb`

**Dataset voorbereiden:**

Je dataset moet er zo uitzien:
```
AI afbeeldingen/
├── Afbeeldingen OK/
├── Afbeeldingen NOK alles weg/
├── Afbeeldingen NOK hamer weg/
├── Afbeeldingen NOK schaar weg/
├── Afbeeldingen NOK schaar en sleutel weg/
└── Afbeeldingen NOK sleutel weg/
```

---

## 🚀 Stap-voor-Stap Instructies

### **Stap 1: Upload Dataset naar Google Drive**

1. Open [Google Drive](https://drive.google.com)
2. Maak een nieuwe folder (bijv. "Werkplek AI")
3. Upload je **hele** `AI afbeeldingen` folder
   - Drag & drop de folder
   - Of: Rechtermuisknop → Upload folder
4. Wacht tot upload compleet is

**Alternatief (kleine dataset):**
- Zip je `AI afbeeldingen` folder lokaal
- Je uploadt de ZIP later direct in Colab

---

### **Stap 2: Open Notebook in Google Colab**

**Optie A: Via Google Drive**
1. Upload `Werkplek_Inspectie_Training.ipynb` naar Google Drive
2. Dubbelklik op het bestand
3. Klik "Open with Google Colaboratory"
   - Staat Colaboratory er niet? → "Connect more apps" → Zoek "Colaboratory"

**Optie B: Direct upload**
1. Ga naar [colab.research.google.com](https://colab.research.google.com)
2. File → Upload notebook
3. Selecteer `Werkplek_Inspectie_Training.ipynb`

---

### **Stap 3: Zet Runtime op GPU** ⚠️ **BELANGRIJK!**

1. Klik in menu: **Runtime** → **Change runtime type**
2. Bij "Hardware accelerator" kies: **T4 GPU**
3. Klik **Save**

**Check of GPU actief is:**
- Run de eerste cel (nvidia-smi)
- Je moet GPU info zien, bijv: "Tesla T4"

---

### **Stap 4: Run het Notebook**

**Je hebt 2 opties voor dataset upload:**

#### **OPTIE A: Vanuit Google Drive** (Aanbevolen voor grote datasets)

1. **Cel: "Mount Google Drive"**
   - Run deze cel
   - Klik op de link
   - Selecteer je Google account
   - Kopieer de authorization code
   - Plak in Colab en druk Enter

2. **Pas het pad aan:**
   ```python
   DATASET_SOURCE = '/content/drive/MyDrive/Werkplek AI/AI afbeeldingen'
   ```
   ⚠️ Vervang dit met **jouw** Drive pad!

3. **Run de cel** → Dataset wordt gekopieerd naar Colab

#### **OPTIE B: ZIP Upload** (Voor datasets < 100MB)

1. **Zip je dataset lokaal:**
   - Rechtermuisknop op `AI afbeeldingen` folder
   - "Send to" → "Compressed (zipped) folder"

2. **Run de upload cel:**
   - Klik "Choose Files"
   - Selecteer je ZIP
   - Wacht op upload

---

### **Stap 5: Run alle Cellen** 🎯

Nu kun je **alle cellen achter elkaar runnen:**

**Sneltoets:** Runtime → Run all

**Of cel voor cel:**
1. ✅ Setup omgeving (2 min)
2. ✅ Upload dataset (5 min, afhankelijk van methode)
3. ✅ Prepareer dataset (1 min)
4. ✅ Train model (15-20 min) ☕
5. ✅ Evaluatie (2 min)
6. ✅ Download model (1 min)

**Totaal: ~25-30 minuten**

---

### **Stap 6: Training Monitoren** 📊

Tijdens training zie je:
```
Epoch    GPU_mem   loss   top1_acc   top5_acc
  1/100     1.2G    2.45    0.234      0.876
  2/100     1.2G    2.12    0.345      0.912
  ...
```

**Belangrijk:**
- `loss` moet **omlaag** gaan
- `top1_acc` moet **omhoog** gaan (dit is je accuracy!)
- `GPU_mem` laat GPU gebruik zien

**Early stopping:**
- Training stopt automatisch als er 20 epochs geen verbetering is
- Dit is normaal en bespaart tijd!

---

### **Stap 7: Resultaten Bekijken** 📈

Na training zie je:

**1. Metrics:**
```
Top-1 Accuracy: 92.5%  ← Je model accuracy
Top-5 Accuracy: 98.7%
```

**2. Training Plots:**
- **results.png**: Loss & accuracy curves
- **confusion_matrix.png**: Waar maakt het model fouten?
- **val_batch0_pred.jpg**: Voorbeelden van voorspellingen

**3. Test Voorbeelden:**
- 5 test afbeeldingen met voorspellingen
- Check of voorspellingen kloppen!

---

### **Stap 8: Download Getraind Model** ⬇️

**Automatisch downloaden:**
1. Run de download cel
2. Bestand `werkplek_classifier.pt` wordt gedownload
3. Check je Downloads folder

**Of vanaf Google Drive:**
- Model wordt ook opgeslagen in je Drive
- Handig als download faalt

**Bestandsgrootte:** ~5-10 MB

---

### **Stap 9: Model Plaatsen in Project** 📁

1. Ga naar je project folder:
   ```
   C:\Users\Admin\VisualCode\Projects\School\RefresCO\
   ```

2. Plaats `werkplek_classifier.pt` in:
   ```
   backend/models/werkplek_classifier.pt
   ```

3. **Check of het werkt:**
   ```bash
   cd backend
   python main.py
   ```

4. Je zou moeten zien:
   ```
   📥 Laden YOLO model: models/werkplek_classifier.pt
   ✅ Model geladen
   ```

---

## 🎓 Model Evaluatie

### **Wat is een goede accuracy?**

| Accuracy | Betekenis |
|----------|-----------|
| > 90% | 🎉 Excellent! Productie-ready |
| 80-90% | ✅ Goed, bruikbaar |
| 70-80% | ⚠️ Matig, meer data nodig |
| < 70% | ❌ Slecht, model revisie nodig |

### **Als accuracy te laag is:**

**1. Meer data verzamelen**
- Target: minimaal 50-100 foto's per categorie
- Variatie: verschillende hoeken, belichting, afstanden

**2. Langere training**
- Verhoog `EPOCHS` van 100 → 150 of 200
- Verlaag `patience` niet, early stopping is goed

**3. Groter model**
- Verander in notebook:
  ```python
  MODEL_SIZE = 's'  # ipv 'n'
  ```
- Small model is accurater maar langzamer

**4. Check je data**
- Zijn labels correct?
- Zijn foto's duidelijk genoeg?
- Zitten er verkeerde foto's in de folders?

---

## 🐛 Troubleshooting

### **"GPU not available"**
**Oplossing:**
- Runtime → Change runtime type → T4 GPU
- Save en reconnect
- Run nvidia-smi cell opnieuw

### **"Drive mount failed"**
**Oplossing:**
- Refresh de pagina
- Run mount cell opnieuw
- Check authorization code

### **"Out of memory"**
**Oplossing:**
- Verlaag `BATCH_SIZE`:
  ```python
  BATCH_SIZE = 8  # ipv 16
  ```
- Of verlaag `IMAGE_SIZE`:
  ```python
  IMAGE_SIZE = 320  # ipv 640
  ```

### **"Dataset folder not found"**
**Oplossing:**
- Check het pad in de cel
- Run `!ls /content/dataset_raw` om te zien wat er is
- Pas `DATASET_SOURCE` pad aan

### **Training duurt te lang**
**Oorzaken:**
- GPU niet actief → Check Runtime type
- Te grote batch size → Verlaag naar 8
- CPU training is 15x langzamer!

### **Model download werkt niet**
**Oplossing:**
- Check Google Drive backup:
  ```
  /content/drive/MyDrive/werkplek_classifier.pt
  ```
- Of download handmatig via Files panel (links)

---

## 💡 Tips & Tricks

### **Colab Session Management**
- Colab timeout na **90 minuten inactiviteit**
- Max **12 uur** per sessie
- Bewaar regelmatig naar Drive!

### **Download ook de plots**
```python
# In een nieuwe cel:
from google.colab import files
files.download('runs/classify/werkplek_inspect/results.png')
files.download('runs/classify/werkplek_inspect/confusion_matrix.png')
```

### **Training herstarten**
Als je session crashed:
1. Reconnect
2. Run vanaf "Train YOLO Model" cel
3. Model checkpoints staan in `runs/`

### **Meerdere runs vergelijken**
```python
# Verander naam bij training:
name='werkplek_inspect_v2',
```
Dan staan ze in aparte folders

---

## 📊 Verwachte Resultaten

Met je dataset (211 foto's, 6 classes):

**Verwachte accuracy:** 85-95%

**Training tijd:**
- GPU (T4): ~15-20 minuten
- CPU: ~2-3 uur ❌ (gebruik altijd GPU!)

**Model size:** ~6 MB (nano model)

**Confusion matrix:**
- Diagonaal moet donker zijn (goede voorspellingen)
- Off-diagonal moet licht zijn (weinig fouten)

---

## ✅ Checklist

Voor je begint:
- [ ] Google account ingelogd
- [ ] Dataset in Drive of ZIP klaar
- [ ] Notebook geopend in Colab
- [ ] Runtime op GPU gezet
- [ ] 30 minuten tijd

Na training:
- [ ] Accuracy > 80%
- [ ] Model gedownload
- [ ] Model in `backend/models/` geplaatst
- [ ] Backend test gedaan
- [ ] Plots bekeken en opgeslagen

---

## 🎯 Volgende Stappen

Na successful training:

1. **Test de backend:**
   ```bash
   cd backend
   python main.py
   # Test op http://localhost:8000
   ```

2. **Start de frontend:**
   ```bash
   cd frontend
   npm install
   npm start
   # Open http://localhost:3000
   ```

3. **Maak test foto's:**
   - Test met echte werkplek foto's
   - Check of voorspellingen kloppen
   - Documenteer je resultaten

4. **Voor je presentatie:**
   - Screenshots van training plots
   - Demo van werkende app
   - Accuracy metrics
   - Voorbeelden van OK/NOK detectie

---

## 📞 Hulp Nodig?

**Errors in Colab?**
- Check de error message
- Google: "colab [error message]"
- Vaak is het een simpel pad probleem

**Model werkt niet goed?**
- Check confusion matrix: welke classes worden verward?
- Kijk naar misclassificeerde voorbeelden
- Meer data van die specifieke classes verzamelen

**Vragen?**
- Laat het me weten, ik help je verder! 🚀

---

Succes met je training! 🎉
