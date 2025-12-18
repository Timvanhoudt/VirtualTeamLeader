"""
Database module voor analyse logging
Slaat alle analyses op voor latere review en model verbetering
"""

import sqlite3
from datetime import datetime
from pathlib import Path
import json

DATABASE_PATH = Path("data/analyses.db")

def init_database():
    """Initialiseer database en maak tabellen aan"""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # ===== BESTAANDE TABEL: analyses =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            image_path TEXT NOT NULL,
            predicted_class TEXT NOT NULL,
            predicted_label TEXT NOT NULL,
            confidence REAL NOT NULL,
            status TEXT NOT NULL,
            missing_items TEXT,
            corrected_class TEXT,
            corrected_label TEXT,
            notes TEXT,
            face_count INTEGER DEFAULT 0,
            training_candidate BOOLEAN DEFAULT 0,
            exported_for_training BOOLEAN DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            workplace_id INTEGER,
            model_version TEXT
        )
    """)

    # ===== NIEUWE TABEL: workplaces =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workplaces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            items TEXT NOT NULL,
            reference_photo TEXT,
            active BOOLEAN DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ===== NIEUWE TABEL: training_images =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS training_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workplace_id INTEGER NOT NULL,
            image_path TEXT NOT NULL,
            label TEXT NOT NULL,
            class_id INTEGER,
            source TEXT DEFAULT 'manual_upload',
            validated BOOLEAN DEFAULT 0,
            used_in_training BOOLEAN DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (workplace_id) REFERENCES workplaces(id) ON DELETE CASCADE
        )
    """)

    # ===== NIEUWE TABEL: models =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workplace_id INTEGER NOT NULL,
            version TEXT NOT NULL,
            model_path TEXT NOT NULL,
            uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
            uploaded_by TEXT DEFAULT 'admin',
            status TEXT DEFAULT 'uploaded',
            test_accuracy REAL,
            config TEXT,
            notes TEXT,
            FOREIGN KEY (workplace_id) REFERENCES workplaces(id) ON DELETE CASCADE
        )
    """)

    # ===== NIEUWE TABEL: dataset_exports =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dataset_exports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workplace_id INTEGER NOT NULL,
            export_path TEXT NOT NULL,
            image_count INTEGER,
            class_distribution TEXT,
            exported_at TEXT DEFAULT CURRENT_TIMESTAMP,
            exported_by TEXT DEFAULT 'admin',
            notes TEXT,
            FOREIGN KEY (workplace_id) REFERENCES workplaces(id) ON DELETE CASCADE
        )
    """)

    # Migratie: voeg nieuwe kolommen toe als ze niet bestaan
    try:
        cursor.execute("SELECT training_candidate FROM analyses LIMIT 1")
    except sqlite3.OperationalError:
        print("Migratie: training_candidate kolom toevoegen...")
        cursor.execute("ALTER TABLE analyses ADD COLUMN training_candidate BOOLEAN DEFAULT 0")
        conn.commit()

    try:
        cursor.execute("SELECT exported_for_training FROM analyses LIMIT 1")
    except sqlite3.OperationalError:
        print("Migratie: exported_for_training kolom toevoegen...")
        cursor.execute("ALTER TABLE analyses ADD COLUMN exported_for_training BOOLEAN DEFAULT 0")
        conn.commit()

    try:
        cursor.execute("SELECT device_id FROM analyses LIMIT 1")
    except sqlite3.OperationalError:
        print("Migratie: device_id kolom toevoegen...")
        cursor.execute("ALTER TABLE analyses ADD COLUMN device_id TEXT DEFAULT 'onbekend'")
        conn.commit()

    try:
        cursor.execute("SELECT workplace_id FROM analyses LIMIT 1")
    except sqlite3.OperationalError:
        print("Migratie: workplace_id kolom toevoegen...")
        cursor.execute("ALTER TABLE analyses ADD COLUMN workplace_id INTEGER")
        conn.commit()

    try:
        cursor.execute("SELECT model_version FROM analyses LIMIT 1")
    except sqlite3.OperationalError:
        print("Migratie: model_version kolom toevoegen...")
        cursor.execute("ALTER TABLE analyses ADD COLUMN model_version TEXT")
        conn.commit()

    conn.commit()
    conn.close()
    print("OK Database geinitaliseerd met alle tabellen")


