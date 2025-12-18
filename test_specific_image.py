"""
Test een specifieke foto en laat alle prediction scores zien
"""

import requests
from pathlib import Path
import sys

API_URL = "http://localhost:8000"

def test_image(image_path):
    """Test een specifieke foto en toon alle class probabilities"""

    path = Path(image_path)

    if not path.exists():
        print(f"[X] Foto niet gevonden: {path}")
        return

    print("="*70)
    print(f"TESTING: {path.name}")
    print("="*70)

    # Upload naar API
    with open(path, 'rb') as f:
        files = {'file': (path.name, f, 'image/jpeg')}

        try:
            response = requests.post(
                f"{API_URL}/api/inspect",
                files=files,
                params={'blur_faces': 'false'}
            )

            if response.status_code == 200:
                data = response.json()

                print(f"\nRESULTAAT:")
                print(f"  Predicted Class: {data['step2_analysis']['class_name']}")
                print(f"  Confidence: {data['step1_classification']['confidence']:.2%}")
                print(f"  Status: {data['step1_classification']['status'].upper()}")

                if data['step2_analysis']['missing_items']:
                    print(f"  Missing: {', '.join(data['step2_analysis']['missing_items'])}")

                print(f"\nCheck de backend logs voor alle class scores!")

            else:
                print(f"[X] API Error: {response.status_code}")
                print(response.text)

        except Exception as e:
            print(f"[X] Request failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_specific_image.py <path_to_image>")
        print("\nExample:")
        print("  python test_specific_image.py data/processed/yolo_dataset/val/2_nok_hamer_weg/val_22_hamerweg00001.jpg")
        sys.exit(1)

    test_image(sys.argv[1])
