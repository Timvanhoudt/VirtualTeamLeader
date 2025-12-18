"""
Test de backend API met echte validation images
Dit simuleert wat de frontend doet
"""

import requests
from pathlib import Path

API_URL = "http://localhost:8000"

def test_with_validation_image():
    """Test API met een validation image"""

    print("="*70)
    print("TEST BACKEND API MET VALIDATION IMAGES")
    print("="*70)

    # Test verschillende classes
    test_images = [
        ("data/processed/yolo_dataset/val/0_ok/val_24_goed00346.jpg", "0_ok"),
        ("data/processed/yolo_dataset/val/2_nok_hamer_weg/val_22_hamerweg00001.jpg", "2_nok_hamer_weg"),
        ("data/processed/yolo_dataset/val/3_nok_schaar_weg/val_10_schaarweg00286.jpg", "3_nok_schaar_weg"),
        ("data/processed/yolo_dataset/val/1_nok_alles_weg/val_2_scene00061.jpg", "1_nok_alles_weg"),
    ]

    for img_path, expected_class in test_images:
        path = Path(img_path)

        if not path.exists():
            print(f"[X] Image niet gevonden: {path}")
            continue

        print(f"\n{'='*70}")
        print(f"Testing: {path.name}")
        print(f"Expected: {expected_class}")
        print(f"{'='*70}")

        # Upload naar API
        with open(path, 'rb') as f:
            files = {'file': (path.name, f, 'image/jpeg')}

            try:
                response = requests.post(
                    f"{API_URL}/api/inspect",
                    files=files,
                    params={'blur_faces': False}  # Disable face blur voor test
                )

                if response.status_code == 200:
                    data = response.json()

                    # Extract resultaten
                    class_id = data['step2_analysis']['class_id']
                    class_name = data['step2_analysis']['class_name']
                    confidence = data['step1_classification']['confidence']
                    status = data['step1_classification']['status']

                    is_correct = class_name.lower().replace(" ", "_").replace("-", "") == expected_class.lower().replace("_", "")

                    status_icon = "[OK]" if is_correct else "[FAIL]"

                    print(f"\n{status_icon} Result:")
                    print(f"  Class: {class_name}")
                    print(f"  Confidence: {confidence:.2%}")
                    print(f"  Status: {status.upper()}")

                    if 'privacy' in data:
                        print(f"  Faces detected: {data['privacy']['faces_detected']}")

                else:
                    print(f"[X] API Error: {response.status_code}")
                    print(response.text)

            except Exception as e:
                print(f"[X] Request failed: {e}")

    print(f"\n{'='*70}")
    print("Test voltooid!")
    print(f"{'='*70}")


if __name__ == "__main__":
    test_with_validation_image()
