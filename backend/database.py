"""
Database module voor analyse logging - PostgreSQL versie
Slaat alle analyses op voor latere review en model verbetering
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path
import json

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """Maak database connectie met RealDictCursor"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


# NOTE: init_database() removed - PostgreSQL schema already exists!
# Schema is managed externally and has different field names than SQLite
# DO NOT recreate or alter tables - this will break existing data!


def save_analysis(data):
    """
    Sla analyse resultaat op in database

    PostgreSQL Schema Mapping:
    - status -> result
    - predicted_class/predicted_label -> model_prediction
    - missing_items -> metadata (jsonb)

    Args:
        data: Dict met analyse gegevens

    Returns:
        ID van opgeslagen analyse
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # FIX #2: Confidence NULL prevention - ensure confidence is never NULL
    confidence = data.get('confidence')
    if confidence is None:
        confidence = 0.0

    # Map frontend fields to PostgreSQL fields
    # Frontend sends: status, predicted_class, predicted_label
    # PostgreSQL has: result, model_prediction
    result = data.get('status', 'OK')  # status -> result
    model_prediction = data.get('predicted_label') or data.get('predicted_class', 'unknown')

    # Build metadata JSON from missing_items and other detection info
    metadata = {}
    if 'missing_items' in data:
        metadata['missing_items'] = data['missing_items']
    if 'detected_hamer' in data:
        metadata['detected_hamer'] = data['detected_hamer']
    if 'detected_schaar' in data:
        metadata['detected_schaar'] = data['detected_schaar']
    if 'detected_sleutel' in data:
        metadata['detected_sleutel'] = data['detected_sleutel']
    if 'total_detections' in data:
        metadata['total_detections'] = data['total_detections']
    if 'model_type' in data:
        metadata['model_type'] = data['model_type']
    if 'device_id' in data:
        metadata['device_id'] = data['device_id']
    if 'camera_info' in data and data['camera_info']:
        metadata['camera_info'] = data['camera_info']

    # Determine is_correct (None initially, will be set by user correction)
    is_correct = None

    # Calculate processing_time if not provided
    processing_time = data.get('processing_time', 0.0)

    cursor.execute("""
        INSERT INTO analyses
        (workplace_id, user_id, timestamp, image_path, result, confidence,
         model_prediction, is_correct, processing_time, metadata, model_version)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
        RETURNING id
    """, (
        data.get('workplace_id', None),
        data.get('user_id', None),
        data.get('timestamp', datetime.now()),
        data.get('image_path'),
        result,  # status -> result
        confidence,  # FIX #2: Never NULL
        model_prediction,  # predicted_label -> model_prediction
        is_correct,  # Will be set on user correction
        processing_time,
        json.dumps(metadata) if metadata else None,  # FIX #4: JSONB casting
        data.get('model_version', None)
    ))

    analysis_id = cursor.fetchone()['id']
    conn.commit()
    conn.close()

    return analysis_id


def get_all_analyses(limit=100, offset=0, filter_status=None):
    """
    Haal alle analyses op

    PostgreSQL -> Frontend Field Mapping:
    - result -> status (frontend expects 'status')
    - model_prediction -> predicted_label AND predicted_class
    - user_correction -> corrected_label
    - metadata -> extract missing_items and detection counts

    Args:
        limit: Maximum aantal resultaten
        offset: Offset voor paginatie
        filter_status: Filter op OK/NOK (optioneel)

    Returns:
        List van analyse dicts with frontend-compatible field names
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM analyses"
    params = []

    if filter_status:
        # Map frontend filter to PostgreSQL field
        query += " WHERE result = %s"
        params.append(filter_status)

    query += " ORDER BY timestamp DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    cursor.execute(query, params)
    rows = cursor.fetchall()

    analyses = []
    for row in rows:
        analysis = dict(row)

        # CRITICAL: Map PostgreSQL fields to frontend expected fields
        analysis['status'] = analysis.get('result')  # result -> status
        analysis['predicted_label'] = analysis.get('model_prediction')  # model_prediction -> predicted_label
        analysis['predicted_class'] = analysis.get('model_prediction')  # Also set predicted_class
        analysis['corrected_label'] = analysis.get('user_correction')  # user_correction -> corrected_label
        analysis['created_at'] = analysis.get('timestamp')  # timestamp -> created_at for frontend

        # Extract metadata fields for frontend compatibility
        # FIX #5: JSON parsing error handling
        metadata = analysis.get('metadata', {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = {}
        elif metadata is None:
            metadata = {}

        # Extract fields from metadata
        analysis['missing_items'] = metadata.get('missing_items', [])
        analysis['detected_hamer'] = metadata.get('detected_hamer', 0)
        analysis['detected_schaar'] = metadata.get('detected_schaar', 0)
        analysis['detected_sleutel'] = metadata.get('detected_sleutel', 0)
        analysis['total_detections'] = metadata.get('total_detections', 0)
        analysis['model_type'] = metadata.get('model_type', 'classification')

        # FIX #6: Path separator fixes - Convert Windows backslashes to forward slashes for frontend
        if analysis.get('image_path'):
            analysis['image_path'] = analysis['image_path'].replace('\\', '/')

        analyses.append(analysis)

    conn.close()
    return analyses


def update_correction(analysis_id, corrected_class, corrected_label, notes=None, confidence_threshold=70.0):
    """
    Update analyse met correctie (voor model verbetering)

    PostgreSQL Schema:
    - Uses user_correction field (NOT corrected_label)
    - Uses is_correct boolean field
    - model_prediction stays unchanged for accuracy tracking

    Args:
        analysis_id: ID van analyse
        corrected_class: Correcte class (ignored, using corrected_label)
        corrected_label: Correct label
        notes: Optionele notities (stored in metadata)
        confidence_threshold: Dynamische drempel voor lage confidence (default 70%)
    """
    import os
    conn = get_db_connection()
    cursor = conn.cursor()

    # Haal eerste de originele analyse op
    cursor.execute("""
        SELECT model_prediction, confidence, image_path, metadata
        FROM analyses
        WHERE id = %s
    """, (analysis_id,))

    result = cursor.fetchone()
    if not result:
        conn.close()
        raise ValueError(f"Analyse met ID {analysis_id} niet gevonden")

    model_prediction = result['model_prediction']
    confidence = result['confidence'] or 0.0
    image_path = result['image_path']

    # Parse existing metadata
    # FIX #5: JSON parsing error handling
    metadata = result.get('metadata', {})
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except (json.JSONDecodeError, TypeError):
            metadata = {}
    elif metadata is None:
        metadata = {}

    # Determine if prediction is correct
    is_correct = (model_prediction == corrected_label)

    # Bepaal of dit een training candidate is
    threshold_decimal = confidence_threshold / 100.0
    is_low_confidence = (confidence < threshold_decimal)
    has_notes = notes and notes.strip() and notes.strip() != "{}"

    # Store correction info in metadata
    if notes:
        try:
            notes_dict = json.loads(notes) if isinstance(notes, str) else notes
            metadata['correction_notes'] = notes_dict
        except:
            metadata['correction_notes'] = notes

    print(f"📝 Correctie ID {analysis_id}:")
    print(f"  - AI voorspelling: {model_prediction}")
    print(f"  - Correctie: {corrected_label}")
    print(f"  - Is correct: {is_correct}")
    print(f"  - Confidence: {confidence*100:.1f}%")
    print(f"  - Drempel: {confidence_threshold}%")

    # Update met PostgreSQL velden
    # CRITICAL: Use user_correction (NOT corrected_label)
    cursor.execute("""
        UPDATE analyses
        SET user_correction = %s,
            is_correct = %s,
            metadata = %s::jsonb
        WHERE id = %s
    """, (corrected_label, is_correct, json.dumps(metadata), analysis_id))

    conn.commit()
    conn.close()
    print(f"✅ Correctie opgeslagen!")


def get_statistics():
    """
    Haal statistieken op over analyses

    PostgreSQL Schema:
    - status -> result
    - predicted_label -> model_prediction
    - corrected_class -> user_correction

    Returns:
        Dict met statistieken
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total analyses
    cursor.execute("SELECT COUNT(*) as count FROM analyses")
    total = cursor.fetchone()['count']

    # OK vs NOK - use 'result' field
    cursor.execute("SELECT result, COUNT(*) as count FROM analyses GROUP BY result")
    status_rows = cursor.fetchall()
    status_counts = {row['result']: row['count'] for row in status_rows}

    # Meest voorkomende fouten - use model_prediction and result
    cursor.execute("""
        SELECT model_prediction, COUNT(*) as count
        FROM analyses
        WHERE result = 'NOK'
        GROUP BY model_prediction
        ORDER BY count DESC
        LIMIT 5
    """)
    common_issues = cursor.fetchall()

    # Gemiddelde confidence - FIX #1: COALESCE for NULL handling
    cursor.execute("SELECT COALESCE(AVG(confidence), 0) as avg_conf FROM analyses")
    avg_conf_result = cursor.fetchone()
    avg_confidence = avg_conf_result['avg_conf'] if avg_conf_result else 0

    # Aantal correcties - use user_correction field
    cursor.execute("SELECT COUNT(*) as count FROM analyses WHERE user_correction IS NOT NULL")
    corrections_count = cursor.fetchone()['count']

    conn.close()

    return {
        'total_analyses': total,
        'ok_count': status_counts.get('OK', 0),
        'nok_count': status_counts.get('NOK', 0),
        'common_issues': [{'label': row['model_prediction'], 'count': row['count']} for row in common_issues],
        'avg_confidence': round(avg_confidence, 2) if avg_confidence else 0,
        'corrections_count': corrections_count
    }


def get_accuracy_over_time():
    """
    Bereken model accuracy per week om verbetering over tijd te tracken

    PostgreSQL Schema:
    - Uses is_correct boolean field
    - user_correction IS NOT NULL indicates reviewed

    Returns:
        List van dicts met week info en accuracy percentage
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # FIX #1: COALESCE voor SUM() NULL handling
    # Use is_correct boolean field instead of comparing predicted_label = corrected_label
    cursor.execute("""
        SELECT
            TO_CHAR(timestamp, 'IYYY-IW') as week,
            TO_CHAR(timestamp, 'YYYY-MM-DD') as date,
            COUNT(*) as total,
            COALESCE(SUM(CASE WHEN is_correct = TRUE THEN 1 ELSE 0 END), 0) as correct
        FROM analyses
        WHERE user_correction IS NOT NULL
        GROUP BY week, date
        ORDER BY date ASC
    """)

    results = cursor.fetchall()
    conn.close()

    # Bereken accuracy percentage per week
    timeline = []
    for row in results:
        total = row['total']
        correct = row['correct']
        accuracy = round((correct / total * 100), 1) if total > 0 else 0
        timeline.append({
            'week': row['week'],
            'date': row['date'],
            'total': total,
            'correct': correct,
            'accuracy': accuracy
        })

    return timeline


def get_accuracy_stats():
    """
    Bereken model accuracy statistieken (gebruikt voor timeline chart)

    PostgreSQL Schema:
    - Uses is_correct boolean field

    Returns:
        Dict met accuracy metrics
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # FIX #1: COALESCE voor SUM() NULL handling - voorkomt NULL bij lege resultaten
    # Use is_correct boolean field
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COALESCE(SUM(CASE WHEN is_correct = TRUE THEN 1 ELSE 0 END), 0) as correct
        FROM analyses
        WHERE user_correction IS NOT NULL
    """)

    result = cursor.fetchone()
    conn.close()

    total = result['total'] if result else 0
    correct = result['correct'] if result else 0

    accuracy = round((correct / total * 100), 1) if total > 0 else 0

    return {
        'total': total,
        'correct': correct,
        'accuracy': accuracy
    }


def get_training_candidates(confidence_threshold=70.0):
    """
    Haal alle training candidates op die nog niet geëxporteerd zijn
    DYNAMISCH: Filtert op basis van confidence threshold en fouten

    PostgreSQL Schema:
    - Uses is_correct and user_correction fields
    - No exported_for_training or training_candidate fields in PostgreSQL

    Args:
        confidence_threshold: Drempel percentage voor lage confidence (default 70%)

    Returns:
        List van analyse dicts die klaar zijn voor training
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Convert percentage naar decimaal
    threshold_decimal = confidence_threshold / 100.0

    # Select candidates: reviewed (has user_correction) AND (incorrect OR low confidence)
    cursor.execute("""
        SELECT * FROM analyses
        WHERE user_correction IS NOT NULL
        AND (
            is_correct = FALSE
            OR confidence < %s
        )
        ORDER BY timestamp DESC
    """, (threshold_decimal,))

    rows = cursor.fetchall()

    candidates = []
    for row in rows:
        analysis = dict(row)

        # Map PostgreSQL fields to frontend expected fields
        analysis['status'] = analysis.get('result')
        analysis['predicted_label'] = analysis.get('model_prediction')
        analysis['predicted_class'] = analysis.get('model_prediction')
        analysis['corrected_label'] = analysis.get('user_correction')

        # Extract metadata fields
        # FIX #5: JSON parsing error handling
        metadata = analysis.get('metadata', {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = {}
        elif metadata is None:
            metadata = {}

        analysis['missing_items'] = metadata.get('missing_items', [])

        candidates.append(analysis)

    conn.close()
    print(f"📊 Training candidates met drempel {confidence_threshold}%: {len(candidates)} gevonden")
    return candidates


def get_training_statistics():
    """
    Haal statistieken op voor training pipeline

    PostgreSQL Schema:
    - Uses user_correction to determine reviewed status
    - Uses is_correct for training candidates
    - No exported_for_training or training_candidate fields

    Returns:
        Dict met training pipeline metrics
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Aantal unreviewed analyses (no user_correction)
    cursor.execute("SELECT COUNT(*) as count FROM analyses WHERE user_correction IS NULL")
    unreviewed_count = cursor.fetchone()['count']

    # Aantal training candidates (incorrect predictions)
    cursor.execute("""
        SELECT COUNT(*) as count FROM analyses
        WHERE user_correction IS NOT NULL AND is_correct = FALSE
    """)
    training_queue_count = cursor.fetchone()['count']

    # Aantal correct predictions (could be used for validation)
    cursor.execute("SELECT COUNT(*) as count FROM analyses WHERE is_correct = TRUE")
    exported_count = cursor.fetchone()['count']

    conn.close()

    return {
        'unreviewed_count': unreviewed_count,
        'training_queue_count': training_queue_count,
        'exported_count': exported_count,
        'training_target': 200,
        'training_progress_percent': min(100, round((training_queue_count / 200) * 100, 1))
    }


def mark_as_exported(analysis_ids):
    """
    Markeer geselecteerde analyses als geëxporteerd voor training

    NOTE: PostgreSQL schema doesn't have exported_for_training field.
    This function is kept for API compatibility but stores export info in metadata.

    Args:
        analysis_ids: List van analysis IDs om te markeren
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Store export timestamp in metadata instead
    placeholders = ','.join(['%s'] * len(analysis_ids))
    cursor.execute(f"""
        UPDATE analyses
        SET metadata = COALESCE(metadata, '{{}}'::jsonb) || '{{"exported_for_training": true}}'::jsonb
        WHERE id IN ({placeholders})
    """, analysis_ids)

    conn.commit()
    conn.close()


def export_training_data(analysis_ids, export_base_path):
    """
    Exporteer geselecteerde analyses voor retraining
    Organiseert foto's in mappen per corrected_class

    Args:
        analysis_ids: List van analysis IDs om te exporteren
        export_base_path: Basis pad voor export (bijv. 'data/training_export_v2')

    Returns:
        Dict met export statistieken
    """
    import shutil
    from pathlib import Path

    conn = get_db_connection()
    cursor = conn.cursor()

    placeholders = ','.join(['%s'] * len(analysis_ids))
    cursor.execute(f"""
        SELECT * FROM analyses
        WHERE id IN ({placeholders})
    """, analysis_ids)

    rows = cursor.fetchall()
    conn.close()

    export_path = Path(export_base_path)
    export_path.mkdir(parents=True, exist_ok=True)

    stats = {}

    for row in rows:
        analysis = dict(row)
        corrected_class = analysis['corrected_class']
        image_path = Path(analysis['image_path']) if analysis.get('image_path') else None

        if not image_path:
            continue

        # Maak class directory aan
        class_dir = export_path / str(corrected_class)
        class_dir.mkdir(exist_ok=True)

        # Kopieer afbeelding
        if image_path.exists():
            dest_path = class_dir / image_path.name
            shutil.copy2(image_path, dest_path)

            # Update statistieken
            if corrected_class not in stats:
                stats[corrected_class] = 0
            stats[corrected_class] += 1

    # Markeer als geëxporteerd
    mark_as_exported(analysis_ids)

    return {
        'total_exported': len(rows),
        'export_path': str(export_path),
        'class_distribution': stats
    }


def export_to_csv(output_path):
    """
    Export alle analyses naar CSV voor analyse in Excel

    Args:
        output_path: Pad voor CSV bestand
    """
    import csv

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM analyses ORDER BY created_at DESC")
    rows = cursor.fetchall()

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            for row in rows:
                writer.writerow(dict(row))

    conn.close()
    return len(rows)


# ========================================
# WERKPLEK MANAGEMENT FUNCTIES
# ========================================

def create_workplace(name, description, items, reference_photo=None):
    """
    Maak nieuwe werkplek aan

    PostgreSQL Schema:
    - Uses reference_photo_path (NOT reference_photo)

    Args:
        name: Werkplek naam (uniek)
        description: Beschrijving
        items: List van items die op werkplek horen (bijv. ["hamer", "schaar", "sleutel"])
        reference_photo: Pad naar referentie foto (optioneel) - mapped to reference_photo_path

    Returns:
        ID van nieuwe werkplek
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Convert items list to comma-separated string
        items_str = ','.join(items) if isinstance(items, list) else items

        # Map reference_photo parameter to reference_photo_path field
        cursor.execute("""
            INSERT INTO workplaces (name, description, items, reference_photo_path, updated_at)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING id
        """, (name, description, items_str, reference_photo))

        workplace_id = cursor.fetchone()['id']
        conn.commit()
        print(f"OK Werkplek '{name}' aangemaakt (ID: {workplace_id})")
        return workplace_id

    except psycopg2.IntegrityError:
        print(f"ERROR Werkplek '{name}' bestaat al!")
        conn.rollback()
        return None
    finally:
        conn.close()


def get_all_workplaces(active_only=True):
    """
    Haal alle werkplekken op

    PostgreSQL Schema:
    - reference_photo_path needs to be mapped to reference_photo for frontend

    Args:
        active_only: Alleen actieve werkplekken ophalen

    Returns:
        List van werkplek dicts with frontend-compatible field names
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM workplaces"
    # NOTE: PostgreSQL schema doesn't have is_active field, skip filter
    # if active_only:
    #     query += " WHERE is_active = TRUE"
    query += " ORDER BY created_at DESC"

    cursor.execute(query)
    rows = cursor.fetchall()

    workplaces = []
    for row in rows:
        wp = dict(row)

        # Map PostgreSQL fields to frontend expected fields
        wp['reference_photo'] = wp.get('reference_photo_path')  # Map reference_photo_path -> reference_photo

        # FIX #6: Items empty string edge case - handle trailing commas
        if wp.get('items'):
            items_str = wp['items'].strip()
            # Split and filter out empty strings
            wp['items'] = [item.strip() for item in items_str.split(',') if item.strip()] if items_str else []
        else:
            wp['items'] = []

        # FIX #5: Whiteboard JSON parsing error handling
        if wp.get('whiteboard_region'):
            try:
                if isinstance(wp['whiteboard_region'], str):
                    wp['whiteboard_region'] = json.loads(wp['whiteboard_region'])
            except (json.JSONDecodeError, TypeError):
                wp['whiteboard_region'] = None

        # Alias for frontend compatibility (always True if no is_active field)
        wp['active'] = True

        workplaces.append(wp)

    conn.close()
    return workplaces


def get_workplace(workplace_id):
    """
    Haal specifieke werkplek op

    PostgreSQL Schema:
    - reference_photo_path needs to be mapped to reference_photo for frontend

    Args:
        workplace_id: ID van werkplek

    Returns:
        Werkplek dict of None with frontend-compatible field names
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM workplaces WHERE id = %s", (workplace_id,))
    row = cursor.fetchone()

    if row:
        wp = dict(row)

        # Map PostgreSQL fields to frontend expected fields
        wp['reference_photo'] = wp.get('reference_photo_path')  # Map reference_photo_path -> reference_photo

        # FIX #6: Items empty string edge case
        if wp.get('items'):
            items_str = wp['items'].strip()
            wp['items'] = [item.strip() for item in items_str.split(',') if item.strip()] if items_str else []
        else:
            wp['items'] = []

        # FIX #5: Whiteboard JSON parsing error handling
        if wp.get('whiteboard_region'):
            try:
                if isinstance(wp['whiteboard_region'], str):
                    wp['whiteboard_region'] = json.loads(wp['whiteboard_region'])
            except (json.JSONDecodeError, TypeError):
                wp['whiteboard_region'] = None

        # Alias for frontend compatibility (always True if no is_active field)
        wp['active'] = True

        conn.close()
        return wp

    conn.close()
    return None


def update_workplace(workplace_id, name=None, description=None, items=None, reference_photo=None, active=None, confidence_threshold=None, whiteboard_region=None):
    """
    Update werkplek gegevens

    PostgreSQL Schema:
    - reference_photo -> reference_photo_path
    - No is_active field in PostgreSQL schema

    Args:
        workplace_id: ID van werkplek
        name: Nieuwe naam (optioneel)
        description: Nieuwe beschrijving (optioneel)
        items: Nieuwe items list (optioneel)
        reference_photo: Nieuwe referentie foto (optioneel) - mapped to reference_photo_path
        active: Nieuwe active status (optioneel) - IGNORED, no is_active field
        confidence_threshold: Confidence drempel 0.0-1.0 (optioneel)
        whiteboard_region: Whiteboard region dict met x1, y1, x2, y2 (optioneel)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    updates = []
    params = []

    if name is not None:
        updates.append("name = %s")
        params.append(name)
    if description is not None:
        updates.append("description = %s")
        params.append(description)
    if items is not None:
        updates.append("items = %s")
        # Convert list to comma-separated string
        items_str = ','.join(items) if isinstance(items, list) else items
        params.append(items_str)
    if reference_photo is not None:
        # Map reference_photo to reference_photo_path
        updates.append("reference_photo_path = %s")
        params.append(reference_photo)
    if confidence_threshold is not None:
        updates.append("confidence_threshold = %s")
        params.append(confidence_threshold)
    # Note: active is ignored - not in PostgreSQL schema
    if whiteboard_region is not None:
        updates.append("whiteboard_region = %s::jsonb")
        params.append(json.dumps(whiteboard_region) if whiteboard_region else None)

    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(workplace_id)

        query = f"UPDATE workplaces SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(query, params)
        conn.commit()
        print(f"OK Werkplek {workplace_id} bijgewerkt")

    conn.close()


def delete_workplace(workplace_id):
    """
    Verwijder werkplek (en alle gerelateerde data door CASCADE)

    Args:
        workplace_id: ID van werkplek
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM workplaces WHERE id = %s", (workplace_id,))
    conn.commit()
    conn.close()

    print(f"🗑️ Werkplek {workplace_id} verwijderd")


def set_workplace_model(workplace_id, model_type, model_path):
    """
    Stel actief model in voor een werkplek

    Args:
        workplace_id: ID van werkplek
        model_type: 'classification' of 'detection'
        model_path: Pad naar model file (bijv. 'models/werkplek_detector (7).pt')
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE workplaces
        SET active_model_type = %s,
            active_model_path = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (model_type, model_path, workplace_id))

    conn.commit()
    conn.close()

    print(f"✅ Werkplek {workplace_id}: model gezet naar {model_type} ({model_path})")


def get_workplace_model(workplace_id):
    """
    Haal actief model configuratie op voor een werkplek (inclusief model versie)

    Args:
        workplace_id: ID van werkplek

    Returns:
        Dict met model_type, model_path en model_version, of None als niet geconfigureerd
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Haal werkplek model info + actief model uit models tabel
    # PostgreSQL schema: workplaces has 'model_type' (NOT 'active_model_type')
    cursor.execute("""
        SELECT w.model_type, w.active_model_path, m.version
        FROM workplaces w
        LEFT JOIN models m ON m.workplace_id = w.id AND m.is_active = TRUE
        WHERE w.id = %s
    """, (workplace_id,))

    result = cursor.fetchone()
    conn.close()

    if result and result['model_type']:
        return {
            'model_type': result['model_type'],
            'model_path': result['active_model_path'],
            'model_version': result['version']  # Kan None zijn als geen actief model in models tabel
        }
    return None


# ========================================
# TRAINING IMAGES FUNCTIES
# ========================================

def add_training_image(workplace_id, image_path, label, class_id=None, source='manual_upload', model_version=None, metadata=None):
    """
    Voeg training image toe aan dataset

    Args:
        workplace_id: ID van werkplek
        image_path: Pad naar afbeelding
        label: Label (bijv. "ok", "nok_hamer_weg")
        class_id: Class ID (optioneel)
        source: Bron van afbeelding (manual_upload, production, camera)
        model_version: Model versie waarvoor deze training image bedoeld is (optioneel)
        metadata: Extra metadata als dict (optioneel)

    Returns:
        ID van training image
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # FIX #4: JSONB type casting - add ::jsonb cast for metadata
    metadata_json = json.dumps(metadata) if metadata else None

    cursor.execute("""
        INSERT INTO training_images
        (workplace_id, image_path, label, class_id, source, model_version, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
        RETURNING id
    """, (workplace_id, image_path, label, class_id, source, model_version, metadata_json))

    image_id = cursor.fetchone()['id']
    conn.commit()
    conn.close()

    return image_id


def get_training_images(workplace_id, validated_only=False):
    """
    Haal training images op voor werkplek

    Args:
        workplace_id: ID van werkplek
        validated_only: Alleen gevalideerde images

    Returns:
        List van training image dicts
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM training_images WHERE workplace_id = %s"
    if validated_only:
        query += " AND validated = TRUE"
    query += " ORDER BY created_at DESC"

    cursor.execute(query, (workplace_id,))
    rows = cursor.fetchall()

    images = [dict(row) for row in rows]
    conn.close()

    return images


def update_training_image_label(image_id, new_label):
    """
    Update label van een training image

    Args:
        image_id: ID van training image
        new_label: Nieuwe label

    Returns:
        True als succesvol, False anders
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE training_images
            SET label = %s
            WHERE id = %s
        """, (new_label, image_id))

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except Exception as e:
        conn.close()
        print(f"Error updating training image label: {e}")
        return False


def delete_training_image(image_id):
    """
    Verwijder een training image

    Args:
        image_id: ID van training image

    Returns:
        Tuple (success: bool, image_path: str) - path voor file cleanup
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Haal eerst het image path op voor cleanup
        cursor.execute("SELECT image_path FROM training_images WHERE id = %s", (image_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return False, None

        image_path = row['image_path']

        # Verwijder uit database
        cursor.execute("DELETE FROM training_images WHERE id = %s", (image_id,))
        conn.commit()

        success = cursor.rowcount > 0
        conn.close()
        return success, image_path
    except Exception as e:
        conn.close()
        print(f"Error deleting training image: {e}")
        return False, None


def get_training_dataset_stats(workplace_id, model_version=None):
    """
    Haal dataset statistieken op voor werkplek - focus op MODEL FOUTEN

    PostgreSQL Schema:
    - Uses user_correction (NOT corrected_label)
    - Uses model_prediction (NOT predicted_label)
    - Uses is_correct boolean
    - Correction notes stored in metadata->correction_notes

    Args:
        workplace_id: ID van werkplek
        model_version: Optioneel - filter op specifieke model versie (bijv. "v1.0", "v2.0")

    Returns:
        Dict met statistieken over model prestaties en fout types
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Build WHERE clause with optional model_version filter
    if model_version:
        where_base = "workplace_id = %s AND model_version = %s"
        params_base = (workplace_id, model_version)
    else:
        where_base = "workplace_id = %s"
        params_base = (workplace_id,)

    # Totaal aantal analyses/foto's voor deze werkplek (+ optioneel model filter)
    cursor.execute(f"SELECT COUNT(*) as count FROM analyses WHERE {where_base}", params_base)
    total = cursor.fetchone()['count']

    # Beoordeelde foto's (hebben user_correction)
    cursor.execute(f"""
        SELECT COUNT(*) as count FROM analyses
        WHERE {where_base} AND user_correction IS NOT NULL AND user_correction != ''
    """, params_base)
    labeled_count = cursor.fetchone()['count']

    unlabeled_count = total - labeled_count

    # MODEL ACCURACY: Correct voorspeld (is_correct = TRUE)
    cursor.execute(f"""
        SELECT COUNT(*) as count FROM analyses
        WHERE {where_base}
        AND user_correction IS NOT NULL
        AND is_correct = TRUE
    """, params_base)
    correct_predictions = cursor.fetchone()['count']

    # MODEL FOUTEN: Incorrect voorspeld (is_correct = FALSE)
    cursor.execute(f"""
        SELECT COUNT(*) as count FROM analyses
        WHERE {where_base}
        AND user_correction IS NOT NULL
        AND is_correct = FALSE
    """, params_base)
    incorrect_predictions = cursor.fetchone()['count']

    # FOUT TYPES: Welke fouten maakt het model?
    cursor.execute(f"""
        SELECT
            model_prediction,
            user_correction,
            COUNT(*) as count
        FROM analyses
        WHERE {where_base}
        AND user_correction IS NOT NULL
        AND is_correct = FALSE
        GROUP BY model_prediction, user_correction
        ORDER BY count DESC
    """, params_base)

    error_types = []
    for row in cursor.fetchall():
        error_types.append({
            'predicted': row['model_prediction'],
            'actual': row['user_correction'],
            'count': row['count'],
            'description': f"Model zei '{row['model_prediction']}' maar was '{row['user_correction']}'"
        })

    # Distributie van user_correction labels (voor training set balans)
    cursor.execute(f"""
        SELECT user_correction, COUNT(*) as count
        FROM analyses
        WHERE {where_base} AND user_correction IS NOT NULL AND user_correction != ''
        GROUP BY user_correction
        ORDER BY count DESC
    """, params_base)
    label_rows = cursor.fetchall()
    label_distribution = {row['user_correction']: row['count'] for row in label_rows}

    # DETECTIE FOUTEN PER OBJECT (uit metadata->correction_notes JSON)
    cursor.execute(f"""
        SELECT metadata
        FROM analyses
        WHERE {where_base}
        AND metadata IS NOT NULL
        AND metadata->>'correction_notes' IS NOT NULL
    """, params_base)

    detection_errors = {
        'missing': {},      # Item niet gedetecteerd (false negative)
        'false_positive': {},  # Item foutief gedetecteerd (false positive)
        'count_error': {}   # Verkeerd aantal gedetecteerd
    }

    for row in cursor.fetchall():
        try:
            # FIX #5: JSON parsing error handling
            metadata = row['metadata']
            if isinstance(metadata, str):
                metadata = json.loads(metadata)

            notes = metadata.get('correction_notes', {})
            if isinstance(notes, str):
                notes = json.loads(notes)

            # Parse missing items
            if 'missing_items' in notes and notes['missing_items']:
                for item in notes['missing_items']:
                    detection_errors['missing'][item] = detection_errors['missing'].get(item, 0) + 1

            # Parse false positives
            if 'false_positives' in notes and notes['false_positives']:
                for item in notes['false_positives']:
                    detection_errors['false_positive'][item] = detection_errors['false_positive'].get(item, 0) + 1

            # Parse count errors
            if 'incorrect_counts' in notes and notes['incorrect_counts']:
                for item, count_data in notes['incorrect_counts'].items():
                    detected = count_data.get('detected', 0)
                    expected = count_data.get('expected', 0)
                    error_key = f"{item} ({detected}x ipv {expected}x)"
                    detection_errors['count_error'][error_key] = detection_errors['count_error'].get(error_key, 0) + 1
        except:
            continue

    conn.close()

    accuracy = round((correct_predictions / labeled_count * 100), 1) if labeled_count > 0 else 0

    return {
        'total_images': total,
        'labeled_count': labeled_count,
        'unlabeled_count': unlabeled_count,
        'training_ready': labeled_count,
        'correct_predictions': correct_predictions,
        'incorrect_predictions': incorrect_predictions,
        'accuracy': accuracy,
        'error_types': error_types,
        'label_distribution': label_distribution,
        'detection_errors': detection_errors
    }


def validate_training_image(image_id, validated=True):
    """
    Markeer training image als gevalideerd

    Args:
        image_id: ID van training image
        validated: Boolean
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE training_images
        SET validated = %s
        WHERE id = %s
    """, (validated, image_id))

    conn.commit()
    conn.close()


