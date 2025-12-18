"""
FastAPI Backend voor Werkplek Inspectie AI
Endpoints voor foto upload, analyse en resultaten
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO
from datetime import datetime
import io
from PIL import Image
import base64

from utils.face_blur import FaceBlurrer
from database import init_database, save_analysis

app = FastAPI(
    title="Werkplek Inspectie API",
    description="AI-powered werkplek controle systeem",
    version="1.0.0"
)

# Initialiseer database bij startup
@app.on_event("startup")
async def startup_event():
    init_database()
    print("✅ Database geïnitialiseerd bij startup")

# CORS voor frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In productie: specificeer je frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files voor reference photos
reference_photos_dir = Path("data/reference_photos")
reference_photos_dir.mkdir(parents=True, exist_ok=True)
app.mount("/data/reference_photos", StaticFiles(directory=str(reference_photos_dir)), name="reference_photos")

# Mount static files voor training images
training_images_dir = Path("data/training_images")
training_images_dir.mkdir(parents=True, exist_ok=True)
app.mount("/data/training_images", StaticFiles(directory=str(training_images_dir)), name="training_images")

# Globale variabelen
MODEL_PATH = Path("models/werkplek_classifier.pt")
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# AI Models (lazy loading)
yolo_model = None
face_blurrer = None

# Class mapping - ALFABETISCHE VOLGORDE (zoals YOLO ImageFolder ze leest)
# YOLOv8 sorteert folders alfabetisch:
# 0_ok, 1_nok_alles_weg, 2_nok_hamer_weg, 3_nok_schaar_weg,
# 4_nok_schaar_sleutel_weg, 5_nok_sleutel_weg, 6_nok_alleen_sleutel
CLASS_INFO = {
    0: {"name": "OK", "status": "ok", "description": "Werkplek is compleet en correct"},
    1: {"name": "NOK - Alles weg", "status": "nok", "description": "Alle gereedschappen ontbreken", "missing": ["hamer", "schaar", "sleutel"]},
    2: {"name": "NOK - Hamer weg", "status": "nok", "description": "Hamer ontbreekt", "missing": ["hamer"]},
    3: {"name": "NOK - Schaar weg", "status": "nok", "description": "Schaar ontbreekt", "missing": ["schaar"]},
    4: {"name": "NOK - Schaar en sleutel weg", "status": "nok", "description": "Schaar en sleutel ontbreken", "missing": ["schaar", "sleutel"]},
    5: {"name": "NOK - Sleutel weg", "status": "nok", "description": "Sleutel ontbreekt", "missing": ["sleutel"]},
    6: {"name": "NOK - Alleen sleutel", "status": "nok", "description": "Alleen sleutel aanwezig, hamer en schaar ontbreken", "missing": ["hamer", "schaar"]}
}

SUGGESTIONS = {
    "hamer": "Plaats de kunstofhamer terug op de aangewezen positie",
    "schaar": "Plaats de schaar terug in de gereedschapskist",
    "sleutel": "Plaats de sleutel terug op de werkbank"
}


def load_models():
    """Laad AI models (lazy loading)"""
    global yolo_model, face_blurrer

    if yolo_model is None:
        if MODEL_PATH.exists():
            print(f"📥 Laden YOLO model: {MODEL_PATH}")
            yolo_model = YOLO(str(MODEL_PATH))
        else:
            print("⚠ YOLO model niet gevonden, gebruik dummy mode")
            yolo_model = "dummy"

    if face_blurrer is None:
        print("📥 Laden face blur model...")
        face_blurrer = FaceBlurrer()


def process_image_bytes(image_bytes):
    """Convert bytes naar OpenCV image"""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img


def blur_faces_in_image(image):
    """Blur gezichten in afbeelding"""
    load_models()
    blurred_img, face_count = face_blurrer.blur_faces(image.copy())
    return blurred_img, face_count


def image_to_base64(image):
    """Convert OpenCV image naar base64 string"""
    _, buffer = cv2.imencode('.jpg', image)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{img_base64}"


def analyze_image(image):
    """
    Analyseer afbeelding met YOLO model

    Returns:
        dict met resultaten
    """
    load_models()

    if yolo_model == "dummy":
        # Dummy mode voor testing zonder model
        return {
            "class_id": 2,
            "confidence": 0.87,
            "status": "nok"
        }

    # YOLO inference
    results = yolo_model(image)

    for result in results:
        top_class = result.probs.top1
        confidence = result.probs.top1conf.item()

        class_info = CLASS_INFO.get(top_class, {})

        return {
            "class_id": int(top_class),
            "confidence": float(confidence),
            "status": class_info.get("status", "unknown")
        }


def generate_suggestions(class_id):
    """Genereer suggesties op basis van classificatie"""
    class_info = CLASS_INFO.get(class_id, {})

    if class_info.get("status") == "ok":
        return []

    missing_items = class_info.get("missing", [])
    suggestions = []

    for item in missing_items:
        if item in SUGGESTIONS:
            suggestions.append({
                "item": item,
                "action": SUGGESTIONS[item]
            })

    return suggestions


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Werkplek Inspectie API",
        "version": "1.0.0",
        "model_loaded": yolo_model is not None
    }


@app.get("/api/classes")
async def get_classes():
    """Haal alle mogelijke classes op"""
    return {
        "classes": CLASS_INFO
    }


@app.get("/api/debug/model-info")
async def debug_model_info():
    """Debug endpoint - model informatie"""
    load_models()
    
    info = {
        "model_loaded": yolo_model != "dummy",
        "model_path": str(MODEL_PATH),
        "model_exists": MODEL_PATH.exists(),
        "expected_classes": len(CLASS_INFO),
        "class_mapping": {k: v["name"] for k, v in CLASS_INFO.items()}
    }
    
    if yolo_model != "dummy":
        # Get actual model class names
        try:
            info["model_classes"] = yolo_model.names
        except:
            info["model_classes"] = "Unable to fetch"
    
    return info


@app.post("/api/inspect")
async def inspect_workplace(
    file: UploadFile = File(...),
    blur_faces: bool = Form(True),
    device_id: str = Form("onbekend"),
    workplace_id: int = Form(None),
    request: Request = None
):
    """
    Inspecteer werkplek foto

    Stappen:
    1. Upload foto
    2. Blur gezichten (privacy)
    3. Classificeer: OK/NOK
    4. Als NOK: detecteer wat er mis is
    5. Geef suggesties

    Returns:
        Complete analyse resultaten
    """
    try:
        # Auto-detecteer device van User-Agent als geen device_id is opgegeven
        if device_id == "onbekend" and request:
            user_agent = request.headers.get("user-agent", "")
            ua_lower = user_agent.lower()

            # Parse specifieke device informatie uit User-Agent
            device_parts = []

            # Detecteer mobiele devices
            if "iphone" in ua_lower:
                device_parts.append("iPhone")
                # Probeer iOS versie te vinden
                if "os " in ua_lower:
                    try:
                        ios_version = ua_lower.split("os ")[1].split(" ")[0].replace("_", ".")
                        device_parts.append(f"iOS {ios_version}")
                    except:
                        pass
            elif "ipad" in ua_lower:
                device_parts.append("iPad")
                if "os " in ua_lower:
                    try:
                        ios_version = ua_lower.split("os ")[1].split(" ")[0].replace("_", ".")
                        device_parts.append(f"iOS {ios_version}")
                    except:
                        pass
            elif "android" in ua_lower:
                device_parts.append("Android")
                # Probeer Android versie te vinden
                if "android " in ua_lower:
                    try:
                        android_version = ua_lower.split("android ")[1].split(";")[0].strip()
                        device_parts.append(android_version)
                    except:
                        pass
                # Probeer device model te vinden (Samsung, Huawei, etc.)
                if "samsung" in ua_lower:
                    device_parts.append("Samsung")
                elif "huawei" in ua_lower:
                    device_parts.append("Huawei")
                elif "xiaomi" in ua_lower:
                    device_parts.append("Xiaomi")
                elif "oppo" in ua_lower:
                    device_parts.append("Oppo")
                elif "oneplus" in ua_lower:
                    device_parts.append("OnePlus")

            # Detecteer desktop OS
            elif "windows" in ua_lower:
                device_parts.append("Windows")
                if "windows nt 10" in ua_lower:
                    device_parts.append("10/11")
                elif "windows nt 6.3" in ua_lower:
                    device_parts.append("8.1")
                elif "windows nt 6.2" in ua_lower:
                    device_parts.append("8")
                elif "windows nt 6.1" in ua_lower:
                    device_parts.append("7")
            elif "mac os x" in ua_lower or "macintosh" in ua_lower:
                device_parts.append("macOS")
                if "mac os x " in ua_lower:
                    try:
                        mac_version = ua_lower.split("mac os x ")[1].split(")")[0].replace("_", ".")
                        device_parts.append(mac_version)
                    except:
                        pass
            elif "linux" in ua_lower:
                device_parts.append("Linux")
                if "ubuntu" in ua_lower:
                    device_parts.append("Ubuntu")

            # Detecteer browser
            if "chrome" in ua_lower and "edg" not in ua_lower:
                device_parts.append("Chrome")
            elif "edg" in ua_lower:
                device_parts.append("Edge")
            elif "firefox" in ua_lower:
                device_parts.append("Firefox")
            elif "safari" in ua_lower and "chrome" not in ua_lower:
                device_parts.append("Safari")

            # Combineer alle parts
            if device_parts:
                device_id = " - ".join(device_parts)
            else:
                # Fallback naar simpele detectie
                if "mobile" in ua_lower:
                    device_id = "Mobiel"
                elif "tablet" in ua_lower:
                    device_id = "Tablet"
                else:
                    device_id = "Desktop"

        # Lees uploaded file
        contents = await file.read()
        image = process_image_bytes(contents)

        if image is None:
            raise HTTPException(status_code=400, detail="Ongeldige afbeelding")

        # Stap 1: Check voor gezichten (privacy)
        face_count = 0
        processed_image = image

        if blur_faces:
            processed_image, face_count = blur_faces_in_image(image)

            # Als er gezichten zijn: AFKEUREN - geen analyse
            if face_count > 0:
                raise HTTPException(
                    status_code=403,
                    detail=f"Foto afgekeurd: {face_count} gezicht(en) gedetecteerd. Privacy vereist - verwijder personen uit het beeld."
                )

        # Stap 2: Analyseer met YOLO
        analysis = analyze_image(processed_image)

        # Stap 3: Haal class info op
        class_id = analysis["class_id"]
        class_info = CLASS_INFO.get(class_id, {})

        # Stap 4: Genereer suggesties
        suggestions = generate_suggestions(class_id)

        # Stap 5: Sla resultaat op
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"inspect_{timestamp}.jpg"
        output_path = UPLOAD_DIR / filename
        cv2.imwrite(str(output_path), processed_image)

        # Convert processed image naar base64 voor frontend
        img_base64 = image_to_base64(processed_image)

        # Stap 6: Sla analyse op in database voor later review
        print(f"DEBUG: workplace_id ontvangen = {workplace_id}, type = {type(workplace_id)}")
        analysis_data = {
            'timestamp': timestamp,
            'image_path': str(output_path),
            'predicted_class': str(class_id),
            'predicted_label': class_info.get("name", "Onbekend"),
            'confidence': analysis["confidence"],
            'status': analysis["status"].upper(),
            'missing_items': class_info.get("missing", []),
            'face_count': face_count,
            'device_id': device_id,
            'workplace_id': workplace_id  # Voeg workplace ID toe voor filtering
        }
        analysis_id = save_analysis(analysis_data)

        return {
            "success": True,
            "analysis_id": analysis_id,
            "timestamp": timestamp,
            "privacy": {
                "faces_detected": face_count,
                "faces_blurred": face_count if blur_faces else 0
            },
            "step1_classification": {
                "status": analysis["status"],
                "confidence": analysis["confidence"],
                "result": "OK" if analysis["status"] == "ok" else "NOK"
            },
            "step2_analysis": {
                "class_id": class_id,
                "class_name": class_info.get("name", "Onbekend"),
                "description": class_info.get("description", ""),
                "missing_items": class_info.get("missing", [])
            },
            "step3_suggestions": suggestions,
            "image": {
                "filename": filename,
                "base64": img_base64
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tijdens analyse: {str(e)}")


@app.post("/api/blur-preview")
async def blur_preview(file: UploadFile = File(...)):
    """
    Blur gezichten in foto en geef preview terug

    Args:
        file: Foto om te blurren

    Returns:
        Geblurde foto + aantal gezichten
    """
    try:
        contents = await file.read()
        image = process_image_bytes(contents)

        if image is None:
            raise HTTPException(status_code=400, detail="Ongeldige afbeelding")

        # Blur gezichten
        blurred_image, face_count = blur_faces_in_image(image)

        # Converteer naar base64
        _, buffer = cv2.imencode('.jpg', blurred_image)
        img_base64 = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode()}"

        return {
            "face_count": face_count,
            "blurred_image": img_base64,
            "has_faces": face_count > 0
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tijdens blur: {str(e)}")


@app.get("/api/history")
async def get_history(limit: int = 100, offset: int = 0, status: str = None, workplace_id: int = None):
    """
    Haal analyse geschiedenis op voor review

    Args:
        limit: Maximum aantal resultaten
        offset: Offset voor paginatie
        status: Filter op OK/NOK (optioneel)
        workplace_id: Filter op specifieke werkplek (optioneel)

    Returns:
        List van analyses met metadata
    """
    import sqlite3
    import json

    try:
        # Als workplace_id is meegegeven, filter daarop
        conn = sqlite3.connect('data/analyses.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM analyses"
        params = []
        conditions = []

        if workplace_id is not None:
            conditions.append("workplace_id = ?")
            params.append(workplace_id)

        if status:
            conditions.append("status = ?")
            params.append(status)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        analyses = []
        for row in rows:
            analysis = dict(row)
            analysis['missing_items'] = json.loads(analysis['missing_items']) if analysis['missing_items'] else []
            analyses.append(analysis)

        conn.close()

        # Get statistics
        from database import get_statistics
        stats = get_statistics()

        return {
            "analyses": analyses,
            "statistics": stats,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "count": len(analyses)
            },
            "success": True  # Voor consistency met andere endpoints
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tijdens ophalen geschiedenis: {str(e)}")


class CorrectionRequest(BaseModel):
    corrected_class: str
    corrected_label: str
    notes: str = None
    confidence_threshold: float = 70.0  # Dynamische drempel voor training candidates

@app.post("/api/correct/{analysis_id}")
async def correct_analysis(analysis_id: int, correction: CorrectionRequest):
    """
    Corrigeer een analyse voor model verbetering

    Args:
        analysis_id: ID van analyse
        correction: Request body met correctie gegevens + confidence threshold

    Returns:
        Success bericht
    """
    from database import update_correction

    try:
        update_correction(
            analysis_id,
            correction.corrected_class,
            correction.corrected_label,
            correction.notes,
            correction.confidence_threshold  # Geef dynamische drempel door
        )
        return {
            "success": True,
            "message": f"Analyse {analysis_id} gecorrigeerd naar {correction.corrected_label}",
            "analysis_id": analysis_id
        }
    except Exception as e:
        print(f"❌ ERROR in correct_analysis endpoint: {str(e)}")
        print(f"   Type: {type(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error tijdens correctie: {str(e)}")


@app.get("/api/export/csv")
async def export_csv():
    """
    Export alle analyses naar CSV voor verdere analyse

    Returns:
        Download link voor CSV bestand
    """
    from database import export_to_csv
    from fastapi.responses import FileResponse

    try:
        output_path = Path("data/analyses_export.csv")
        count = export_to_csv(output_path)

        return FileResponse(
            path=output_path,
            filename=f"analyses_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            media_type="text/csv"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tijdens export: {str(e)}")


@app.get("/api/accuracy-timeline")
async def get_accuracy_timeline():
    """
    Haal model accuracy over tijd op (per week)

    Returns:
        Tijdlijn met accuracy percentages per week
    """
    from database import get_accuracy_over_time

    try:
        timeline = get_accuracy_over_time()
        return {
            "success": True,
            "timeline": timeline,
            "count": len(timeline)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tijdens ophalen tijdlijn: {str(e)}")


@app.get("/api/training/statistics")
async def get_training_statistics():
    """
    Haal training pipeline statistieken op

    Returns:
        - unreviewed_count: Aantal analyses zonder beoordeling
        - training_queue_count: Aantal analyses klaar voor training export
        - exported_count: Aantal al geëxporteerde analyses
        - training_target: Doel aantal (200)
        - training_progress_percent: Percentage van doel bereikt
    """
    from database import get_training_statistics

    try:
        stats = get_training_statistics()
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tijdens ophalen training stats: {str(e)}")


@app.get("/api/training/candidates")
async def get_training_candidates_endpoint(confidence_threshold: float = 70.0):
    """
    Haal alle training candidates op (nog niet geëxporteerd)
    DYNAMISCH: Accepteert confidence threshold als query parameter

    Args:
        confidence_threshold: Drempel percentage voor lage confidence (default 70%)

    Returns:
        List van analyses die klaar zijn voor training export
        Dit zijn analyses met:
        - Foutieve voorspellingen (predicted != corrected)
        - Lage confidence (< threshold)
    """
    from database import get_training_candidates

    try:
        candidates = get_training_candidates(confidence_threshold)
        return {
            "success": True,
            "candidates": candidates,
            "count": len(candidates)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tijdens ophalen candidates: {str(e)}")


class ExportRequest(BaseModel):
    analysis_ids: list[int]
    export_name: str = None

@app.post("/api/training/export")
async def export_training_data(request: ExportRequest):
    """
    Exporteer geselecteerde analyses voor model retraining
    Organiseert foto's in mappen per corrected_class

    Args:
        analysis_ids: List van analysis IDs om te exporteren
        export_name: Optionele naam voor export (bijv. 'v2', 'batch1')

    Returns:
        Export statistieken + pad
    """
    from database import export_training_data as db_export_training_data
    from datetime import datetime

    try:
        if not request.analysis_ids:
            raise HTTPException(status_code=400, detail="Geen analyses geselecteerd")

        # Genereer export naam
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_name = request.export_name or f"export_{timestamp}"
        export_path = f"data/training_exports/{export_name}"

        # Export data
        result = db_export_training_data(request.analysis_ids, export_path)

        return {
            "success": True,
            "export": result,
            "message": f"{result['total_exported']} analyses geëxporteerd naar {result['export_path']}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tijdens export: {str(e)}")


@app.delete("/api/analysis/{analysis_id}")
async def delete_analysis(analysis_id: int):
    """
    Verwijder een analyse en de bijbehorende foto

    Args:
        analysis_id: ID van de analyse om te verwijderen

    Returns:
        Success bericht
    """
    from database import DATABASE_PATH
    import sqlite3
    import os

    try:
        # Haal eerst de image_path op
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT image_path FROM analyses WHERE id = ?", (analysis_id,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Analyse {analysis_id} niet gevonden")

        image_path = result[0]

        # Verwijder de analyse uit database
        cursor.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
        conn.commit()
        conn.close()

        # Verwijder de foto van disk
        if os.path.exists(image_path):
            os.remove(image_path)
            print(f"🗑️ Foto verwijderd: {image_path}")

        print(f"🗑️ Analyse {analysis_id} verwijderd")

        return {
            "success": True,
            "message": f"Analyse {analysis_id} verwijderd",
            "analysis_id": analysis_id
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ERROR bij verwijderen analyse {analysis_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error tijdens verwijderen: {str(e)}")


@app.get("/uploads/{filename}")
async def serve_upload(filename: str):
    """
    Serve uploaded images voor history pagina
    """
    from fastapi.responses import FileResponse

    file_path = UPLOAD_DIR / filename
    if file_path.exists():
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail="Afbeelding niet gevonden")


@app.post("/api/compare")
async def compare_images(
    reference: UploadFile = File(...),
    test: UploadFile = File(...)
):
    """
    Vergelijk test foto met referentie foto

    Args:
        reference: Master foto (SYSTEEM DATA)
        test: Huidige foto van gebruiker

    Returns:
        Vergelijkingsresultaten
    """
    try:
        # Lees beide afbeeldingen
        ref_contents = await reference.read()
        test_contents = await test.read()

        ref_image = process_image_bytes(ref_contents)
        test_image = process_image_bytes(test_contents)

        if ref_image is None or test_image is None:
            raise HTTPException(status_code=400, detail="Ongeldige afbeelding(en)")

        # Analyseer beide
        ref_analysis = analyze_image(ref_image)
        test_analysis = analyze_image(test_image)

        # Vergelijk
        match = ref_analysis["class_id"] == test_analysis["class_id"]

        return {
            "success": True,
            "match": match,
            "reference": {
                "class_id": ref_analysis["class_id"],
                "class_name": CLASS_INFO[ref_analysis["class_id"]]["name"],
                "confidence": ref_analysis["confidence"]
            },
            "test": {
                "class_id": test_analysis["class_id"],
                "class_name": CLASS_INFO[test_analysis["class_id"]]["name"],
                "confidence": test_analysis["confidence"]
            },
            "suggestions": generate_suggestions(test_analysis["class_id"]) if not match else []
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tijdens vergelijking: {str(e)}")


# ========================================
# WERKPLEK MANAGEMENT ENDPOINTS
# ========================================

@app.get("/api/workplaces")
async def get_workplaces(active_only: bool = True):
    """
    Haal alle werkplekken op

    Args:
        active_only: Alleen actieve werkplekken (default: True)

    Returns:
        List van werkplekken
    """
    from database import get_all_workplaces

    try:
        workplaces = get_all_workplaces(active_only=active_only)
        return {
            "success": True,
            "workplaces": workplaces,
            "count": len(workplaces)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/api/workplaces/{workplace_id}")
async def get_workplace_detail(workplace_id: int):
    """
    Haal specifieke werkplek op met alle details

    Args:
        workplace_id: ID van werkplek

    Returns:
        Werkplek details inclusief statistieken
    """
    from database import (get_workplace, get_training_dataset_stats,
                         get_models, get_dataset_exports)

    try:
        workplace = get_workplace(workplace_id)
        if not workplace:
            raise HTTPException(status_code=404, detail="Werkplek niet gevonden")

        # Haal statistieken op
        dataset_stats = get_training_dataset_stats(workplace_id)
        models = get_models(workplace_id)
        exports = get_dataset_exports(workplace_id)

        return {
            "success": True,
            "workplace": workplace,
            "dataset_stats": dataset_stats,
            "models": models,
            "exports": exports
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


class WorkplaceCreate(BaseModel):
    name: str
    description: str = None
    items: list[str]
    reference_photo: str = None


@app.post("/api/workplaces")
async def create_workplace_endpoint(workplace: WorkplaceCreate):
    """
    Maak nieuwe werkplek aan

    Args:
        workplace: Werkplek gegevens

    Returns:
        ID van nieuwe werkplek
    """
    from database import create_workplace

    try:
        workplace_id = create_workplace(
            name=workplace.name,
            description=workplace.description,
            items=workplace.items,
            reference_photo=workplace.reference_photo
        )

        if workplace_id is None:
            raise HTTPException(status_code=400, detail="Werkplek met deze naam bestaat al")

        return {
            "success": True,
            "workplace_id": workplace_id,
            "message": f"Werkplek '{workplace.name}' aangemaakt"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


class WorkplaceUpdate(BaseModel):
    name: str = None
    description: str = None
    items: list[str] = None
    reference_photo: str = None
    active: bool = None


@app.put("/api/workplaces/{workplace_id}")
async def update_workplace_endpoint(workplace_id: int, update: WorkplaceUpdate):
    """
    Update werkplek gegevens

    Args:
        workplace_id: ID van werkplek
        update: Te updaten velden
    """
    from database import update_workplace, get_workplace

    try:
        # Check of werkplek bestaat
        if not get_workplace(workplace_id):
            raise HTTPException(status_code=404, detail="Werkplek niet gevonden")

        update_workplace(
            workplace_id=workplace_id,
            name=update.name,
            description=update.description,
            items=update.items,
            reference_photo=update.reference_photo,
            active=update.active
        )

        return {
            "success": True,
            "message": f"Werkplek {workplace_id} bijgewerkt"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.delete("/api/workplaces/{workplace_id}")
async def delete_workplace_endpoint(workplace_id: int):
    """
    Verwijder werkplek

    Args:
        workplace_id: ID van werkplek
    """
    from database import delete_workplace, get_workplace

    try:
        # Check of werkplek bestaat
        if not get_workplace(workplace_id):
            raise HTTPException(status_code=404, detail="Werkplek niet gevonden")

        delete_workplace(workplace_id)

        return {
            "success": True,
            "message": f"Werkplek {workplace_id} verwijderd"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/api/workplaces/{workplace_id}/reference-photo")
async def upload_reference_photo(
    workplace_id: int,
    file: UploadFile = File(...)
):
    """
    Upload referentie foto voor werkplek

    Args:
        workplace_id: ID van werkplek
        file: Afbeelding bestand

    Returns:
        Pad naar opgeslagen referentie foto
    """
    from database import update_workplace, get_workplace

    try:
        # Check of werkplek bestaat
        workplace = get_workplace(workplace_id)
        if not workplace:
            raise HTTPException(status_code=404, detail="Werkplek niet gevonden")

        # Sla afbeelding op
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reference_{workplace_id}_{timestamp}_{file.filename}"
        reference_dir = Path(f"data/reference_photos")
        reference_dir.mkdir(parents=True, exist_ok=True)

        file_path = reference_dir / filename
        contents = await file.read()

        with open(file_path, "wb") as f:
            f.write(contents)

        # Update werkplek met referentie foto pad
        relative_path = f"/data/reference_photos/{filename}"
        update_workplace(
            workplace_id=workplace_id,
            reference_photo=relative_path
        )

        return {
            "success": True,
            "message": "Referentie foto geüpload",
            "reference_photo": relative_path
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ========================================
# TRAINING DATA MANAGEMENT ENDPOINTS
# ========================================

@app.post("/api/workplaces/{workplace_id}/training-images")
async def upload_training_image(
    workplace_id: int,
    file: UploadFile = File(...),
    label: str = Form(None),
    class_id: int = Form(None)
):
    """
    Upload training image voor werkplek

    Args:
        workplace_id: ID van werkplek
        file: Afbeelding bestand
        label: Label voor deze afbeelding
        class_id: Class ID (optioneel)

    Returns:
        Training image ID
    """
    from database import add_training_image, get_workplace

    try:
        # Check of werkplek bestaat
        if not get_workplace(workplace_id):
            raise HTTPException(status_code=404, detail="Werkplek niet gevonden")

        # Sla afbeelding op
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"training_{workplace_id}_{timestamp}_{file.filename}"
        training_dir = Path(f"data/training_images/workplace_{workplace_id}")
        training_dir.mkdir(parents=True, exist_ok=True)

        file_path = training_dir / filename
        contents = await file.read()

        with open(file_path, "wb") as f:
            f.write(contents)

        # Registreer in database (met relatieve path voor frontend)
        relative_path = str(file_path).replace("\\", "/")
        image_id = add_training_image(
            workplace_id=workplace_id,
            image_path=relative_path,
            label=label or "unlabeled",
            class_id=class_id,
            source="manual_upload"
        )

        return {
            "success": True,
            "image_id": image_id,
            "file_path": str(file_path),
            "message": "Training image uploaded"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/api/workplaces/{workplace_id}/training-images")
async def get_training_images_endpoint(workplace_id: int, validated_only: bool = False):
    """
    Haal training images op voor werkplek

    Args:
        workplace_id: ID van werkplek
        validated_only: Alleen gevalideerde images

    Returns:
        List van training images
    """
    from database import get_training_images, get_workplace

    try:
        # Check of werkplek bestaat
        if not get_workplace(workplace_id):
            raise HTTPException(status_code=404, detail="Werkplek niet gevonden")

        images = get_training_images(workplace_id, validated_only=validated_only)

        return {
            "success": True,
            "images": images,
            "count": len(images)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/api/workplaces/{workplace_id}/dataset-stats")
async def get_dataset_stats_endpoint(workplace_id: int):
    """
    Haal dataset statistieken op voor werkplek

    Args:
        workplace_id: ID van werkplek

    Returns:
        Dataset statistieken
    """
    from database import get_training_dataset_stats, get_workplace

    try:
        # Check of werkplek bestaat
        if not get_workplace(workplace_id):
            raise HTTPException(status_code=404, detail="Werkplek niet gevonden")

        stats = get_training_dataset_stats(workplace_id)

        return {
            "success": True,
            "stats": stats
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ========================================
# MODEL MANAGEMENT ENDPOINTS
# ========================================

@app.post("/api/workplaces/{workplace_id}/models")
async def upload_model(
    workplace_id: int,
    file: UploadFile = File(...),
    version: str = None,
    test_accuracy: float = None,
    notes: str = None
):
    """
    Upload getraind model voor werkplek

    Args:
        workplace_id: ID van werkplek
        file: Model bestand (.pt)
        version: Model versie
        test_accuracy: Test accuracy percentage
        notes: Notities over model

    Returns:
        Model ID
    """
    from database import register_model, get_workplace

    try:
        # Check of werkplek bestaat
        if not get_workplace(workplace_id):
            raise HTTPException(status_code=404, detail="Werkplek niet gevonden")

        # Check of het een .pt bestand is
        if not file.filename.endswith('.pt'):
            raise HTTPException(status_code=400, detail="Alleen .pt bestanden toegestaan")

        # Sla model op
        models_dir = Path(f"models/workplace_{workplace_id}")
        models_dir.mkdir(parents=True, exist_ok=True)

        if version is None:
            # Auto-genereer versie
            from database import get_models
            existing_models = get_models(workplace_id)
            version = f"v{len(existing_models) + 1}.0"

        model_filename = f"model_{version}.pt"
        model_path = models_dir / model_filename

        contents = await file.read()
        with open(model_path, "wb") as f:
            f.write(contents)

        # Registreer in database
        model_id = register_model(
            workplace_id=workplace_id,
            version=version,
            model_path=str(model_path),
            test_accuracy=test_accuracy,
            notes=notes
        )

        return {
            "success": True,
            "model_id": model_id,
            "version": version,
            "model_path": str(model_path),
            "message": f"Model {version} uploaded"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/api/workplaces/{workplace_id}/models")
async def get_models_endpoint(workplace_id: int, status: str = None):
    """
    Haal modellen op voor werkplek

    Args:
        workplace_id: ID van werkplek
        status: Filter op status (optioneel)

    Returns:
        List van modellen
    """
    from database import get_models, get_workplace

    try:
        # Check of werkplek bestaat
        if not get_workplace(workplace_id):
            raise HTTPException(status_code=404, detail="Werkplek niet gevonden")

        models = get_models(workplace_id, status=status)

        return {
            "success": True,
            "models": models,
            "count": len(models)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/api/models/{model_id}/activate")
async def activate_model_endpoint(model_id: int):
    """
    Activeer model (zet status naar 'active')

    Args:
        model_id: ID van model

    Returns:
        Success bericht
    """
    from database import activate_model

    try:
        activate_model(model_id)

        return {
            "success": True,
            "message": f"Model {model_id} geactiveerd"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ========================================
# DATASET EXPORT ENDPOINTS
# ========================================

@app.post("/api/workplaces/{workplace_id}/export-dataset")
async def export_dataset_for_training(workplace_id: int, train_split: float = 0.8):
    """
    Exporteer dataset in YOLO format voor training

    Args:
        workplace_id: ID van werkplek
        train_split: Percentage voor training (0.8 = 80% train, 20% val)

    Returns:
        ZIP file met dataset in YOLO format
    """
    from database import (get_workplace, get_training_images,
                         register_dataset_export)
    import zipfile
    import shutil
    import random
    from io import BytesIO

    try:
        # Check workplace
        workplace = get_workplace(workplace_id)
        if not workplace:
            raise HTTPException(status_code=404, detail="Werkplek niet gevonden")

        # Haal alle gevalideerde training images op
        images = get_training_images(workplace_id, validated_only=False)

        if len(images) == 0:
            raise HTTPException(status_code=400, detail="Geen training images gevonden")

        # Groepeer images per label
        images_by_label = {}
        for img in images:
            if img['label'] not in images_by_label:
                images_by_label[img['label']] = []
            images_by_label[img['label']].append(img)

        # Maak tijdelijke export directory
        export_dir = Path(f"data/temp_export_{workplace_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        export_dir.mkdir(parents=True, exist_ok=True)

        train_dir = export_dir / "train"
        val_dir = export_dir / "val"

        # Splits data per label en kopieer
        class_distribution = {}
        total_train = 0
        total_val = 0

        for label, label_images in images_by_label.items():
            # Shuffle
            random.shuffle(label_images)

            # Split
            split_idx = int(len(label_images) * train_split)
            train_images = label_images[:split_idx]
            val_images = label_images[split_idx:]

            # Maak label directories
            (train_dir / label).mkdir(parents=True, exist_ok=True)
            (val_dir / label).mkdir(parents=True, exist_ok=True)

            # Kopieer training images
            for img in train_images:
                src = Path(img['image_path'])
                if src.exists():
                    dst = train_dir / label / src.name
                    shutil.copy2(src, dst)
                    total_train += 1

            # Kopieer validation images
            for img in val_images:
                src = Path(img['image_path'])
                if src.exists():
                    dst = val_dir / label / src.name
                    shutil.copy2(src, dst)
                    total_val += 1

            class_distribution[label] = {
                'train': len(train_images),
                'val': len(val_images),
                'total': len(label_images)
            }

        # Maak data.yaml voor YOLO
        yaml_content = f"""# YOLOv8 Classification Dataset
