# 📸 Foto's Maken voor Betere Sleutel Detectie

## 🎯 Doel

**40-50 nieuwe foto's maken** van setup met **ALLEEN de sleutel**

**Setup:**
- ❌ Hamer WEG
- ❌ Schaar WEG
- ✅ Sleutel AANWEZIG

---

## 📋 Checklist voor Fotosessie

### **Benodigdheden:**
- [ ] Tablet of camera
- [ ] Werkplek setup
- [ ] Sleutel
- [ ] Goede belichting
- [ ] 20-30 minuten tijd

---

## 📸 **Fotografie Protocol**

### **Stap 1: Basis Setup** (10 foto's)

**Setup:**
```
Werkplek:
├── Hamer: ❌ VERWIJDER
├── Schaar: ❌ VERWIJDER
└── Sleutel: ✅ LAAT STAAN (normale positie)
```

**Maak:**
1. Rechtsboven (vogelperspectief) - normaal
2. Rechtsboven - iets naar links
3. Rechtsboven - iets naar rechts
4. Schuin links (45°)
5. Schuin rechts (45°)
6. Van voren (horizontaal)
7. Iets verder weg
8. Dichtbij (zoom op sleutel)
9. Normale afstand - schaduw
10. Normale afstand - fel licht

---

### **Stap 2: Verschillende Posities** (10 foto's)

**Varieer sleutel positie:**

```
Positie 1: Links op werkbank
├── Foto 1: Rechtsboven
└── Foto 2: Schuin

Positie 2: Midden op werkbank
├── Foto 3: Rechtsboven
└── Foto 4: Schuin

Positie 3: Rechts op werkbank
├── Foto 5: Rechtsboven
└── Foto 6: Schuin

Positie 4: Onder (lagere positie)
├── Foto 7: Rechtsboven
└── Foto 8: Schuin

Positie 5: Boven (hogere positie)
├── Foto 9: Rechtsboven
└── Foto 10: Schuin
```

---

### **Stap 3: Verschillende Rotaties van SLEUTEL** (10 foto's)

**Draai de sleutel zelf:**

```
Sleutel 0° (horizontaal):
├── Foto 1: Rechtsboven
└── Foto 2: Schuin links

Sleutel 45°:
├── Foto 3: Rechtsboven
└── Foto 4: Schuin rechts

Sleutel 90° (verticaal):
├── Foto 5: Rechtsboven
└── Foto 6: Schuin links

Sleutel 135°:
├── Foto 7: Rechtsboven
└── Foto 8: Schuin rechts

Sleutel 180°:
├── Foto 9: Rechtsboven
└── Foto 10: Schuin links
```

---

### **Stap 4: Verschillende CAMERA Rotaties** (10 foto's)

**Draai de CAMERA/TABLET:**

```
Setup: Sleutel normaal, midden

Camera 0° (normaal):
├── Foto 1: Rechtsboven
└── Foto 2: Schuin

Camera 45° gedraaid:
├── Foto 3: Rechtsboven
└── Foto 4: Schuin

Camera 90° gedraaid (portrait):
├── Foto 5: Rechtsboven
└── Foto 6: Schuin

Camera 180° gedraaid (ondersteboven):
├── Foto 7: Rechtsboven
└── Foto 8: Schuin

Camera 270° gedraaid:
├── Foto 9: Rechtsboven
└── Foto 10: Schuin
```

---

### **Stap 5: Extra Variaties** (10 foto's)

**Verschillende condities:**

```
1. Fel zonlicht
2. Schaduw
3. Kunstlicht
4. Half in schaduw
5. Met reflectie
6. Iets wazig (onscherp)
7. Zeer scherp (focus op sleutel)
8. Achtergrond rommelig
9. Achtergrond schoon
10. Sleutel half buiten beeld (edge case)
```

---

## 📁 **Folder Structuur**

```
C:\Users\Admin\Desktop\AI afbeeldingen\
├── Afbeeldingen OK\
├── Afbeeldingen NOK alles weg\
├── Afbeeldingen NOK hamer weg\
├── Afbeeldingen NOK schaar weg\
├── Afbeeldingen NOK schaar en sleutel weg\
├── Afbeeldingen NOK sleutel weg\
└── Afbeeldingen NOK alleen sleutel\     ← NIEUW! (40-50 foto's)
    ├── alleen_sleutel_001.jpg
    ├── alleen_sleutel_002.jpg
    ├── alleen_sleutel_003.jpg
    └── ...
```

---

## ✅ **Kwaliteits Checklist**

### **Per Foto Check:**
- [ ] Sleutel is duidelijk zichtbaar
- [ ] Hamer is NIET aanwezig
- [ ] Schaar is NIET aanwezig
- [ ] Foto is scherp (niet te wazig)
- [ ] Goede belichting (niet te donker/licht)
- [ ] Hele werkplek in beeld
- [ ] Minimaal 1920x1080 resolutie

