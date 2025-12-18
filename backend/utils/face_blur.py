"""
Face Blur Utility voor Privacy
Detecteert en blurt gezichten in afbeeldingen
"""

import cv2
import numpy as np
from pathlib import Path

class FaceBlurrer:
    def __init__(self):
        """Initialiseer face detection met OpenCV Haar Cascade"""
        # Probeer het Haar Cascade model te laden
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

        if self.face_cascade.empty():
            raise Exception("❌ Kon face detection model niet laden")

        print("✓ Face detection model geladen")

    def blur_faces(self, image, blur_strength=99):
        """
        Detecteer en blur gezichten in een afbeelding

        Args:
            image: numpy array (BGR format van OpenCV)
            blur_strength: sterkte van de blur (oneven getal, hoger = meer blur)

        Returns:
            Afbeelding met geblurde gezichten
        """
        # Zorg dat blur strength een oneven getal is
        if blur_strength % 2 == 0:
            blur_strength += 1

        # Convert naar grijswaarden voor detectie
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detecteer gezichten
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        # Blur elk gedetecteerd gezicht
        for (x, y, w, h) in faces:
            # Vergroot de ROI iets voor betere coverage
            padding = 20
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(image.shape[1], x + w + padding)
            y2 = min(image.shape[0], y + h + padding)

            # Extract face region
            face_region = image[y1:y2, x1:x2]

            # Blur het gezicht
            blurred_face = cv2.GaussianBlur(face_region, (blur_strength, blur_strength), 0)

            # Plaats terug in originele afbeelding
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