def save_analysis(data):
    """
    Sla analyse resultaat op in database

    Args:
        data: Dict met analyse gegevens

    Returns:
        ID van opgeslagen analyse
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO analyses
        (timestamp, image_path, predicted_class, predicted_label,
         confidence, status, missing_items, face_count, device_id, workplace_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['timestamp'],
        data['image_path'],
        data['predicted_class'],
        data['predicted_label'],
        data['confidence'],
        data['status'],
        json.dumps(data.get('missing_items', [])),
        data.get('face_count', 0),
        data.get('device_id', 'onbekend'),
        data.get('workplace_id', None)
    ))

    analysis_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return analysis_id


def get_all_analyses(limit=100, offset=0, filter_status=None):
    """
    Haal alle analyses op

    Args:
        limit: Maximum aantal resultaten
        offset: Offset voor paginatie
        filter_status: Filter op OK/NOK (optioneel)

    Returns:
        List van analyse dicts
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = "SELECT * FROM analyses"
    params = []

    if filter_status:
        query += " WHERE status = ?"
        params.append(filter_status)

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
    return analyses


def update_correction(analysis_id, corrected_class, corrected_label, notes=None, confidence_threshold=70.0):
    """
    Update analyse met correctie (voor model verbetering)
    BEHOUDT de originele predicted_class/label voor accuracy tracking!
    AUTOMATISCH markeren als training candidate bij fouten of lage confidence

    Args:
        analysis_id: ID van analyse
        corrected_class: Correcte class
        corrected_label: Correct label
        notes: Optionele notities
        confidence_threshold: Dynamische drempel voor lage confidence (default 70%)
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Haal eerst de originele analyse op om confidence en predicted_label te checken
    cursor.execute("""
        SELECT predicted_label, confidence
        FROM analyses
        WHERE id = ?
    """, (analysis_id,))

    result = cursor.fetchone()
    if not result:
        conn.close()
        raise ValueError(f"Analyse met ID {analysis_id} niet gevonden")

    predicted_label, confidence = result

    # Bepaal of dit een training candidate is
    # Criteria: 1) Fout voorspeld OF 2) Lage confidence (onder dynamische drempel)
    is_incorrect = (predicted_label != corrected_label)
    threshold_decimal = confidence_threshold / 100.0  # Convert percentage naar decimaal
    is_low_confidence = (confidence < threshold_decimal)
    should_be_training_candidate = is_incorrect or is_low_confidence

    print(f"📝 Correctie ID {analysis_id}:")
    print(f"  - AI voorspelling: {predicted_label}")
    print(f"  - Correctie: {corrected_label}")
    print(f"  - Confidence: {confidence*100:.1f}%")
    print(f"  - Drempel: {confidence_threshold}%")
    print(f"  - Training candidate: {should_be_training_candidate} (incorrect={is_incorrect}, low_conf={is_low_confidence})")

    # Update ALLEEN de correctie velden, NIET de predicted velden!
    # We moeten de originele AI voorspelling behouden voor accuracy tracking
    cursor.execute("""
        UPDATE analyses
        SET corrected_class = ?,
            corrected_label = ?,
            notes = ?,
            training_candidate = ?
        WHERE id = ?
    """, (corrected_class, corrected_label, notes, 1 if should_be_training_candidate else 0, analysis_id))

    conn.commit()
    conn.close()
    print(f"OK Correctie opgeslagen!")


def get_statistics():
    """
    Haal statistieken op over analyses

    Returns:
        Dict met statistieken
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Total analyses
    cursor.execute("SELECT COUNT(*) FROM analyses")
    total = cursor.fetchone()[0]

    # OK vs NOK
    cursor.execute("SELECT status, COUNT(*) FROM analyses GROUP BY status")
    status_counts = dict(cursor.fetchall())

    # Meest voorkomende fouten
    cursor.execute("""
        SELECT predicted_label, COUNT(*) as count
        FROM analyses
        WHERE status = 'NOK'
        GROUP BY predicted_label
        ORDER BY count DESC
        LIMIT 5
    """)
    common_issues = cursor.fetchall()

    # Gemiddelde confidence
    cursor.execute("SELECT AVG(confidence) FROM analyses")
    avg_confidence = cursor.fetchone()[0]

    # Aantal correcties
    cursor.execute("SELECT COUNT(*) FROM analyses WHERE corrected_class IS NOT NULL")
    corrections_count = cursor.fetchone()[0]

    conn.close()

    return {
        'total_analyses': total,
        'ok_count': status_counts.get('OK', 0),
        'nok_count': status_counts.get('NOK', 0),
        'common_issues': [{'label': label, 'count': count} for label, count in common_issues],
        'avg_confidence': round(avg_confidence, 2) if avg_confidence else 0,
        'corrections_count': corrections_count
    }