### **Na Fotosessie:**
- [ ] 40-50 foto's gemaakt
- [ ] Alle foto's gekopieerd naar juiste folder
- [ ] Foto's hernoemd (optioneel)
- [ ] Backup gemaakt
- [ ] Klaar voor upload naar Drive/Colab

---

## 🎯 **Waarom Deze Variatie?**

### **1. Positie Variatie**
```
Waarom: Sleutel kan overal liggen
Effect: Model leert sleutel herkennen ongeacht positie
```

### **2. Rotatie Variatie (Sleutel)**
```
Waarom: Sleutel kan gedraaid liggen
Effect: Model leert sleutel in alle richtingen
```

### **3. Rotatie Variatie (Camera)**
```
Waarom: Tablet kan gedraaid worden bij foto
Effect: Model leert sleutel bij gedraaide foto's
```

### **4. Licht Variatie**
```
Waarom: Belichting verschilt per situatie
Effect: Model leert sleutel in alle licht condities
```

### **5. Focus Variatie**
```
Waarom: Sleutel is het belangrijkste object
Effect: Model leert verschil tussen sleutel vs andere objecten
```

---

## 📊 **Verwachte Impact**

### **VOOR (Huidige Dataset):**
```
Sleutel herkenning: 70%
Sleutel focus foto's: 35 (in "OK" class)
Sleutel variatie: Laag
```

### **NA (Met Nieuwe Foto's):**
```
Sleutel herkenning: 85-90% ⬆️
Sleutel focus foto's: 35 + 50 = 85
Sleutel variatie: Hoog
```

**Verbetering:** +15-20% accuracy op sleutel detectie!

---

## 🚀 **Na de Fotosessie**

### **Stap 1: Organiseer Foto's**
```bash
1. Kopieer alle foto's naar:
   C:\Users\Admin\Desktop\AI afbeeldingen\Afbeeldingen NOK alleen sleutel\

2. Hernaam (optioneel):
   alleen_sleutel_001.jpg
   alleen_sleutel_002.jpg
   ...
```

### **Stap 2: Upload naar Google Drive**
```
1. Ga naar drive.google.com
2. Open je "AI afbeeldingen" folder
3. Maak nieuwe folder: "Afbeeldingen NOK alleen sleutel"
4. Upload alle 40-50 foto's
```

### **Stap 3: Retrain in Colab**
```
1. Open Werkplek_Inspectie_Training.ipynb
2. Check dat nieuwe folder wordt herkend
3. Run preprocessing (cel #11)
4. Check output:
   ✓ Afbeeldingen NOK alleen sleutel: 50 afbeeldingen (class 6)
5. Run training (cel #16)
6. Download nieuw model
```

---

## 💡 **Pro Tips**

### **Tip 1: Batch Fotograferen**
```
✅ Maak eerst 10 foto's met setup A
✅ Dan verander positie → 10 foto's setup B
✅ Etc.

❌ Niet: Elke foto andere setup
   (Te traag, verlies focus)
```

### **Tip 2: Gebruik Timer/Burst Mode**
```
✅ Zet tablet op statief/vast
✅ Gebruik timer of burst mode
✅ 3-5 foto's per positie

Resultaat: Scherpere foto's, sneller klaar
```

### **Tip 3: Check Onderweg**
```
Na elke 10 foto's:
- Open een paar foto's
- Check of sleutel goed zichtbaar is
- Check belichting
- Check scherpte
```

### **Tip 4: Backup Direct**
```
✅ Kopieer foto's direct naar PC
✅ Maak backup op tweede locatie
✅ Upload naar Drive zodra klaar

❌ Wacht niet tot einde
   (Risico: fotos kwijt!)
```

---

## 🎯 **Minimale Requirements**

**Absoluut minimum voor verbetering:**
- ⭐ **30 foto's** - Basis verbetering
- ⭐⭐ **40 foto's** - Goede verbetering (AANBEVOLEN)
- ⭐⭐⭐ **50+ foto's** - Maximale verbetering

**Focus op:**
1. ✅ Verschillende rotaties (BELANGRIJKST!)
2. ✅ Verschillende posities
3. ✅ Verschillende belichting

---

## ✅ **Klaar om te Beginnen?**

**Checklist:**
- [ ] Setup klaar (sleutel, werkplek)
- [ ] Tablet/camera klaar
- [ ] Goede belichting
- [ ] 20-30 min tijd
- [ ] Folder aangemaakt

**Start met:**
1. Stap 1: Basis Setup (10 foto's) - warm up
2. Stap 4: Camera Rotaties (10 foto's) - BELANGRIJKST!
3. Stap 2: Posities (10 foto's)
4. Stap 3: Sleutel Rotaties (10 foto's)
5. Stap 5: Extra Variaties (10 foto's)

**Totaal: 50 foto's = 85%+ sleutel accuracy!** 🎯

---

**Succes met fotograferen!** 📸✨
