"""
Direct model test - Test het model zonder de FastAPI backend
Dit helpt ons te zien of het probleem in het model zit of in de processing
"""

from ultralytics import YOLO
import cv2
from pathlib import Path
import numpy as np

# Class mapping - zoals in de backend
CLASS_INFO = {
    0: "0_ok",
    1: "1_nok_alles_weg",
    2: "2_nok_hamer_weg",
    3: "3_nok_schaar_weg",
    4: "4_nok_schaar_sleutel_weg",
    5: "5_nok_sleutel_weg",
    6: "6_nok_alleen_sleutel"
}

def test_model_on_validation():
    """Test het model op alle validation images"""

    print("="*70)
    print("🧪 DIRECT MODEL TEST - Validation Set")
    print("="*70)

    # Laad model
    model_path = Path("backend/models/werkplek_classifier.pt")
    print(f"\n📥 Laden model: {model_path}")
    model = YOLO(str(model_path))

    print(f"✓ Model geladen!")
    print(f"Model classes: {model.names}")
    print()

    # Zoek alle validation images
    val_dir = Path("data/processed/yolo_dataset/val")

    if not val_dir.exists():
        print(f"❌ Validation directory niet gevonden: {val_dir}")
        return

    # Test per class
    results_summary = {}

    for class_id, class_name in CLASS_INFO.items():
        class_dir = val_dir / class_name

        if not class_dir.exists():
            print(f"⚠ Class directory niet gevonden: {class_dir}")
            continue

        images = list(class_dir.glob("*.jpg"))

        if not images:
            print(f"⚠ Geen images gevonden in: {class_dir}")
            continue

        print(f"\n{'='*70}")
        print(f"Testing: {class_name} ({len(images)} images)")
        print(f"{'='*70}")

        correct = 0
        total = len(images)

        for img_path in images[:5]:  # Test eerste 5 van elke class
            # Lees afbeelding
            img = cv2.imread(str(img_path))

            if img is None:
                print(f"❌ Kon afbeelding niet laden: {img_path.name}")
                continue

            # Predict
            results = model(img, verbose=False)

            for result in results:
                pred_class = result.probs.top1
                confidence = result.probs.top1conf.item()

                is_correct = (pred_class == class_id)

                status = "✓" if is_correct else "✗"

                print(f"{status} {img_path.name:30} | "
                      f"Expected: {class_name:30} | "
                      f"Got: {CLASS_INFO[pred_class]:30} | "
                      f"Conf: {confidence:.2%}")

                if is_correct:
                    correct += 1

        accuracy = (correct / min(5, total)) * 100 if total > 0 else 0
        results_summary[class_name] = {
            'correct': correct,
            'total': min(5, total),
            'accuracy': accuracy
        }

    # Print summary
    print(f"\n{'='*70}")
    print("📊 SUMMARY")
    print(f"{'='*70}")

    total_correct = 0
    total_tested = 0

    for class_name, stats in results_summary.items():
        print(f"{class_name:30} | {stats['correct']}/{stats['total']} correct | {stats['accuracy']:.1f}% accuracy")
        total_correct += stats['correct']
        total_tested += stats['total']

    overall_accuracy = (total_correct / total_tested * 100) if total_tested > 0 else 0

    print(f"{'='*70}")
    print(f"Overall Accuracy: {total_correct}/{total_tested} = {overall_accuracy:.2f}%")
    print(f"{'='*70}")


def test_single_image(image_path):
    """Test een enkele afbeelding"""
    print(f"\n🔍 Testing single image: {image_path}")

    model_path = Path("backend/models/werkplek_classifier.pt")
    model = YOLO(str(model_path))

    img = cv2.imread(str(image_path))

    if img is None:
        print(f"❌ Kon afbeelding niet laden")
        return

    print(f"Image shape: {img.shape}")

    results = model(img, verbose=True)

    for result in results:
        probs = result.probs

        print(f"\nTop predictions:")
        print(f"{'='*70}")

        # Get top 5 predictions
        top5_indices = probs.top5
        top5_conf = probs.top5conf

        for idx, conf in zip(top5_indices, top5_conf):
            class_name = CLASS_INFO.get(idx, "Unknown")
            print(f"{class_name:30} | Confidence: {conf:.2%}")


if __name__ == "__main__":
    # Test validation set
    test_model_on_validation()

    # Test een specifieke afbeelding als je wilt
    # test_single_image("data/processed/yolo_dataset/val/0_ok/val_1_ok00001.jpg")
