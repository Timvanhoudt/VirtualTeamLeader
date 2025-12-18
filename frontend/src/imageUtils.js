// Image utility functies voor auto-rotatie

/**
 * Detecteer en corrigeer foto oriëntatie
 * Rooteert foto's automatisch naar de juiste stand
 */
export const normalizeImageOrientation = async (file) => {
  return new Promise((resolve) => {
    const reader = new FileReader();

    reader.onload = (e) => {
      const img = new Image();

      img.onload = () => {
        // Maak canvas voor rotatie
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');

        // DISABLED: Automatische rotatie veroorzaakt classificatie problemen
        // Het model is getraind op originele foto orientaties
        let width = img.width;
        let height = img.height;

        // Gebruik foto zoals het is - GEEN automatische rotatie
        canvas.width = width;
        canvas.height = height;
        ctx.drawImage(img, 0, 0);

        // Convert terug naar data URL - gebruik maximale kwaliteit voor model accuracy
        const normalizedDataUrl = canvas.toDataURL('image/jpeg', 1.0);
        resolve(normalizedDataUrl);
      };

      img.src = e.target.result;
    };

    reader.readAsDataURL(file);
  });
};

/**
 * Roteer een image data URL met een specifieke hoek
 */
export const rotateImage = (dataUrl, degrees) => {
  return new Promise((resolve) => {
    const img = new Image();

    img.onload = () => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');

      const rad = degrees * Math.PI / 180;
      const sin = Math.abs(Math.sin(rad));
      const cos = Math.abs(Math.cos(rad));

      // Nieuwe canvas dimensies na rotatie
      const newWidth = img.width * cos + img.height * sin;
      const newHeight = img.width * sin + img.height * cos;

      canvas.width = newWidth;
      canvas.height = newHeight;

      ctx.translate(newWidth / 2, newHeight / 2);
      ctx.rotate(rad);
      ctx.drawImage(img, -img.width / 2, -img.height / 2);

      resolve(canvas.toDataURL('image/jpeg', 1.0));
    };

    img.src = dataUrl;
  });
};

/**
 * Voeg rotatie knoppen toe voor handmatige correctie
 */
export const addRotationControls = () => {
  // Deze functie kan gebruikt worden om UI knoppen toe te voegen
  return {
    rotate90: (dataUrl) => rotateImage(dataUrl, 90),
    rotate180: (dataUrl) => rotateImage(dataUrl, 180),
    rotate270: (dataUrl) => rotateImage(dataUrl, 270),
  };
};
