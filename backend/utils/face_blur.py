"""
Face Blur Utility voor Privacy
Detecteert en blurt gezichten in afbeeldingen
"""

import cv2
import numpy as np
from pathlib import Path
import urllib.request
import os

class FaceBlurrer:
    def __init__(self):
        """Initialiseer face detection met YuNet (modern DNN model)"""
        # Download YuNet model als het niet bestaat
        model_path = Path("models/face_detection_yunet_2023mar.onnx")
        model_path.parent.mkdir(exist_ok=True)

        if not model_path.exists():
            print("📥 Downloading YuNet face detection model...")
            url = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
            try:
                urllib.request.urlretrieve(url, str(model_path))
                print("✓ YuNet model downloaded")
            except Exception as e:
                print(f"⚠ Could not download YuNet model: {e}")
                print("Falling back to Haar Cascade...")
                # Fallback naar Haar Cascade
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                self.face_cascade = cv2.CascadeClassifier(cascade_path)
                self.detector = None
                if not self.face_cascade.empty():
                    print("✓ Haar Cascade face detection model geladen (fallback)")
                return

        # Initialiseer YuNet detector
        try:
            self.detector = cv2.FaceDetectorYN.create(
                str(model_path),
                "",
                (320, 320),
                score_threshold=0.6,  # Hogere threshold = minder false positives
                nms_threshold=0.3,
                top_k=5000
            )
            self.face_cascade = None
            print("✓ YuNet face detection model geladen")
        except Exception as e:
            print(f"⚠ Could not load YuNet: {e}")
            print("Falling back to Haar Cascade...")
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            self.detector = None
            if not self.face_cascade.empty():
                print("✓ Haar Cascade face detection model geladen (fallback)")

    def blur_faces(self, image, blur_strength=99):
        """
        Detecteer en blur gezichten in een afbeelding

        Args:
            image: numpy array (BGR format van OpenCV)
            blur_strength: sterkte van de blur (oneven getal, hoger = meer blur)

        Returns:
            Afbeelding met geblurde gezichten, aantal gezichten
        """
        # Zorg dat blur strength een oneven getal is
        if blur_strength % 2 == 0:
            blur_strength += 1

        # Gebruik YuNet als beschikbaar, anders Haar Cascade
        if self.detector is not None:
            # YuNet detection - resize voor snelheid
            height, width = image.shape[:2]

            # Resize naar max 640px voor snellere face detection
            max_size = 640
            if width > max_size or height > max_size:
                scale = max_size / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                resized = cv2.resize(image, (new_width, new_height))
            else:
                resized = image
                scale = 1.0

            # Set input size voor detector
            self.detector.setInputSize((resized.shape[1], resized.shape[0]))

            # Detecteer gezichten op verkleinde foto
            _, faces = self.detector.detect(resized)

            if faces is None:
                return image, 0

            # Blur elk gedetecteerd gezicht
            for face in faces:
                # YuNet geeft: x, y, w, h, score, landmarks...
                x, y, w, h = face[:4].astype(int)

                # Schaal terug naar originele resolutie
                if scale != 1.0:
                    x = int(x / scale)
                    y = int(y / scale)
                    w = int(w / scale)
                    h = int(h / scale)

                # Vergroot de ROI iets voor betere coverage
                padding = 20
                x1 = max(0, x - padding)
                y1 = max(0, y - padding)
                x2 = min(width, x + w + padding)
                y2 = min(height, y + h + padding)

                # Extract face region
                face_region = image[y1:y2, x1:x2]

                if face_region.size > 0:
                    # Blur het gezicht
                    blurred_face = cv2.GaussianBlur(face_region, (blur_strength, blur_strength), 0)
                    # Plaats terug in originele afbeelding
                    image[y1:y2, x1:x2] = blurred_face

            return image, len(faces)
        else:
            # Fallback: Haar Cascade detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)

            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=4,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )

            # Blur elk gedetecteerd gezicht
            for (x, y, w, h) in faces:
                padding = 20
                x1 = max(0, x - padding)
                y1 = max(0, y - padding)
                x2 = min(image.shape[1], x + w + padding)
                y2 = min(image.shape[0], y + h + padding)

                face_region = image[y1:y2, x1:x2]
                if face_region.size > 0:
                    blurred_face = cv2.GaussianBlur(face_region, (blur_strength, blur_strength), 0)
                    image[y1:y2, x1:x2] = blurred_face

            return image, len(faces)

    def process_image_file(self, input_path, output_path=None, blur_strength=99):
        """
        Verwerk een afbeeldingsbestand en blur gezichten

        Args:
            input_path: pad naar input afbeelding
            output_path: pad voor output (optioneel)
            blur_strength: sterkte van blur

        Returns:
            aantal gedetecteerde gezichten
        """
        # Lees afbeelding
        image = cv2.imread(str(input_path))

        if image is None:
            raise ValueError(f"Kon afbeelding niet laden: {input_path}")

        # Blur gezichten
        blurred_image, face_count = self.blur_faces(image, blur_strength)

        # Opslaan
        if output_path:
            cv2.imwrite(str(output_path), blurred_image)
        else:
            # Overschrijf origineel
            cv2.imwrite(str(input_path), blurred_image)

        return face_count

    def process_folder(self, input_folder, output_folder=None, blur_strength=99):
        """
        Verwerk alle afbeeldingen in een folder

        Args:
            input_folder: folder met afbeeldingen
            output_folder: output folder (optioneel)
            blur_strength: sterkte van blur

        Returns:
            statistieken dict
        """
        input_path = Path(input_folder)
        stats = {
            'total_images': 0,
            'total_faces': 0,
            'images_with_faces': 0
        }

        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}

        # Maak output folder als nodig
        if output_folder:
            output_path = Path(output_folder)
            output_path.mkdir(parents=True, exist_ok=True)

        # Verwerk alle afbeeldingen
        for img_file in input_path.rglob('*'):
            if img_file.suffix.lower() in image_extensions:
                stats['total_images'] += 1

                try:
                    if output_folder:
                        # Behoud relatieve folder structuur
                        rel_path = img_file.relative_to(input_path)
                        out_file = output_path / rel_path
                        out_file.parent.mkdir(parents=True, exist_ok=True)
                    else:
                        out_file = None

                    face_count = self.process_image_file(img_file, out_file, blur_strength)

                    if face_count > 0:
                        stats['images_with_faces'] += 1
                        stats['total_faces'] += face_count
                        print(f"✓ {img_file.name}: {face_count} gezicht(en) geblurd")

                except Exception as e:
                    print(f"⚠ Error bij {img_file.name}: {e}")

        return stats


def main():
    """Test face blur functionaliteit"""
    print("🎭 Face Blur Test\n")

    blurrer = FaceBlurrer()

    # Test op de dataset
    input_folder = Path("../data/raw")
    output_folder = Path("../data/processed/blurred")

    print(f"Input: {input_folder}")
    print(f"Output: {output_folder}\n")

    stats = blurrer.process_folder(input_folder, output_folder)

    print("\n" + "="*50)
    print("STATISTIEKEN")
    print("="*50)
    print(f"Totaal afbeeldingen: {stats['total_images']}")
    print(f"Afbeeldingen met gezichten: {stats['images_with_faces']}")
    print(f"Totaal gezichten geblurd: {stats['total_faces']}")
    print("="*50)


if __name__ == "__main__":
    main()