def get_accuracy_over_time():
    """
    Bereken model accuracy per week om verbetering over tijd te tracken

    Returns:
        List van dicts met week info en accuracy percentage
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Haal alle gecorrigeerde analyses op, gegroepeerd per week
    cursor.execute("""
        SELECT
            strftime('%Y-W%W', created_at) as week,
            strftime('%Y-%m-%d', created_at) as date,
            COUNT(*) as total,
            SUM(CASE WHEN predicted_label = corrected_label THEN 1 ELSE 0 END) as correct
        FROM analyses
        WHERE corrected_label IS NOT NULL
        GROUP BY week
        ORDER BY date ASC
    """)

    results = cursor.fetchall()
    conn.close()

    # Bereken accuracy percentage per week
    timeline = []
    for week, date, total, correct in results:
        accuracy = round((correct / total * 100), 1) if total > 0 else 0
        timeline.append({
            'week': week,
            'date': date,
            'total': total,
            'correct': correct,
            'accuracy': accuracy
        })

    return timeline


def get_training_candidates(confidence_threshold=70.0):
    """
    Haal alle training candidates op die nog niet geëxporteerd zijn
    DYNAMISCH: Filtert op basis van confidence threshold en fouten

    Args:
        confidence_threshold: Drempel percentage voor lage confidence (default 70%)

    Returns:
        List van analyse dicts die klaar zijn voor training
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Convert percentage naar decimaal
    threshold_decimal = confidence_threshold / 100.0

    # Haal alle gecorrigeerde analyses op die:
    # 1) Fout voorspeld ZIJN (predicted != corrected) OF
    # 2) Lage confidence hebben (< drempel)
    # EN nog niet geëxporteerd zijn
    cursor.execute("""
        SELECT * FROM analyses
        WHERE corrected_label IS NOT NULL
        AND exported_for_training = 0
        AND (
            predicted_label != corrected_label
            OR confidence < ?
        )
        ORDER BY created_at DESC
    """, (threshold_decimal,))

    rows = cursor.fetchall()

    candidates = []
    for row in rows:
        analysis = dict(row)
        analysis['missing_items'] = json.loads(analysis['missing_items']) if analysis['missing_items'] else []
        candidates.append(analysis)

    conn.close()
    print(f"📊 Training candidates met drempel {confidence_threshold}%: {len(candidates)} gevonden")
    return candidates


def get_training_statistics():
    """
    Haal statistieken op voor training pipeline

    Returns:
        Dict met training pipeline metrics
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Aantal unreviewed analyses
    cursor.execute("SELECT COUNT(*) FROM analyses WHERE corrected_label IS NULL")
    unreviewed_count = cursor.fetchone()[0]

    # Aantal training candidates (nog niet geëxporteerd)
    cursor.execute("""
        SELECT COUNT(*) FROM analyses
        WHERE training_candidate = 1 AND exported_for_training = 0
    """)
    training_queue_count = cursor.fetchone()[0]

    # Aantal al geëxporteerd
    cursor.execute("SELECT COUNT(*) FROM analyses WHERE exported_for_training = 1")
    exported_count = cursor.fetchone()[0]

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

    Args:
        analysis_ids: List van analysis IDs om te markeren
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    placeholders = ','.join('?' * len(analysis_ids))
    cursor.execute(f"""
        UPDATE analyses
        SET exported_for_training = 1
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

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    placeholders = ','.join('?' * len(analysis_ids))
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
        image_path = Path(analysis['image_path'])

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

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
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

    Args:
        name: Werkplek naam (uniek)
        description: Beschrijving
        items: List van items die op werkplek horen (bijv. ["hamer", "schaar", "sleutel"])
        reference_photo: Pad naar referentie foto (optioneel)

    Returns:
        ID van nieuwe werkplek
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO workplaces (name, description, items, reference_photo, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (name, description, json.dumps(items), reference_photo))

        workplace_id = cursor.lastrowid
        conn.commit()
        print(f"OK Werkplek '{name}' aangemaakt (ID: {workplace_id})")
        return workplace_id

    except sqlite3.IntegrityError:
        print(f"ERROR Werkplek '{name}' bestaat al!")
        return None
    finally:
        conn.close()


