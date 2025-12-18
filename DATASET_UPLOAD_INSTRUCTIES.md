# 📤 Dataset Uploaden naar Google Colab - Complete Gids

## 🎯 **Wat je gaat doen:**

Je hebt je dataset op je computer:
```
C:\Users\Admin\Desktop\AI afbeeldingen\
```

Deze moet je in Google Colab krijgen. Er zijn 3 manieren:

---

## ✅ **OPTIE 1: Via Google Drive** (AANBEVOLEN)

### **Waarom deze optie?**
- ✅ Snelst voor grote datasets (211 foto's)
- ✅ Dataset blijft bewaard (kun je later hergebruiken)
- ✅ Geen upload limit

### **Stap-voor-stap:**

#### **1. Open Google Drive**
```
1. Ga naar: drive.google.com
2. Log in met je Google account
```

#### **2. Maak een folder (optioneel maar handig)**
```
1. Klik op "New" (of "+ Nieuw")
2. Kies "Folder" (of "Map")
3. Naam: "School AI Project" (of wat je wilt)
4. Klik "Create"
5. Open de folder (dubbelklik)
```

#### **3. Upload je dataset folder**
```
1. Klik op "New" → "Folder upload" (of "Map uploaden")

   OF sleep je folder:

2. Open File Explorer op je computer
3. Ga naar: C:\Users\Admin\Desktop\
4. Sleep "AI afbeeldingen" folder naar Google Drive browser
```

#### **4. Wacht tot upload klaar is**
```
- Je ziet een upload progress indicator rechtsonder
- Bij 211 foto's duurt dit ~5-15 minuten (afhankelijk van internet)
- BELANGRIJK: Sluit de browser tab NIET tijdens upload!
```

#### **5. Check of upload gelukt is**
```
1. Ga naar je folder in Drive
2. Open "AI afbeeldingen"
3. Je zou moeten zien:
   - Afbeeldingen OK (folder met 35 foto's)
   - Afbeeldingen NOK alles weg (24 foto's)
   - Afbeeldingen NOK hamer weg (36 foto's)
   - Afbeeldingen NOK schaar weg (36 foto's)
   - Afbeeldingen NOK schaar en sleutel weg (35 foto's)
   - Afbeeldingen NOK sleutel weg (45 foto's)
```

#### **6. Kopieer het Drive pad**
```
Optie A - Via adresbalk:
1. Je bent in de "AI afbeeldingen" folder
2. Klik in de adresbalk
3. Kopieer de URL
4. Het pad wordt: /content/drive/MyDrive/[je folder naam]/AI afbeeldingen

Optie B - Onthoud je folder structuur:
Als je uploadde naar: "School AI Project/AI afbeeldingen"
Dan is het pad: /content/drive/MyDrive/School AI Project/AI afbeeldingen
```

#### **7. Pas het pad aan in Colab**
```python
# In het Colab notebook, vind deze regel:
DATASET_SOURCE = '/content/drive/MyDrive/AI afbeeldingen'

# Vervang met jouw pad, bijvoorbeeld:
DATASET_SOURCE = '/content/drive/MyDrive/School AI Project/AI afbeeldingen'

# Of als je direct in MyDrive uploadde:
DATASET_SOURCE = '/content/drive/MyDrive/AI afbeeldingen'
```

#### **8. Mount Drive in Colab**
```python
# Run deze cel in Colab:
from google.colab import drive
drive.mount('/content/drive')

# Volg de instructies:
1. Klik op de link die verschijnt
2. Kies je Google account
3. Klik "Allow"
4. Kopieer de authorization code
5. Plak in Colab en druk Enter
```

#### **9. Test of het werkt**
```python
# Run deze cel om te checken:
!ls -la "/content/drive/MyDrive/School AI Project/AI afbeeldingen"

# Je zou je folders moeten zien!
```

---

## 🗜️ **OPTIE 2: ZIP Upload** (Makkelijkst - voor kleine datasets)

### **Waarom deze optie?**
- ✅ Simpelst, geen Google Drive nodig
- ✅ Eén bestand uploaden ipv 211
- ⚠️ Langzamere upload (1 groot bestand)

### **Stap-voor-stap:**

#### **1. Maak een ZIP van je dataset**
```
Windows:
1. Ga naar: C:\Users\Admin\Desktop\
2. Rechtermuisknop op "AI afbeeldingen" folder
3. Kies "Send to" → "Compressed (zipped) folder"
4. Wacht tot ZIP klaar is
5. Je krijgt: "AI afbeeldingen.zip"
```

#### **2. Open Colab notebook**
```
1. Open Werkplek_Inspectie_Training.ipynb in Colab
2. Zoek de sectie: "OPTIE B: ZIP Upload"
```

#### **3. Upload de ZIP**
```python
# Run deze cel:
from google.colab import files
import zipfile

print("Upload je dataset.zip...")
uploaded = files.upload()

# Er verschijnt een "Choose Files" knop
# Klik erop en selecteer: "AI afbeeldingen.zip"
```

#### **4. Wacht tot upload klaar is**
```
- Je ziet een progress bar
- Bij ~200MB duurt dit ~3-5 minuten
- Wacht tot "Saving AI afbeeldingen.zip to..." verschijnt
```

#### **5. Unzip automatisch**
```python
# De volgende regels in de cel unzippen automatisch:
for filename in uploaded.keys():
    if filename.endswith('.zip'):
        with zipfile.ZipFile(filename, 'r') as zip_ref:
            zip_ref.extractall('/content/dataset_raw')
        print(f"✅ {filename} uitgepakt")
```

#### **6. Check of het werkt**
```python
# Run:
!ls -la /content/dataset_raw

# Je zou je folders moeten zien!
```

---

## 📦 **OPTIE 3: Direct vanuit Project Folder** (Als je project al in Colab hebt)

### **Stap-voor-stap:**

#### **1. Je data staat al in data/raw/**
```bash
# Als je al lokaal werkt, kun je de hele project folder uploaden naar Drive:

1. Zip je hele RefresCO folder
2. Upload naar Google Drive
3. Unzip in Colab
```

#### **2. In Colab:**
```python
# Mount Drive
from google.colab import drive
drive.mount('/content/drive')

# Kopieer project
!cp -r "/content/drive/MyDrive/RefresCO" /content/

# Dataset staat al in data/raw/
DATASET_SOURCE = '/content/RefresCO/data/raw'
```

---

## 🎯 **Welke Optie Kiezen?**

| Situatie | Beste Optie |
|----------|-------------|
| Eerste keer, grote dataset | ✅ **OPTIE 1: Google Drive** |
| Snel iets testen | ✅ **OPTIE 2: ZIP Upload** |
| Lokaal al alles klaar | ✅ **OPTIE 3: Project folder** |
| Internet is langzaam | ✅ **OPTIE 2: ZIP** (1 bestand) |
| Wil dataset bewaren | ✅ **OPTIE 1: Drive** |

---

## 🔍 **Veelgestelde Problemen**

### **Upload duurt heel lang**
```
Oplossing:
- Check je internet snelheid
- Upload in stappen (eerst 1-2 folders testen)
- Gebruik ZIP (Optie 2) - vaak sneller
```

### **"Folder not found" in Colab**
```
Oplossing:
1. Check het pad precies:
   !ls /content/drive/MyDrive/

2. Gebruik quotes als er spaties in naam:
   "/content/drive/MyDrive/School AI Project/AI afbeeldingen"

3. Tab-completion werkt in Colab:
   Type: !ls /content/drive/MyDrive/
   Dan tab - je ziet beschikbare folders
```

### **Drive mount werkt niet**
```
Oplossing:
1. Refresh de Colab pagina
2. Runtime → Restart runtime
3. Run mount cell opnieuw
4. Gebruik ander Google account
```

### **ZIP upload faalt**
```
Oplossing:
1. Check ZIP grootte (max ~200-300MB voor upload)
2. Split dataset in 2 ZIPs als te groot
3. Of gebruik Google Drive (Optie 1)
```

### **Niet alle foto's geüpload**
```
Check:
1. In Drive, klik op folder → rechtermuis → Details
2. Check aantal items
3. Moet 211 foto's zijn (verdeeld over 6 folders)

Als minder:
- Upload was niet compleet
- Probeer opnieuw
```

---

## ✅ **Verificatie Checklist**

Na upload, check dit in Colab:

```python
# 1. Check of folders bestaan
!ls -la /content/dataset_raw/

# Output zou moeten zijn:
# Afbeeldingen OK
# Afbeeldingen NOK alles weg
# Afbeeldingen NOK hamer weg
# Afbeeldingen NOK schaar weg
# Afbeeldingen NOK schaar en sleutel weg
# Afbeeldingen NOK sleutel weg

# 2. Tel foto's
!find /content/dataset_raw -type f \( -name "*.jpg" -o -name "*.png" \) | wc -l

# Output: 211 (of iets meer met extra bestanden)

# 3. Per folder
!find "/content/dataset_raw/Afbeeldingen OK" -type f -name "*.jpg" | wc -l
# Output: 35

!find "/content/dataset_raw/Afbeeldingen NOK hamer weg" -type f -name "*.jpg" | wc -l
# Output: 36

# etc.
```

Als alle checks ✅ zijn → Je kunt verder met training! 🚀

---

## 📝 **Quick Reference**

### **Google Drive Pad Voorbeelden**
```python
# Direct in MyDrive:
DATASET_SOURCE = '/content/drive/MyDrive/AI afbeeldingen'

# In een subfolder:
DATASET_SOURCE = '/content/drive/MyDrive/School/AI afbeeldingen'

# Met spaties in naam (gebruik quotes):
DATASET_SOURCE = "/content/drive/MyDrive/School AI Project/AI afbeeldingen"
```

### **ZIP Upload Code**
```python
from google.colab import files
uploaded = files.upload()
# Klik "Choose Files" → Selecteer ZIP
```

### **Check Dataset**
```python
# Zie wat er is:
!ls -la /content/dataset_raw/

# Tel afbeeldingen:
!find /content/dataset_raw -name "*.jpg" | wc -l
```

---

## 🎯 **Volgende Stap**

Als dataset succesvol geüpload:

1. ✅ Dataset in Colab
2. ▶️ Run preprocessing cel
3. 🚀 Start training!

Zie: [COLAB_TRAINING_GUIDE.md](COLAB_TRAINING_GUIDE.md) voor de rest van de stappen.

---

**Succes! Als je ergens tegenaan loopt, laat het me weten! 📤**