# ========================================
# MODEL MANAGEMENT FUNCTIES
# ========================================

def register_model(workplace_id, version, model_path, model_type='classification', uploaded_by='admin', test_accuracy=None, config=None, notes=None):
    """
    Registreer nieuw model in database

    PostgreSQL Schema:
    - training_date (NOT uploaded_at)
    - training_images_count
    - metrics (jsonb) - stores test_accuracy and config
    - created_by (integer, NOT uploaded_by text)

    Args:
        workplace_id: ID van werkplek
        version: Model versie (bijv. "v1.0", "v1.1")
        model_path: Pad naar model bestand
        model_type: Type model ('classification' of 'detection')
        uploaded_by: Wie heeft het model geüpload (ignored, use created_by integer instead)
        test_accuracy: Test accuracy percentage (stored in metrics jsonb)
        config: JSON string met model config (stored in metrics jsonb)
        notes: Notities over model (ignored, use metrics jsonb)

    Returns:
        ID van model
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Build metrics JSON from test_accuracy, config, and notes
    metrics = {}
    if test_accuracy is not None:
        metrics['test_accuracy'] = test_accuracy
    if config:
        try:
            metrics['config'] = json.loads(config) if isinstance(config, str) else config
        except:
            metrics['config'] = config
    if notes:
        metrics['notes'] = notes

    cursor.execute("""
        INSERT INTO models
        (workplace_id, version, model_path, model_type, training_date, metrics, is_active)
        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, %s::jsonb, FALSE)
        RETURNING id
    """, (workplace_id, version, model_path, model_type, json.dumps(metrics) if metrics else None))

    model_id = cursor.fetchone()['id']
    conn.commit()
    conn.close()

    print(f"✅ Model {version} ({model_type}) geregistreerd voor werkplek {workplace_id} (ID: {model_id})")
    return model_id


def get_models(workplace_id, status=None):
    """
    Haal modellen op voor werkplek

    PostgreSQL Schema:
    - training_date (NOT uploaded_at)
    - No status field in PostgreSQL
    - metrics jsonb contains test_accuracy, config, notes

    Args:
        workplace_id: ID van werkplek
        status: Filter op status (optioneel) - IGNORED, no status field

    Returns:
        List van model dicts with extracted metrics
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM models WHERE workplace_id = %s"
    params = [workplace_id]

    # Note: status parameter ignored - no status field in PostgreSQL schema

    query += " ORDER BY training_date DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    models = []
    # FIX #3: Boolean conversion for is_active field
    for row in rows:
        model = dict(row)
        if 'is_active' in model:
            model['is_active'] = bool(model['is_active'])

        # Extract metrics for frontend compatibility
        # FIX #5: JSON parsing error handling
        metrics = model.get('metrics', {})
        if isinstance(metrics, str):
            try:
                metrics = json.loads(metrics)
            except (json.JSONDecodeError, TypeError):
                metrics = {}
        elif metrics is None:
            metrics = {}

        # Map metrics fields to top-level for frontend compatibility
        model['test_accuracy'] = metrics.get('test_accuracy')
        model['config'] = metrics.get('config')
        model['notes'] = metrics.get('notes')

        # Map training_date to uploaded_at for frontend compatibility
        model['uploaded_at'] = model.get('training_date')

        models.append(model)

    conn.close()
    return models