# Werkplek: {workplace['name']}
# Gegenereerd: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

path: .
train: train
val: val

# Classes
names:
{chr(10).join([f"  {i}: {label}" for i, label in enumerate(sorted(images_by_label.keys()))])}

# Class mapping (alphabetically sorted)
# {json.dumps({i: label for i, label in enumerate(sorted(images_by_label.keys()))}, indent=2)}
"""

        yaml_path = export_dir / "data.yaml"
        with open(yaml_path, 'w') as f:
            f.write(yaml_content)

        # Maak README
        readme_content = f"""# Training Dataset - {workplace['name']}

## Dataset Informatie

- **Werkplek:** {workplace['name']}
- **Beschrijving:** {workplace['description'] or 'Geen beschrijving'}
- **Items:** {', '.join(workplace['items'])}
- **Totaal Images:** {len(images)}
- **Training Images:** {total_train}
- **Validation Images:** {total_val}
- **Split:** {int(train_split*100)}% train / {int((1-train_split)*100)}% val
- **Gegenereerd:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Class Distributie

{chr(10).join([f"- **{label}**: {info['total']} images (train: {info['train']}, val: {info['val']})" for label, info in class_distribution.items()])}

## Structuur

```
dataset/
├── data.yaml          # YOLO config
├── train/
│   ├── ok/
│   ├── nok_hamer_weg/
│   └── ...
└── val/
    ├── ok/
    ├── nok_hamer_weg/
    └── ...
```

