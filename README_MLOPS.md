# RefresCO v2 - MLOps Platform 🚀

Complete MLOps platform voor werkplek inspectie met AI model lifecycle management.

## 📋 Overzicht

Dit platform biedt:
- ✅ Multi-werkplek management
- ✅ Training data collectie & labeling
- ✅ Dataset export voor externe training (Colab)
- ✅ Model upload & versie beheer
- ✅ Production deployment & monitoring
- ✅ Feedback loop voor continuous improvement

---

## 🚀 Snel Starten

### Optie 1: Automatisch (Windows)
Dubbelklik op `START_MLOPS.bat`

### Optie 2: Handmatig

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

**URLs:**
- Backend API: `http://localhost:8000`
- Frontend App: `http://localhost:3000`
- Admin Dashboard: `http://localhost:3000` → Klik "⚙️ Admin"

---

## 📖 Gebruikshandleiding

### 1️⃣ Werkplek Toevoegen

1. Open `http://localhost:3000`
2. Klik op **"⚙️ Admin"** rechtsboven
3. Klik op **"+ Nieuwe Werkplek"**
4. Vul in:
   - **Naam**: Bijv. "Werkplek A - Gereedschap"
   - **Beschrijving**: Optioneel
   - **Items**: Komma gescheiden, bijv. "hamer, schaar, sleutel"
5. Klik **"Toevoegen"**

### 2️⃣ Training Data Verzamelen

*(Komt in Fase 2)*
- Upload foto's per situatie
- Label: OK / NOK (welk item ontbreekt)
- Valideer en organiseer

### 3️⃣ Dataset Exporteren

*(Komt in Fase 2)*
- Selecteer werkplek
- Klik "Export Dataset"
- Download ZIP in YOLO format
- Upload naar Google Colab voor training

### 4️⃣ Model Trainen (Extern)

**In Google Colab:**
```python
# Upload je dataset ZIP
# Unzip dataset
# Train YOLO model
# Download trained model.pt
```

### 5️⃣ Model Uploaden

*(Komt in Fase 2)*
- Open Admin → Models tab
- Selecteer werkplek
- Upload .pt bestand
- Vul test accuracy in
- Activeer model

### 6️⃣ Productie Gebruiken

1. Klik "🔧 Werkplek Inspectie AI" (hoofdscherm)
2. Maak foto van werkplek
3. AI analyseert met actieve model
4. Bekijk resultaten

### 7️⃣ Feedback Loop

1. Klik "📊 Geschiedenis"
2. Review analyses
3. Corrigeer fouten
4. Markeer voor retraining
5. Export verbeterde dataset
6. Train nieuw model

---

## 🏗️ Architectuur