def get_active_model(workplace_id):
    """
    Haal actieve model op voor werkplek

    PostgreSQL Schema:
    - training_date (NOT uploaded_at)
    - metrics jsonb contains test_accuracy, config, notes

    Args:
        workplace_id: ID van werkplek

    Returns:
        Model dict of None with extracted metrics
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM models
        WHERE workplace_id = %s AND is_active = TRUE
        ORDER BY training_date DESC
        LIMIT 1
    """, (workplace_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        model = dict(row)
        # FIX #3: Boolean conversion
        if 'is_active' in model:
            model['is_active'] = bool(model['is_active'])

        # Extract metrics for frontend compatibility
        # FIX #5: JSON parsing error handling
        metrics = model.get('metrics', {})
        if isinstance(metrics, str):
            try:
                metrics = json.loads(metrics)
            except (json.JSONDecodeError, TypeError):
                metrics = {}
        elif metrics is None:
            metrics = {}

        # Map metrics fields to top-level for frontend compatibility
        model['test_accuracy'] = metrics.get('test_accuracy')
        model['config'] = metrics.get('config')
        model['notes'] = metrics.get('notes')

        # Map training_date to uploaded_at for frontend compatibility
        model['uploaded_at'] = model.get('training_date')

        return model
    return None


def activate_model(model_id):
    """
    Activeer model (deactiveer andere modellen voor deze werkplek)
    en update werkplek configuratie

    Args:
        model_id: ID van model om te activeren
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Haal model info op
    cursor.execute("SELECT workplace_id, model_path, model_type FROM models WHERE id = %s", (model_id,))
    result = cursor.fetchone()

    if not result:
        conn.close()
        raise ValueError(f"Model {model_id} niet gevonden")

    workplace_id = result['workplace_id']
    model_path = result['model_path']
    model_type = result['model_type']

    # Deactiveer alle andere modellen voor deze werkplek
    cursor.execute("""
        UPDATE models
        SET is_active = FALSE
        WHERE workplace_id = %s AND is_active = TRUE
    """, (workplace_id,))

    # Activeer dit model
    cursor.execute("""
        UPDATE models
        SET is_active = TRUE
        WHERE id = %s
    """, (model_id,))

    # Update werkplek met actieve model configuratie
    cursor.execute("""
        UPDATE workplaces
        SET active_model_type = %s,
            active_model_path = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (model_type, model_path, workplace_id))

    conn.commit()
    conn.close()

    print(f"✅ Model {model_id} geactiveerd voor werkplek {workplace_id} ({model_type} type)")