## Training in Google Colab

```python
from ultralytics import YOLO

# Load a model
model = YOLO('yolov8n-cls.pt')  # pretrained model

# Train the model
results = model.train(
    data='.',
    epochs=50,
    imgsz=640,
    batch=16,
    name='werkplek_classifier'
)

# Validate
metrics = model.val()

# Export
model.export(format='torchscript')
```

## Download Trained Model

Na training, download het beste model:
- `runs/classify/werkplek_classifier/weights/best.pt`

Upload dit bestand in het Admin Dashboard onder "Modellen".
"""

        readme_path = export_dir / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)

        # Maak ZIP file
        zip_filename = f"dataset_{workplace['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        zip_path = Path("data/exports") / zip_filename
        zip_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in export_dir.rglob('*'):
                if file.is_file():
                    arcname = file.relative_to(export_dir)
                    zipf.write(file, arcname)

        # Registreer export in database
        register_dataset_export(
            workplace_id=workplace_id,
            export_path=str(zip_path),
            image_count=len(images),
            class_distribution=class_distribution
        )

        # Cleanup temp directory
        shutil.rmtree(export_dir)

        # Return ZIP file
        return FileResponse(
            path=zip_path,
            filename=zip_filename,
            media_type='application/zip',
            headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during export: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    print("="*60)
    print("🚀 Werkplek Inspectie API")
    print("="*60)
    print(f"Model pad: {MODEL_PATH}")
    print(f"Model bestaat: {MODEL_PATH.exists()}")
    print("="*60)

    # Initialiseer database
    init_database()

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