```
┌─────────────────────────────────────────────────────────┐
│                     FRONTEND (React)                    │
│  - Werkplek Inspectie (Camera + AI Analysis)          │
│  - Admin Dashboard (Management)                         │
│  - History (Review & Corrections)                       │
└─────────────────────────────────────────────────────────┘
                           ↕️ HTTP API
┌─────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                     │
│  - Werkplek CRUD endpoints                             │
│  - Training data management                             │
│  - Model upload & activation                            │
│  - AI Inference (YOLO)                                  │
│  - Face blur (Privacy)                                  │
└─────────────────────────────────────────────────────────┘
                           ↕️ SQL
┌─────────────────────────────────────────────────────────┐
│                   DATABASE (SQLite)                     │
│  - workplaces (configuratie)                           │
│  - training_images (dataset)                            │
│  - models (versies)                                     │
│  - analyses (productie data)                            │
│  - dataset_exports (tracking)                           │
└─────────────────────────────────────────────────────────┘

                    EXTERNE TRAINING
┌─────────────────────────────────────────────────────────┐
│              Google Colab / GPU Server                  │
│  1. Download dataset ZIP                                │
│  2. Train YOLO model                                    │
│  3. Upload trained .pt file                             │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Database Schema

### Workplaces
```sql
id, name, description, items (JSON), reference_photo,
active, created_at, updated_at
```

### Training Images
```sql
id, workplace_id, image_path, label, class_id,
source, validated, used_in_training, created_at
```

### Models
```sql
id, workplace_id, version, model_path, uploaded_at,
uploaded_by, status, test_accuracy, config, notes
```

### Analyses (Production Data)
```sql
id, timestamp, image_path, predicted_class, predicted_label,
confidence, status, workplace_id, model_version,
corrected_class, corrected_label, notes, ...
```

### Dataset Exports
```sql
id, workplace_id, export_path, image_count,
class_distribution (JSON), exported_at, exported_by, notes
```

---

## 🔌 API Endpoints

### Werkplekken
- `GET /api/workplaces` - Lijst alle werkplekken
- `GET /api/workplaces/{id}` - Werkplek details + stats
- `POST /api/workplaces` - Nieuwe werkplek aanmaken
- `PUT /api/workplaces/{id}` - Werkplek updaten
- `DELETE /api/workplaces/{id}` - Werkplek verwijderen

### Training Data
- `POST /api/workplaces/{id}/training-images` - Upload foto
- `GET /api/workplaces/{id}/training-images` - Lijst foto's
- `GET /api/workplaces/{id}/dataset-stats` - Statistieken

### Modellen
- `POST /api/workplaces/{id}/models` - Upload model (.pt)
- `GET /api/workplaces/{id}/models` - Lijst modellen
- `POST /api/models/{id}/activate` - Activeer model

### Productie
- `POST /api/inspect` - Analyseer werkplek foto
- `GET /api/history` - Analyse geschiedenis
- `POST /api/correct/{id}` - Corrigeer analyse

---

## 📁 Project Structuur

```
RefresCO_v2_MLOps/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── database.py          # Database functies
│   ├── utils/
│   │   └── face_blur.py     # Privacy protection
│   ├── data/
│   │   ├── analyses.db      # SQLite database
│   │   └── training_images/ # Training dataset
│   └── models/
│       └── workplace_{id}/  # Models per werkplek
│
├── frontend/
│   └── src/
│       ├── App.js           # Hoofd applicatie
│       ├── Admin.js         # Admin dashboard
│       ├── History.js       # Analyse geschiedenis
│       └── *.css            # Styling
│
├── training/
│   └── train_yolo.py        # Training scripts (voor Colab)
│
├── START_MLOPS.bat          # Windows start script
├── README_MLOPS.md          # Deze handleiding
└── FASE1_COMPLEET.md        # Ontwikkel documentatie
```

---

## 🧪 Testing

```bash
# Test database functies
python test_api_workplaces.py

# Test backend API
curl http://localhost:8000/
curl http://localhost:8000/api/workplaces

# Test werkplek toevoegen
curl -X POST http://localhost:8000/api/workplaces \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Werkplek","description":"Test","items":["item1","item2"]}'
```

---

## 🔧 Troubleshooting

### Backend start niet
- Check of Python geïnstalleerd is: `python --version`
- Check dependencies: `pip install -r backend/requirements.txt`
- Check of poort 8000 vrij is

### Frontend start niet
- Check of Node.js geïnstalleerd is: `node --version`
- Installeer dependencies: `cd frontend && npm install`
- Check of poort 3000 vrij is

### Database errors
- Verwijder oude database: `rm backend/data/analyses.db`
- Restart backend (maakt nieuwe database aan)

### API errors
- Check console logs in browser (F12)
- Check backend terminal voor errors
- Verify backend draait op `http://localhost:8000`

---

## 📈 Roadmap

### ✅ Fase 1 - Foundation (COMPLEET)
- Database schema
- Backend API endpoints
- Admin dashboard
- Werkplek management

### 🚧 Fase 2 - Data Collection (Volgende)
- Training data upload interface
- Label editor
- Dataset preview
- Export functionaliteit

### 📋 Fase 3 - Model Management
- Model upload interface
- Model testing
- A/B testing
- Performance metrics

### 📋 Fase 4 - Production Feedback
- Production monitoring
- Auto-labeling suggesties
- Retraining workflow
- Continuous improvement

---

## 💡 Tips

1. **Start klein**: Begin met 1 werkplek, verzamel data, train model
2. **Itereer snel**: Train vaak met kleine datasets om te leren
3. **Label zorgvuldig**: Goede labels = beter model
4. **Monitor productie**: Review analyses regelmatig
5. **Gebruik feedback**: Productie data is goud voor verbetering

---

## 🤝 Support

Voor vragen of problemen:
- Check `FASE1_COMPLEET.md` voor technische details
- Check backend logs in terminal
- Check browser console (F12) voor frontend errors

---

## 📝 Licentie

Intern project - RefresCO

**Veel succes met het platform! 🚀**
