# 🔄 Model Hertrainen Handleiding

Deze handleiding beschrijft hoe je de AI modellen kunt hertrainen in Google Colab. We ondersteunen nu twee typen modellen:
1. **Classificatie** (Bepaalt of een werkplek OK/NOK is + reden)
2. **Object Detectie** (Vindt specifieke tools zoals Hamer, Schaar, Sleutel)

---

## 📂 1. Kies je Notebook

Afhankelijk van wat je wilt trainen, gebruik je een ander notebook. Alle notebooks staan in de `training/` map.

| Doel | Notebook Bestand | Beschrijving |
|------|------------------|--------------|
| **Classificatie** | `Werkplek_Inspectie_Classification.ipynb` | Voor het trainen van het hoofdmodel (7 klasses: OK, NOK hamer weg, etc.) |
| **Object Detectie** | `Werkplek_Inspectie_Detection.ipynb` | Voor het trainen van de tool detector (bounding boxes om tools) |

---

## 🖼️ 2. Dataset Voorbereiden

### Voor Classificatie:
- Gebruik mappenstructuur met klassenamen:
  ```
  dataset/
  ├── OK/
  ├── NOK hamer weg/
  ├── NOK schaar weg/
  └── ...
  ```
- Upload deze map naar Google Drive (bijv. `/content/drive/MyDrive/AI Refresco`)

### Voor Object Detectie:
- Gebruik een CVAT export (YOLO 1.1 formaat) of een map met `images` en `labels`.
- Zorg dat er een `data.yaml` is (wordt automatisch gegenereerd als je de scripts gebruikt).
- Zip je export (bijv. `dataset.zip`).
- Upload naar Google Drive of direct in Colab.

---

## 🚀 3. Training Starten in Google Colab

1. Ga naar [Google Colab](https://colab.research.google.com/)
2. Upload het juiste notebook bestand (`.ipynb`)
3. **Zet Runtime op GPU:** `Runtime` -> `Change runtime type` -> `T4 GPU`
4. Volg de stappen in het notebook.

### Belangrijke Instellingen (in het notebook):

#### Classificatie (`Werkplek_Inspectie_Classification.ipynb`)
- **Augmentatie:** Standaard AAN (rotatie, flip, zoom) voor betere herkenning.
- **Model:** `yolov8n-cls.pt` (nano) of `yolov8s-cls.pt` (small - nauwkeuriger).
- **Epochs:** 100 is meestal genoeg.

#### Object Detectie (`Werkplek_Inspectie_Detection.ipynb`)
- **Model:** `yolov8n.pt` (nano) of `yolov8s.pt` (small).
- **Image Size:** `640` is standaard. Verhoog naar `800` als kleine objecten (sleutels) gemist worden.
- **Classes:** Worden automatisch uit je `data.yaml` gelezen.

---

## 📥 4. Model Downloaden & Installeren

Na training download je het `.pt` bestand (bijv. `best.pt`).

1. Hernoem het bestand:
   - Classificatie: `werkplek_classifier.pt`
   - Object Detectie: `werkplek_detector.pt`
2. Plaats in je project map: `backend/models/`
3. Herstart de backend server.

---

## ❓ Problemen Oplossen

- **Training duurt te lang?** Gebruik een kleiner model ('n') of minder epochs.
- **Out of Memory?** Verlaag de `BATCH_SIZE` in het notebook (bijv. naar 8).
- **Slechte detectie van sleutels?** Probeer Object Detectie met `IMAGE_SIZE = 800`.