def get_all_workplaces(active_only=True):
    """
    Haal alle werkplekken op

    Args:
        active_only: Alleen actieve werkplekken ophalen

    Returns:
        List van werkplek dicts
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = "SELECT * FROM workplaces"
    if active_only:
        query += " WHERE active = 1"
    query += " ORDER BY created_at DESC"

    cursor.execute(query)
    rows = cursor.fetchall()

    workplaces = []
    for row in rows:
        workplace = dict(row)
        workplace['items'] = json.loads(workplace['items'])
        workplaces.append(workplace)

    conn.close()
    return workplaces


def get_workplace(workplace_id):
    """
    Haal specifieke werkplek op

    Args:
        workplace_id: ID van werkplek

    Returns:
        Werkplek dict of None
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM workplaces WHERE id = ?", (workplace_id,))
    row = cursor.fetchone()

    if row:
        workplace = dict(row)
        workplace['items'] = json.loads(workplace['items'])
        conn.close()
        return workplace

    conn.close()
    return None


def update_workplace(workplace_id, name=None, description=None, items=None, reference_photo=None, active=None):
    """
    Update werkplek gegevens

    Args:
        workplace_id: ID van werkplek
        name: Nieuwe naam (optioneel)
        description: Nieuwe beschrijving (optioneel)
        items: Nieuwe items list (optioneel)
        reference_photo: Nieuwe referentie foto (optioneel)
        active: Nieuwe active status (optioneel)
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    updates = []
    params = []

    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if description is not None:
        updates.append("description = ?")
        params.append(description)
    if items is not None:
        updates.append("items = ?")
        params.append(json.dumps(items))
    if reference_photo is not None:
        updates.append("reference_photo = ?")
        params.append(reference_photo)
    if active is not None:
        updates.append("active = ?")
        params.append(1 if active else 0)

    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(workplace_id)

        query = f"UPDATE workplaces SET {', '.join(updates)} WHERE id = ?"
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
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM workplaces WHERE id = ?", (workplace_id,))
    conn.commit()
    conn.close()

    print(f"🗑️ Werkplek {workplace_id} verwijderd")


# ========================================
# TRAINING IMAGES FUNCTIES
# ========================================

def add_training_image(workplace_id, image_path, label, class_id=None, source='manual_upload'):
    """
    Voeg training image toe aan dataset

    Args:
        workplace_id: ID van werkplek
        image_path: Pad naar afbeelding
        label: Label (bijv. "ok", "nok_hamer_weg")
        class_id: Class ID (optioneel)
        source: Bron van afbeelding (manual_upload, production, camera)

    Returns:
        ID van training image
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO training_images
        (workplace_id, image_path, label, class_id, source)
        VALUES (?, ?, ?, ?, ?)
    """, (workplace_id, image_path, label, class_id, source))

    image_id = cursor.lastrowid
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
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = "SELECT * FROM training_images WHERE workplace_id = ?"
    if validated_only:
        query += " AND validated = 1"
    query += " ORDER BY created_at DESC"

    cursor.execute(query, (workplace_id,))
    rows = cursor.fetchall()

    images = [dict(row) for row in rows]
    conn.close()

    return images


def get_training_dataset_stats(workplace_id):
    """
    Haal dataset statistieken op voor werkplek

    Args:
        workplace_id: ID van werkplek

    Returns:
        Dict met statistieken
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Totaal aantal images
    cursor.execute("SELECT COUNT(*) FROM training_images WHERE workplace_id = ?", (workplace_id,))
    total = cursor.fetchone()[0]

    # Per label
    cursor.execute("""
        SELECT label, COUNT(*) as count
        FROM training_images
        WHERE workplace_id = ?
        GROUP BY label
    """, (workplace_id,))
    label_counts = dict(cursor.fetchall())

    # Validated vs unvalidated
    cursor.execute("""
        SELECT validated, COUNT(*) as count
        FROM training_images
        WHERE workplace_id = ?
        GROUP BY validated
    """, (workplace_id,))
    validation_counts = dict(cursor.fetchall())

    conn.close()

    return {
        'total_images': total,
        'label_distribution': label_counts,
        'validated_count': validation_counts.get(1, 0),
        'unvalidated_count': validation_counts.get(0, 0)
    }


