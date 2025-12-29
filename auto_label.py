"""
Auto-label script - Gebruik je eigen YOLO model om nieuwe images automatisch te labelen
Genereert YOLO format label files die je kunt gebruiken voor training of uploaden naar Roboflow
"""
from ultralytics import YOLO
from pathlib import Path
from PIL import Image
import shutil

# =====================================================
# CONFIGURATIE
# =====================================================
MODEL_PATH = "backend/models/werkplek_detector (7).pt"
IMAGES_DIR = "images_to_label"  # Plaats hier je nieuwe images
OUTPUT_DIR = "labeled_dataset"  # Output folder met images + labels
CONFIDENCE_THRESHOLD = 0.25  # Minimum confidence voor detecties

# =====================================================
# SETUP
# =====================================================
print("="*80)
print("🤖 AUTO-LABEL SCRIPT")
print("="*80)
print(f"Model: {MODEL_PATH}")
print(f"Images directory: {IMAGES_DIR}")
print(f"Output directory: {OUTPUT_DIR}")
print(f"Confidence threshold: {CONFIDENCE_THRESHOLD}")
print("="*80 + "\n")

# Check if model exists
model_path = Path(MODEL_PATH)
if not model_path.exists():
    print(f"❌ Model niet gevonden: {MODEL_PATH}")
    print("Beschikbare modellen:")
    for model in Path("backend/models").glob("*.pt"):
        print(f"  - {model.name}")
    exit(1)

# Check if images directory exists
images_dir = Path(IMAGES_DIR)
if not images_dir.exists():
    print(f"❌ Images directory niet gevonden: {IMAGES_DIR}")
    print(f"\n💡 Maak de folder aan en plaats je images erin:")
    print(f"   mkdir {IMAGES_DIR}")
    print(f"   # Kopieer je images naar {IMAGES_DIR}/")
    exit(1)

# Create output directories
output_dir = Path(OUTPUT_DIR)
output_images = output_dir / "images"
output_labels = output_dir / "labels"
output_images.mkdir(parents=True, exist_ok=True)
output_labels.mkdir(parents=True, exist_ok=True)

# Load model
print(f"📦 Loading model...")
model = YOLO(str(model_path))
print(f"✓ Model loaded: {model.names}\n")

# =====================================================
# AUTO-LABELING
# =====================================================
image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpeg"))

if len(image_files) == 0:
    print(f"❌ Geen images gevonden in {IMAGES_DIR}")
    print("Ondersteunde formaten: .jpg, .png, .jpeg")
    exit(1)

print(f"🖼️  Gevonden {len(image_files)} images\n")
print("⏳ Starting auto-labeling...\n")

labeled_count = 0
skipped_count = 0
total_detections = 0

for img_path in image_files:
    print(f"Processing: {img_path.name}... ", end="")

    try:
        # Run model
        results = model(str(img_path), conf=CONFIDENCE_THRESHOLD, verbose=False)

        # Get image dimensions
        img = Image.open(img_path)
        img_w, img_h = img.size

        # Create label file
        label_path = output_labels / f"{img_path.stem}.txt"
        detections_found = 0

        with open(label_path, 'w') as f:
            for result in results:
                if result.boxes is not None and len(result.boxes) > 0:
                    for box in result.boxes:
                        # Get box coordinates (xyxy format)
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])

                        # Convert to YOLO format (normalized xywh)
                        x_center = ((x1 + x2) / 2) / img_w
                        y_center = ((y1 + y2) / 2) / img_h
                        width = (x2 - x1) / img_w
                        height = (y2 - y1) / img_h

                        # Write to label file
                        f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
                        detections_found += 1

        if detections_found > 0:
            # Copy image to output
            shutil.copy(img_path, output_images / img_path.name)
            print(f"✓ {detections_found} detections")
            labeled_count += 1
            total_detections += detections_found
        else:
            # No detections - still copy but mark it
            shutil.copy(img_path, output_images / img_path.name)
            print(f"⚠️  0 detections (image copied, maar geen label)")
            skipped_count += 1

    except Exception as e:
        print(f"❌ Error: {e}")
        skipped_count += 1

# =====================================================
# SUMMARY
# =====================================================
print("\n" + "="*80)
print("📊 AUTO-LABELING VOLTOOID")
print("="*80)
print(f"✓ Images met detecties: {labeled_count}")
print(f"⚠️  Images zonder detecties: {skipped_count}")
print(f"🎯 Totaal detecties: {total_detections}")
print(f"📁 Output: {output_dir}/")
print("="*80)

# =====================================================
# NEXT STEPS
# =====================================================
print("\n💡 VOLGENDE STAPPEN:\n")
print("1. REVIEW DE LABELS:")
print(f"   - Open {output_dir}/ in een label viewer")
print(f"   - Controleer of de bounding boxes correct zijn")
print(f"   - Corrigeer fouten handmatig (bv. in LabelImg of Roboflow)\n")

print("2. VOEG HANDMATIGE ANNOTATIES TOE:")
print(f"   - Images zonder detecties ({skipped_count} stuks) moeten handmatig gelabeld worden")
print(f"   - Nieuwe objecten die het model nog niet kent moet je handmatig annoteren\n")

print("3. UPLOAD NAAR ROBOFLOW (optioneel):")
print(f"   - Ga naar je Roboflow project")
print(f"   - Upload images + labels uit {output_dir}/")
print(f"   - Roboflow herkent automatisch YOLO format\n")

print("4. TRAIN NIEUW MODEL:")
print(f"   - Gebruik de gelabelde data voor training")
print(f"   - Zie training/Werkplek_Inspectie_Detection.ipynb\n")

print("="*80)
print("✅ Klaar! Veel succes met annoteren!")
print("="*80)
