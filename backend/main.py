"""
FastAPI Backend voor Werkplek Inspectie AI
Endpoints voor foto upload, analyse en resultaten
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
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
import json
import asyncio
from typing import AsyncGenerator

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
# Model Type: "classification" of "detection"
MODEL_TYPE = "classification"  # Wijzig naar "detection" voor object detection mode

# Model paths
CLASSIFICATION_MODEL_PATH = Path(__file__).parent / "models" / "werkplek_classifier (3).pt"
DETECTION_MODEL_PATH = Path(__file__).parent / "models" / "werkplek_detector (7).pt"

# Backwards compatibility: MODEL_PATH wijst naar actieve model
MODEL_PATH = CLASSIFICATION_MODEL_PATH if MODEL_TYPE == "classification" else DETECTION_MODEL_PATH

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# AI Models (lazy loading)
yolo_model = None
face_blurrer = None

# Class mapping for CLASSIFICATION models
# BINARY CLASSIFICATION (simpel en betrouwbaar):
# - Class 0: OK - Alle gereedschappen aanwezig
# - Class 1: NOK - Minimaal 1 gereedschap ontbreekt
#
# MULTI-CLASS CLASSIFICATION (legacy, gedetailleerd maar complex):
# YOLOv8 sorteert folders alfabetisch:
# 0_ok, 1_nok_alles_weg, 2_nok_hamer_weg, 3_nok_schaar_weg,
# 4_nok_schaar_sleutel_weg, 5_nok_sleutel_weg, 6_nok_alleen_sleutel

# Binary Classification mapping (RECOMMENDED)
CLASS_INFO_BINARY = {
    0: {"name": "OK", "status": "ok", "description": "Werkplek is compleet - alle gereedschappen aanwezig"},
    1: {"name": "NOK", "status": "nok", "description": "Werkplek incompleet - minimaal 1 gereedschap ontbreekt"}
}

# Multi-class Classification mapping (LEGACY - backwards compatibility)
CLASS_INFO_MULTICLASS = {
    0: {"name": "OK", "status": "ok", "description": "Werkplek is compleet en correct"},
    1: {"name": "NOK - Alles weg", "status": "nok", "description": "Alle gereedschappen ontbreken", "missing": ["hamer", "schaar", "sleutel"]},
    2: {"name": "NOK - Hamer weg", "status": "nok", "description": "Hamer ontbreekt", "missing": ["hamer"]},
    3: {"name": "NOK - Schaar weg", "status": "nok", "description": "Schaar ontbreekt", "missing": ["schaar"]},
    4: {"name": "NOK - Schaar en sleutel weg", "status": "nok", "description": "Schaar en sleutel ontbreken", "missing": ["schaar", "sleutel"]},
    5: {"name": "NOK - Sleutel weg", "status": "nok", "description": "Sleutel ontbreekt", "missing": ["sleutel"]},
    6: {"name": "NOK - Alleen sleutel", "status": "nok", "description": "Alleen sleutel aanwezig, hamer en schaar ontbreken", "missing": ["hamer", "schaar"]},
    7: {"name": "NOK - Hamer en sleutel weg", "status": "nok", "description": "Hamer en sleutel ontbreken, alleen schaar aanwezig", "missing": ["hamer", "sleutel"]}
}

# Default to multiclass for backwards compatibility with existing 8-class models
CLASS_INFO = CLASS_INFO_MULTICLASS

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


def analyze_image(image, model_path=None):
    """
    Analyseer afbeelding met YOLO classification model

    Args:
        image: Image te analyseren
        model_path: Optioneel custom model path (default gebruikt globaal MODEL_PATH)

    Returns:
        dict met resultaten
    """
    if model_path is None:
        model_path = MODEL_PATH

    # Load model (cached als het hetzelfde pad is)
    model = YOLO(str(model_path))

    # YOLO inference
    results = model(image)

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


@app.get("/api/model/type")
async def get_model_type():
    """Get current model type (classification or detection)"""
    return {
        "model_type": MODEL_TYPE,
        "classification_model": str(CLASSIFICATION_MODEL_PATH),
        "detection_model": str(DETECTION_MODEL_PATH)
    }


@app.post("/api/model/type")
async def set_model_type(model_type: str):
    """
    Switch between classification and detection models
    
    Args:
        model_type: "classification" or "detection"
    """
    global MODEL_TYPE, MODEL_PATH, yolo_model
    
    if model_type not in ["classification", "detection"]:
        raise HTTPException(
            status_code=400,
            detail="model_type must be 'classification' or 'detection'"
        )
    
    MODEL_TYPE = model_type
    MODEL_PATH = CLASSIFICATION_MODEL_PATH if model_type == "classification" else DETECTION_MODEL_PATH
    
    # Reload model
    yolo_model = None
    load_models()
    
    return {
        "success": True,
        "model_type": MODEL_TYPE,
        "model_path": str(MODEL_PATH)
    }


# Global progress tracking
analysis_progress = {}

async def send_progress_update(session_id: str, progress: int, message: str):
    """Send progress update voor een specifieke sessie"""
    analysis_progress[session_id] = {
        'progress': progress,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }

@app.get("/api/inspect/progress/{session_id}")
async def get_analysis_progress(session_id: str):
    """
    Server-Sent Events endpoint voor realtime progress updates
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # Wacht tot analyse klaar is of timeout (60 sec)
            timeout = 60
            start_time = datetime.now()

            while True:
                # Check timeout
                if (datetime.now() - start_time).seconds > timeout:
                    yield f"data: {json.dumps({'progress': 100, 'message': 'Timeout', 'done': True})}\n\n"
                    break

                # Check progress
                if session_id in analysis_progress:
                    data = analysis_progress[session_id]
                    progress = data['progress']
                    message = data['message']

                    # Send update
                    yield f"data: {json.dumps({'progress': progress, 'message': message, 'done': progress >= 100})}\n\n"

                    # Als klaar, stop streaming
                    if progress >= 100:
                        # Cleanup
                        del analysis_progress[session_id]
                        break

                # Wacht 100ms voor volgende check
                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            # Client heeft verbinding verbroken
            if session_id in analysis_progress:
                del analysis_progress[session_id]

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/api/inspect")
async def inspect_workplace(
    file: UploadFile = File(...),
    blur_faces: bool = Form(True),
    device_id: str = Form("onbekend"),
    workplace_id: int = Form(None),
    confidence_threshold: float = Form(0.25),  # Dynamische confidence threshold (0.0-1.0)
    session_id: str = Form(None),  # Voor progress tracking
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
        import time
        start_time = time.time()

        # Progress: Start
        if session_id:
            await send_progress_update(session_id, 5, "Foto ontvangen")

        print(f"[TIMING] Start analyse: {time.time() - start_time:.2f}s")
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
        if session_id:
            await send_progress_update(session_id, 15, "Foto verwerken")

        image = process_image_bytes(contents)

        if image is None:
            raise HTTPException(status_code=400, detail="Ongeldige afbeelding")

        # Stap 1: Check voor gezichten (privacy)
        if session_id:
            await send_progress_update(session_id, 25, "Privacy check")

        # Face detection met YuNet (modern DNN model - veel accurater dan Haar Cascade)
        face_count = 0
        processed_image = image

        if blur_faces:
            try:
                face_start = time.time()
                processed_image, face_count = blur_faces_in_image(image)
                print(f"[TIMING] Face detection: {time.time() - face_start:.2f}s")
                print(f"[INSPECT] Face detection result: {face_count} faces detected")

                # Als er gezichten zijn: AFKEUREN - geen analyse
                if face_count > 0:
                    raise HTTPException(
                        status_code=403,
                        detail="Foto afgekeurd: Persoon gedetecteerd. Privacy vereist - verwijder personen uit het beeld."
                    )
            except HTTPException:
                raise
            except Exception as blur_error:
                print(f"[INSPECT] Face detection failed: {str(blur_error)}, continuing without blur")
                processed_image = image
                face_count = 0

        # Stap 2: Bepaal welk model te gebruiken (per werkplek of globaal)
        if session_id:
            await send_progress_update(session_id, 35, "Model laden")

        from database import get_workplace_model

        workplace_model = get_workplace_model(workplace_id) if workplace_id else None

        if workplace_model and workplace_model['model_path']:
            # Gebruik werkplek-specifiek model
            model_type = workplace_model['model_type']
            model_path = Path(__file__).parent / workplace_model['model_path']
            model_version = workplace_model.get('model_version')  # Haal model versie op
            print(f"🏢 Werkplek {workplace_id}: gebruik {model_type} model ({model_path.name}), versie: {model_version}")
        else:
            # Fallback naar globale configuratie
            model_type = MODEL_TYPE
            model_path = MODEL_PATH
            model_version = None
            print(f"⚙️ Geen werkplek model, gebruik globaal: {model_type}")

        # Analyseer met het juiste model
        if session_id:
            await send_progress_update(session_id, 50, "Objecten detecteren")

        model_start = time.time()
        if model_type == "detection":
            analysis = analyze_image_detection(processed_image, model_path, confidence_threshold)
        else:
            analysis = analyze_image(processed_image, model_path)
        print(f"[TIMING] Model inference: {time.time() - model_start:.2f}s")

        if session_id:
            await send_progress_update(session_id, 80, "Resultaten verwerken")

        # Stap 3: Haal class info op
        class_id = analysis["class_id"]
        class_info = CLASS_INFO.get(class_id, {})

        # Stap 4: Genereer suggesties
        suggestions = generate_suggestions(class_id)

        # Stap 5: Sla resultaat op (altijd - wordt pas verwijderd na beoordeling)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"inspect_{timestamp}.jpg"
        output_path = UPLOAD_DIR / filename
        cv2.imwrite(str(output_path), processed_image)
        image_path = str(output_path)

        # Convert processed image naar base64 voor frontend
        img_base64 = image_to_base64(processed_image)

        # Stap 6: Sla analyse op in database voor later review
        print(f"DEBUG: workplace_id ontvangen = {workplace_id}, type = {type(workplace_id)}")
        # Voor classificatie: gebruik binair label (OK/NOK)
        # Voor detectie: gebruik volledige naam
        if model_type == "classification":
            # Binair: alleen OK of NOK
            predicted_label = "OK" if analysis["status"] == "ok" else "NOK"
        else:
            # Detectie: volledige naam
            predicted_label = class_info.get("name", "Onbekend")

        analysis_data = {
            'timestamp': timestamp,
            'image_path': image_path,
            'predicted_class': str(class_id),
            'predicted_label': predicted_label,
            'confidence': analysis["confidence"],
            'status': analysis["status"].upper(),
            'missing_items': class_info.get("missing", []),
            'face_count': face_count,
            'device_id': device_id,
            'workplace_id': workplace_id,  # Voeg workplace ID toe voor filtering
            'model_type': model_type,  # Gebruik het daadwerkelijk gebruikte model type
            'model_version': model_version  # Voeg model versie toe voor filtering
        }

        # Voeg detection counts toe als detection mode actief is
        if model_type == "detection" and "detected_objects" in analysis:
            detected = analysis["detected_objects"]
            analysis_data['detected_hamer'] = detected.get('hamer', 0)
            analysis_data['detected_schaar'] = detected.get('schaar', 0)
            analysis_data['detected_sleutel'] = detected.get('sleutel', 0)
            analysis_data['total_detections'] = sum(detected.values())

        try:
            analysis_id = save_analysis(analysis_data)
            print(f"[INSPECT] Analysis saved with ID: {analysis_id}")
        except Exception as db_error:
            print(f"[INSPECT] WARNING: Failed to save analysis to database: {str(db_error)}")
            import traceback
            traceback.print_exc()
            # Continue zonder database save - de analyse is wel gelukt
            analysis_id = None

        # Build response
        response = {
            "success": True,
            "analysis_id": analysis_id,
            "timestamp": timestamp,
            "model_type": model_type,  # Gebruik daadwerkelijk gebruikte model type
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

        # Add detection-specific data if using detection model
        if model_type == "detection":
            response["detection"] = {
                "detected_objects": analysis.get("detected_objects", {}),
                "bounding_boxes": analysis.get("bounding_boxes", []),
                "debug": analysis.get("debug", {})  # Include debug info
            }

        # Final progress update
        if session_id:
            await send_progress_update(session_id, 100, "Klaar")

        print(f"[TIMING] Total analyse time: {time.time() - start_time:.2f}s")
        return response

    except HTTPException:
        # Re-raise HTTPException (bijv. 403 voor face detection)
        raise
    except Exception as e:
        print(f"[INSPECT] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
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

        # Face detection met YuNet (modern DNN model - veel accurater dan Haar Cascade)
        try:
            blurred_image, face_count = blur_faces_in_image(image)
            print(f"[BLUR PREVIEW] Face detection result: {face_count} faces detected")

            # Als er gezichten zijn gedetecteerd, weiger de foto
            if face_count > 0:
                print(f"[BLUR PREVIEW] Blocking photo - {face_count} faces detected")
                raise HTTPException(
                    status_code=403,
                    detail="Privacy waarschuwing: Persoon gedetecteerd. Foto wordt niet getoond."
                )
        except HTTPException:
            raise
        except Exception as blur_error:
            print(f"[BLUR PREVIEW] Face detection failed: {str(blur_error)}, continuing without blur")
            blurred_image = image
            face_count = 0

        # Converteer naar base64
        _, buffer = cv2.imencode('.jpg', blurred_image)
        img_base64 = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode()}"

        return {
            "face_count": face_count,
            "blurred_image": img_base64,
            "has_faces": face_count > 0
        }

    except HTTPException:
        # Re-raise HTTPException
        raise
    except Exception as e:
        print(f"[BLUR PREVIEW] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error tijdens blur: {str(e)}")


@app.get("/api/history")
async def get_history(limit: int = 100, offset: int = 0, status: str = None, workplace_id: int = None, model_version: str = None):
    """
    Haal analyse geschiedenis op voor review

    Args:
        limit: Maximum aantal resultaten
        offset: Offset voor paginatie
        status: Filter op OK/NOK (optioneel)
        workplace_id: Filter op specifieke werkplek (optioneel)
        model_version: Filter op specifieke model versie (optioneel)

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

        # Filter out analyses waar foto al naar training data is verplaatst
        conditions.append("image_path IS NOT NULL")

        if workplace_id is not None:
            conditions.append("workplace_id = ?")
            params.append(workplace_id)

        if model_version is not None:
            conditions.append("model_version = ?")
            params.append(model_version)

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
    confidence_threshold: float = None  # Confidence threshold voor detection models (0.0-1.0)


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
            active=update.active,
            confidence_threshold=update.confidence_threshold
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


@app.get("/api/workplaces/{workplace_id}/detect-whiteboard")
async def detect_whiteboard_in_reference(workplace_id: int):
    """
    Detecteer whiteboard positie in referentie foto voor ghost overlay

    Args:
        workplace_id: ID van werkplek

    Returns:
        Bounding box coordinaten van gedetecteerd whiteboard
    """
    from database import get_workplace

    try:
        # Haal werkplek op
        workplace = get_workplace(workplace_id)
        if not workplace:
            raise HTTPException(status_code=404, detail="Werkplek niet gevonden")

        reference_photo = workplace.get("reference_photo")
        if not reference_photo:
            return {
                "success": False,
                "message": "Geen referentie foto gevonden"
            }

        # Lees referentie foto
        reference_path = Path(f"data/reference_photos/{reference_photo.split('/')[-1]}")
        if not reference_path.exists():
            return {
                "success": False,
                "message": "Referentie foto bestand niet gevonden"
            }

        # Load image
        image = cv2.imread(str(reference_path))
        if image is None:
            return {
                "success": False,
                "message": "Kon referentie foto niet laden"
            }

        # Get image dimensions
        height, width = image.shape[:2]

        # Gebruik detection model om whiteboard te vinden
        # Check welk model voor deze werkplek actief is
        from database import get_active_model
        active_model = get_active_model(workplace_id)

        if active_model and active_model.get("model_path"):
            model_path = Path(active_model["model_path"])
        else:
            # Fallback naar globaal detection model
            model_path = DETECTION_MODEL_PATH

        if not model_path.exists():
            return {
                "success": False,
                "message": "Geen detection model beschikbaar"
            }

        # Detecteer objecten
        detection_results = analyze_image_detection(
            image,
            model_path=model_path,
            confidence_threshold=0.25
        )

        # Zoek naar whiteboard/hamer in bounding boxes
        whiteboard_box = None
        for bbox in detection_results.get("bounding_boxes", []):
            # In sommige modellen is whiteboard 'hamer' genoemd
            if bbox["object"] in ["whiteboard", "hamer"]:
                # Neem hoogste confidence whiteboard
                if whiteboard_box is None or bbox["confidence"] > whiteboard_box["confidence"]:
                    whiteboard_box = bbox

        if whiteboard_box:
            # Converteer naar percentages voor responsive overlay
            bbox = whiteboard_box["bbox"]
            return {
                "success": True,
                "whiteboard": {
                    "x1": bbox["x1"] / width,  # Percentage van breedte
                    "y1": bbox["y1"] / height,  # Percentage van hoogte
                    "x2": bbox["x2"] / width,
                    "y2": bbox["y2"] / height,
                    "confidence": whiteboard_box["confidence"]
                }
            }
        else:
            return {
                "success": False,
                "message": "Geen whiteboard gedetecteerd in referentie foto"
            }

    except Exception as e:
        import traceback
        print(f"Error detecting whiteboard: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/api/workplaces/{workplace_id}/whiteboard-region")
async def save_whiteboard_region(workplace_id: int, region: dict):
    """
    Sla whiteboard region op voor ghost overlay

    Args:
        workplace_id: ID van werkplek
        region: Dict met x1, y1, x2, y2 (percentages 0-1)

    Returns:
        Success status
    """
    from database import get_workplace, update_workplace

    try:
        # Check of werkplek bestaat
        workplace = get_workplace(workplace_id)
        if not workplace:
            raise HTTPException(status_code=404, detail="Werkplek niet gevonden")

        # Valideer region data
        if not all(key in region for key in ['x1', 'y1', 'x2', 'y2']):
            raise HTTPException(status_code=400, detail="Region moet x1, y1, x2, y2 bevatten")

        # Valideer dat waarden tussen 0 en 1 zijn
        for key in ['x1', 'y1', 'x2', 'y2']:
            if not 0 <= region[key] <= 1:
                raise HTTPException(status_code=400, detail=f"{key} moet tussen 0 en 1 zijn")

        # Update werkplek
        update_workplace(
            workplace_id=workplace_id,
            whiteboard_region=region
        )

        return {
            "success": True,
            "message": "Whiteboard region opgeslagen",
            "region": region
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


@app.post("/api/workplaces/{workplace_id}/training-images/from-analysis")
async def add_analysis_to_training(workplace_id: int, analysis_id: int = Form(...), label: str = Form(...)):
    """
    Verplaats een analyse foto naar trainingsdata

    Args:
        workplace_id: ID van werkplek
        analysis_id: ID van analyse om te verplaatsen
        label: Label voor de training image

    Returns:
        Success bericht
    """
    from database import get_workplace, DATABASE_PATH
    import sqlite3
    import shutil

    try:
        # Check of werkplek bestaat
        workplace = get_workplace(workplace_id)
        if not workplace:
            raise HTTPException(status_code=404, detail="Werkplek niet gevonden")

        # Haal analyse op
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,))
        analysis = cursor.fetchone()
        conn.close()

        if not analysis:
            raise HTTPException(status_code=404, detail="Analyse niet gevonden")

        analysis_dict = dict(analysis)
        image_path = analysis_dict.get('image_path')

        if not image_path or not Path(image_path).exists():
            raise HTTPException(status_code=404, detail="Foto niet gevonden")

        # Gebruik workplace_id uit analyse als die bestaat, anders gebruik URL parameter
        analysis_workplace_id = analysis_dict.get('workplace_id') or workplace_id

        # Kopieer foto naar training folder
        training_dir = Path("data/training_images") / str(analysis_workplace_id)
        training_dir.mkdir(parents=True, exist_ok=True)

        # Genereer unieke naam
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_name = Path(image_path).stem
        new_filename = f"{label}_{timestamp}_{original_name}.jpg"
        new_path = training_dir / new_filename

        # Verplaats bestand naar training folder
        shutil.move(image_path, new_path)

        # Update analyse record:
        # - Update image_path naar nieuwe locatie
        # - Set corrected_label naar het label (zodat het een training candidate wordt)
        # - Mark as training_candidate
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE analyses
            SET image_path = ?,
                corrected_label = ?,
                corrected_class = predicted_class,
                training_candidate = 1
            WHERE id = ?
        """, (str(new_path), label, analysis_id))
        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": f"Foto verplaatst naar trainingsdata",
            "analysis_id": analysis_id,
            "path": str(new_path)
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


@app.put("/api/workplaces/{workplace_id}/training-images/{image_id}")
async def update_training_image_endpoint(
    workplace_id: int,
    image_id: int,
    label: str = Form(...)
):
    """
    Update label van een training image

    Args:
        workplace_id: ID van werkplek
        image_id: ID van training image
        label: Nieuwe label

    Returns:
        Success message
    """
    from database import update_training_image_label, get_workplace

    try:
        # Check of werkplek bestaat
        if not get_workplace(workplace_id):
            raise HTTPException(status_code=404, detail="Werkplek niet gevonden")

        success = update_training_image_label(image_id, label)

        if not success:
            raise HTTPException(status_code=404, detail="Training image niet gevonden")

        return {
            "success": True,
            "message": "Label succesvol bijgewerkt"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.delete("/api/workplaces/{workplace_id}/training-images/{image_id}")
async def delete_training_image_endpoint(workplace_id: int, image_id: int):
    """
    Verwijder een training image

    Args:
        workplace_id: ID van werkplek
        image_id: ID van training image

    Returns:
        Success message
    """
    from database import delete_training_image, get_workplace
    import os

    try:
        # Check of werkplek bestaat
        if not get_workplace(workplace_id):
            raise HTTPException(status_code=404, detail="Werkplek niet gevonden")

        success, image_path = delete_training_image(image_id)

        if not success:
            raise HTTPException(status_code=404, detail="Training image niet gevonden")

        # Verwijder fysiek bestand als het bestaat
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception as e:
                print(f"Warning: Could not delete file {image_path}: {e}")

        return {
            "success": True,
            "message": "Training image succesvol verwijderd"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/api/workplaces/{workplace_id}/model-versions")
async def get_model_versions_endpoint(workplace_id: int):
    """
    Haal beschikbare model versies op voor een werkplek

    Returns lijst van unieke model versies die data hebben gegenereerd
    """
    import sqlite3
    from database import DATABASE_PATH, get_workplace

    try:
        if not get_workplace(workplace_id):
            raise HTTPException(status_code=404, detail="Werkplek niet gevonden")

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT model_version
            FROM analyses
            WHERE workplace_id = ?
            AND model_version IS NOT NULL
            ORDER BY model_version DESC
        """, (workplace_id,))

        versions = [row[0] for row in cursor.fetchall()]
        conn.close()

        return {
            "success": True,
            "versions": versions
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/api/workplaces/{workplace_id}/dataset-stats")
async def get_dataset_stats_endpoint(workplace_id: int, model_version: str = None):
    """
    Haal dataset statistieken op voor werkplek

    Args:
        workplace_id: ID van werkplek
        model_version: Optioneel - filter op specifieke model versie

    Returns:
        Dataset statistieken
    """
    from database import get_training_dataset_stats, get_workplace

    try:
        # Check of werkplek bestaat
        if not get_workplace(workplace_id):
            raise HTTPException(status_code=404, detail="Werkplek niet gevonden")

        stats = get_training_dataset_stats(workplace_id, model_version=model_version)

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
    version: str = Form(None),
    test_accuracy: float = Form(None),
    notes: str = Form(None),
    model_type: str = Form('classification')
):
    """
    Upload getraind model voor werkplek

    Args:
        workplace_id: ID van werkplek
        file: Model bestand (.pt)
        version: Model versie
        test_accuracy: Test accuracy percentage
        notes: Notities over model
        model_type: Type model ('classification' of 'detection')

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

        # Valideer model_type
        if model_type not in ['classification', 'detection']:
            raise HTTPException(status_code=400, detail="Model type moet 'classification' of 'detection' zijn")

        # Haal werkplek info op voor unieke naming
        workplace = get_workplace(workplace_id)
        workplace_name_clean = workplace['name'].lower().replace(' ', '_').replace('-', '_')

        # Sla model op met werkplek naam in filename
        models_dir = Path(f"models/workplace_{workplace_id}")
        models_dir.mkdir(parents=True, exist_ok=True)

        if version is None:
            # Auto-genereer versie
            from database import get_models
            existing_models = get_models(workplace_id)
            version = f"v{len(existing_models) + 1}.0"

        # Model filename bevat: werkplek_naam_versie_type.pt
        # Version kan nu de originele bestandsnaam zijn (zonder .pt)
        model_filename = f"{workplace_name_clean}_{version}_{model_type}.pt"
        model_path = models_dir / model_filename

        contents = await file.read()
        with open(model_path, "wb") as f:
            f.write(contents)

        # Registreer in database
        model_id = register_model(
            workplace_id=workplace_id,
            version=version,
            model_path=str(model_path),
            model_type=model_type,
            test_accuracy=test_accuracy,
            notes=notes
        )

        return {
            "success": True,
            "model_id": model_id,
            "version": version,
            "model_path": str(model_path),
            "model_type": model_type,
            "message": f"Model {version} ({model_type}) uploaded"
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


@app.delete("/api/models/{model_id}")
async def delete_model_endpoint(model_id: int):
    """
    Verwijder model (alleen als niet actief)

    Args:
        model_id: ID van model

    Returns:
        Success bericht
    """
    import sqlite3
    import os
    from pathlib import Path

    try:
        conn = sqlite3.connect('data/analyses.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Haal model info op
        cursor.execute("SELECT * FROM models WHERE id = ?", (model_id,))
        model = cursor.fetchone()

        if not model:
            conn.close()
            raise HTTPException(status_code=404, detail="Model niet gevonden")

        # Check of model actief is
        if model['status'] == 'active':
            conn.close()
            raise HTTPException(status_code=400, detail="Kan actief model niet verwijderen. Deactiveer het model eerst.")

        # Verwijder fysiek bestand
        model_path = Path(model['model_path'])
        if model_path.exists():
            os.remove(model_path)

        # Verwijder uit database
        cursor.execute("DELETE FROM models WHERE id = ?", (model_id,))
        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": f"Model {model_id} verwijderd"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/api/workplaces/{workplace_id}/set-model")
async def set_workplace_model_endpoint(
    workplace_id: int,
    model_type: str,
    model_path: str
):
    """
    Stel actief model in voor een werkplek

    Args:
        workplace_id: ID van werkplek
        model_type: 'classification' of 'detection'
        model_path: Relatief pad naar model (bijv. 'models/werkplek_detector (7).pt')

    Returns:
        Success bericht
    """
    from database import set_workplace_model, get_workplace

    try:
        # Check of werkplek bestaat
        workplace = get_workplace(workplace_id)
        if not workplace:
            raise HTTPException(status_code=404, detail="Werkplek niet gevonden")

        # Valideer model type
        if model_type not in ["classification", "detection"]:
            raise HTTPException(
                status_code=400,
                detail="model_type moet 'classification' of 'detection' zijn"
            )

        # Check of model bestaat
        full_path = Path(__file__).parent / model_path
        if not full_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Model niet gevonden: {model_path}"
            )

        # Sla op in database
        set_workplace_model(workplace_id, model_type, model_path)

        return {
            "success": True,
            "message": f"Model ingesteld voor werkplek {workplace['name']}",
            "model_type": model_type,
            "model_path": model_path
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/api/workplaces/{workplace_id}/get-model")
async def get_workplace_model_endpoint(workplace_id: int):
    """
    Haal actief model configuratie op voor een werkplek

    Args:
        workplace_id: ID van werkplek

    Returns:
        Model configuratie of None
    """
    from database import get_workplace_model as db_get_workplace_model

    try:
        model_config = db_get_workplace_model(workplace_id)

        return {
            "success": True,
            "model_config": model_config
        }

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

        # Maak tijdelijke export directory (alleen images, geen classificatie structuur)
        export_dir = Path(f"data/temp_export_{workplace_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        images_dir = export_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        # Kopieer alle images (zonder classificatie structuur of train/val split)
        total_exported = 0
        for img in images:
            src = Path(img['image_path'])
            if src.exists():
                dst = images_dir / src.name
                shutil.copy2(src, dst)
                total_exported += 1

        # Statistieken voor README (optioneel, alleen ter info)
        label_counts = {}
        for img in images:
            label = img.get('label', 'unknown')
            if label not in label_counts:
                label_counts[label] = 0
            label_counts[label] += 1

        # Maak README (geen YAML - annotaties gebeuren buiten de app)
        readme_content = f"""# Training Dataset - {workplace['name']}

## Dataset Informatie

- **Werkplek:** {workplace['name']}
- **Beschrijving:** {workplace['description'] or 'Geen beschrijving'}
- **Items:** {', '.join(workplace['items'])}
- **Totaal Images:** {total_exported}
- **Gegenereerd:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Label Distributie (ter info)

{chr(10).join([f"- **{label}**: {count} images" for label, count in sorted(label_counts.items())])}

## Structuur

```
dataset/
└── images/
    ├── inspect_20251226_180127.jpg
    ├── inspect_20251226_203702.jpg
    └── ...
```

## Annotatie Workflow

Deze export bevat **alleen images** zonder annotaties.
De images zijn klaar voor:
1. Import in Label Studio of andere annotatie tool
2. Handmatige bounding box annotatie
3. Export naar YOLO detection format
4. Training van object detection model

## Volgende Stappen

1. Upload images naar je annotatie tool (bijv. Label Studio)
2. Annoteer objecten met bounding boxes:
   - hamer (class 0)
   - schaar (class 1)
   - sleutel (class 2)
3. Exporteer annotaties in YOLO detection format
4. Train model met YOLOv8/v11 detection

```python
from ultralytics import YOLO

# Load detection model
model = YOLO('yolo11n.pt')  # pretrained detection model

# Train (na annotatie)
results = model.train(
    data='path/to/data.yaml',  # YOLO config met annotaties
    epochs=100,
    imgsz=640,
    batch=16,
    name='werkplek_detector'
)
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
            image_count=total_exported,
            class_distribution=label_counts
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

    # Start backend met HTTP
    print(f"Starting backend with HTTP on http://0.0.0.0:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
def analyze_image_detection(image, model_path=None, confidence_threshold=0.25):
    """
    Analyseer afbeelding met YOLO Object Detection model
    Telt objecten (schaar, sleutel, whiteboard) en bepaalt status

    Args:
        image: Image te analyseren
        model_path: Optioneel custom model path (default gebruikt globaal DETECTION_MODEL_PATH)
        confidence_threshold: Minimale confidence voor detecties (default 0.25 = 25%)

    Detection model classes:
    0: hamer
    1: schaar
    2: sleutel

    Returns:
        dict met resultaten inclusief bounding boxes
    """
    if model_path is None:
        model_path = DETECTION_MODEL_PATH

    # Load model (cached als het hetzelfde pad is)
    model = YOLO(str(model_path))

    # Haal class names uit het model zelf (dynamisch!)
    model_class_names = model.names  # Dict: {0: 'hamer', 1: 'schaar', 2: 'sleutel'}
    print(f"📋 Model class names: {model_class_names}")

    # Normaliseer class names naar lowercase voor consistentie
    # En map 'whiteboard' → 'hamer' voor backwards compatibility
    def normalize_class_name(name):
        name_lower = name.lower()
        if name_lower == 'whiteboard':
            return 'hamer'
        return name_lower

    # YOLO object detection inference met dynamische confidence threshold
    # confidence_threshold: alleen detecties boven deze drempel accepteren
    # iou=0.7 means less aggressive NMS (allows more overlapping boxes)
    print(f"🎯 Detection confidence threshold: {confidence_threshold*100:.0f}%")
    results = model(image, conf=confidence_threshold, iou=0.7, max_det=100)

    # Tel gedetecteerde objecten (dynamisch op basis van model.names)
    object_counts = {"hamer": 0, "schaar": 0, "sleutel": 0}
    max_confidence = 0.0
    bounding_boxes = []

    print(f"🔍 Detection: {len(results)} result(s)")
    for result in results:
        if result.boxes is not None:
            print(f"  📦 Found {len(result.boxes)} boxes")
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                # Get bounding box coordinates (xyxy format)
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                # Haal object naam uit MODEL (niet hardcoded!)
                if class_id in model_class_names:
                    raw_name = model_class_names[class_id]
                    object_name = normalize_class_name(raw_name)

                    # Tel alleen bekende objecten
                    if object_name in object_counts:
                        object_counts[object_name] += 1

                        print(f"    ✓ Detected: {object_name} (model class: {raw_name}, confidence: {confidence:.2f})")
                        bounding_boxes.append({
                            "object": object_name,
                            "confidence": confidence,
                            "bbox": {
                                "x1": int(x1),
                                "y1": int(y1),
                                "x2": int(x2),
                                "y2": int(y2)
                            }
                        })
                    else:
                        print(f"    ⚠️ Onbekend object: {object_name} (class_id: {class_id})")
                else:
                    print(f"    ? Unknown class_id: {class_id}")

                max_confidence = max(max_confidence, confidence)

    # Bepaal status op basis van aanwezige objecten
    hamer_present = object_counts["hamer"] > 0
    schaar_present = object_counts["schaar"] > 0
    sleutel_present = object_counts["sleutel"] > 0

    # Map naar class_id
    if hamer_present and schaar_present and sleutel_present:
        class_id = 0  # OK - alles aanwezig
    elif not hamer_present and not schaar_present and not sleutel_present:
        class_id = 1  # NOK alles weg
    elif not hamer_present and schaar_present and sleutel_present:
        class_id = 2  # NOK hamer weg
    elif hamer_present and not schaar_present and sleutel_present:
        class_id = 3  # NOK schaar weg
    elif hamer_present and not schaar_present and not sleutel_present:
        class_id = 4  # NOK schaar en sleutel weg
    elif hamer_present and schaar_present and not sleutel_present:
        class_id = 5  # NOK sleutel weg
    elif not hamer_present and not schaar_present and sleutel_present:
        class_id = 6  # NOK alleen sleutel (hamer en schaar weg)
    elif not hamer_present and schaar_present and not sleutel_present:
        class_id = 7  # NOK hamer en sleutel weg (alleen schaar)
    else:
        # Fallback voor onverwachte combinaties
        class_id = 1

    # Detection models gebruiken altijd multiclass mapping (class 0-7)
    class_info = CLASS_INFO_MULTICLASS.get(class_id, {})

    print(f"📊 Final counts: hamer={object_counts['hamer']}, schaar={object_counts['schaar']}, sleutel={object_counts['sleutel']}")
    print(f"📊 Total bounding boxes: {len(bounding_boxes)}")

    # Debug info for frontend
    debug_info = {
        "total_boxes_detected": len(bounding_boxes),
        "raw_counts": object_counts.copy(),
        "detections": [f"{b['object']}({b['confidence']:.2f})" for b in bounding_boxes]
    }

    result = {
        "class_id": int(class_id),
        "confidence": float(max_confidence) if max_confidence > 0 else 0.5,
        "status": class_info.get("status", "unknown"),
        "detected_objects": object_counts,
        "bounding_boxes": bounding_boxes,
        "debug": debug_info  # Temporary debug info
    }

    return result