def validate_training_image(image_id, validated=True):
    """
    Markeer training image als gevalideerd

    Args:
        image_id: ID van training image
        validated: Boolean
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE training_images
        SET validated = ?
        WHERE id = ?
    """, (1 if validated else 0, image_id))

    conn.commit()
    conn.close()


# ========================================
# MODEL MANAGEMENT FUNCTIES
# ========================================

def register_model(workplace_id, version, model_path, uploaded_by='admin', test_accuracy=None, config=None, notes=None):
    """
    Registreer nieuw model in database

    Args:
        workplace_id: ID van werkplek
        version: Model versie (bijv. "v1.0", "v1.1")
        model_path: Pad naar model bestand
        uploaded_by: Wie heeft het model geüpload
        test_accuracy: Test accuracy percentage
        config: JSON string met model config
        notes: Notities over model

    Returns:
        ID van model
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO models
        (workplace_id, version, model_path, uploaded_by, test_accuracy, config, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (workplace_id, version, model_path, uploaded_by, test_accuracy, config, notes))

    model_id = cursor.lastrowid
    conn.commit()
    conn.close()

    print(f"OK Model {version} geregistreerd voor werkplek {workplace_id} (ID: {model_id})")
    return model_id


def get_models(workplace_id, status=None):
    """
    Haal modellen op voor werkplek

    Args:
        workplace_id: ID van werkplek
        status: Filter op status (optioneel)

    Returns:
        List van model dicts
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = "SELECT * FROM models WHERE workplace_id = ?"
    params = [workplace_id]

    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY uploaded_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    models = [dict(row) for row in rows]
    conn.close()

    return models


def get_active_model(workplace_id):
    """
    Haal actieve model op voor werkplek

    Args:
        workplace_id: ID van werkplek

    Returns:
        Model dict of None
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM models
        WHERE workplace_id = ? AND status = 'active'
        ORDER BY uploaded_at DESC
        LIMIT 1
    """, (workplace_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def activate_model(model_id):
    """
    Activeer model (deactiveer andere modellen voor deze werkplek)

    Args:
        model_id: ID van model om te activeren
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Haal werkplek ID op
    cursor.execute("SELECT workplace_id FROM models WHERE id = ?", (model_id,))
    result = cursor.fetchone()

    if not result:
        conn.close()
        raise ValueError(f"Model {model_id} niet gevonden")

    workplace_id = result[0]

    # Deactiveer alle andere modellen voor deze werkplek
    cursor.execute("""
        UPDATE models
        SET status = 'archived'
        WHERE workplace_id = ? AND status = 'active'
    """, (workplace_id,))

    # Activeer dit model
    cursor.execute("""
        UPDATE models
        SET status = 'active'
        WHERE id = ?
    """, (model_id,))

    conn.commit()
    conn.close()

    print(f"OK Model {model_id} geactiveerd voor werkplek {workplace_id}")


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
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO dataset_exports
        (workplace_id, export_path, image_count, class_distribution, exported_by, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (workplace_id, export_path, image_count, json.dumps(class_distribution), exported_by, notes))

    export_id = cursor.lastrowid
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
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM dataset_exports
        WHERE workplace_id = ?
        ORDER BY exported_at DESC
    """, (workplace_id,))

    rows = cursor.fetchall()

    exports = []
    for row in rows:
        export = dict(row)
        export['class_distribution'] = json.loads(export['class_distribution'])
        exports.append(export)

    conn.close()
    return exports


if __name__ == "__main__":
    # Test database
    init_database()
    print("\n== Database statistieken ==")
    stats = get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