# ========================================
# DATASET EXPORT FUNCTIES
# ========================================

def register_dataset_export(workplace_id, export_path, image_count, class_distribution, exported_by='admin', notes=None):
    """
    Registreer dataset export

    Args:
        workplace_id: ID van werkplek
        export_path: Pad naar export ZIP
        image_count: Aantal afbeeldingen
        class_distribution: Dict met class verdeling
        exported_by: Wie heeft geëxporteerd
        notes: Notities

    Returns:
        ID van export
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO dataset_exports
        (workplace_id, export_path, image_count, class_distribution, exported_by, notes)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (workplace_id, export_path, image_count, json.dumps(class_distribution), exported_by, notes))

    export_id = cursor.fetchone()['id']
    conn.commit()
    conn.close()

    print(f"OK Dataset export geregistreerd (ID: {export_id})")
    return export_id


def get_dataset_exports(workplace_id):
    """
    Haal dataset exports op voor werkplek

    Args:
        workplace_id: ID van werkplek

    Returns:
        List van export dicts
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM dataset_exports
        WHERE workplace_id = %s
        ORDER BY exported_at DESC
    """, (workplace_id,))

    rows = cursor.fetchall()

    exports = []
    for row in rows:
        export = dict(row)
        try:
            export['class_distribution'] = json.loads(export['class_distribution'])
        except:
            export['class_distribution'] = {}
        exports.append(export)

    conn.close()
    return exports


if __name__ == "__main__":
    # Fix Windows console encoding
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # Test database connection and statistics
    # NOTE: init_database() removed - PostgreSQL schema already exists!
    print("Testing PostgreSQL database connection...")
    try:
        conn = get_db_connection()
        print("✅ Database connection successful!")
        conn.close()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        exit(1)

    print("\n== Database statistieken ==")
    stats = get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
