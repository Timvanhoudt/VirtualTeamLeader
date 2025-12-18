"""
Script to generate updated Colab notebook with ImageFolder format
Run this to create: Werkplek_Inspectie_Training_UPDATED.ipynb
"""

import json

# Complete notebook structure
notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 🔧 Werkplek Inspectie AI - YOLO Training (UPDATED)\\n",
                "\\n",
                "Training notebook voor Google Colab - **ImageFolder format**\\n",
                "\\n",
                "**✅ UPDATES:**\\n",
                "- ImageFolder format (YOLOv8 modern style)\\n",
                "- 7 classes support\\n",
                "- No data.yaml needed\\n",
                "\\n",
                "**⚠️ BELANGRIJK: Zet Runtime op GPU!**\\n",
                "- Runtime → Change runtime type → GPU (T4)"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## 1️⃣ Setup Omgeving"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["# Check GPU\\n", "!nvidia-smi"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Installeer dependencies\\n",
                "!pip install ultralytics opencv-python pillow -q"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Imports\\n",
                "import os\\n",
                "import shutil\\n",
                "from pathlib import Path\\n",
                "import random\\n",
                "from ultralytics import YOLO\\n",
                "import torch\\n",
                "\\n",
                "print(f\\"✅ PyTorch versie: {torch.__version__}\\")\\n",
                "print(f\\"✅ CUDA beschikbaar: {torch.cuda.is_available()}\\")\\n",
                "if torch.cuda.is_available():\\n",
                "    print(f\\"✅ GPU: {torch.cuda.get_device_name(0)}\\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 2️⃣ Upload Dataset\\n",
                "\\n",
                "**Optie A: Vanuit Google Drive**\\n",
                "**Optie B: Direct ZIP upload**"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# OPTIE A: Mount Google Drive\\n",
                "from google.colab import drive\\n",
                "drive.mount('/content/drive')\\n",
                "\\n",
                "# Pas aan naar jouw Drive locatie\\n",
                "DATASET_SOURCE = '/content/drive/MyDrive/AI afbeeldingen'\\n",
                "\\n",
                "# Kopieer naar Colab\\n",
                "!cp -r \\"{DATASET_SOURCE}\\" /content/dataset_raw\\n",
                "print(\\"✅ Dataset gekopieerd\\")"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# OPTIE B: ZIP Upload\\n",
                "from google.colab import files\\n",
                "import zipfile\\n",
                "\\n",
                "print(\\"Upload je dataset_raw.zip...\\")\\n",
                "uploaded = files.upload()\\n",
                "\\n",
                "for filename in uploaded.keys():\\n",
                "    if filename.endswith('.zip'):\\n",
                "        with zipfile.ZipFile(filename, 'r') as zip_ref:\\n",
                "            zip_ref.extractall('/content/dataset_raw')\\n",
                "        print(f\\"✅ {filename} uitgepakt\\")"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["# Check dataset\\n", "!ls -la /content/dataset_raw"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## 3️⃣ Prepareer Dataset (ImageFolder format)"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Dataset configuratie\\n",
                "RAW_DATA_DIR = Path(\\"/content/dataset_raw\\")\\n",
                "OUTPUT_DIR = Path(\\"/content/yolo_dataset\\")\\n",
                "TRAIN_SPLIT = 0.8\\n",
                "\\n",
                "# 7 Classes (class 6 heeft mogelijk geen data)\\n",
                "CLASS_MAPPING = {\\n",
                "    \\"Afbeeldingen OK\\": 0,\\n",
                "    \\"Afbeeldingen NOK alles weg\\": 1,\\n",
                "    \\"Afbeeldingen NOK hamer weg\\": 2,\\n",
                "    \\"Afbeeldingen NOK schaar weg\\": 3,\\n",
                "    \\"Afbeeldingen NOK schaar en sleutel weg\\": 4,\\n",
                "    \\"Afbeeldingen NOK sleutel weg\\": 5,\\n",
                "    \\"Afbeeldingen NOK alleen sleutel\\": 6\\n",
                "}\\n",
                "\\n",
                "CLASS_NAMES = [\\n",
                "    \\"ok\\",\\n",
                "    \\"nok_alles_weg\\",\\n",
                "    \\"nok_hamer_weg\\",\\n",
                "    \\"nok_schaar_weg\\",\\n",
                "    \\"nok_schaar_sleutel_weg\\",\\n",
                "    \\"nok_sleutel_weg\\",\\n",
                "    \\"nok_alleen_sleutel\\"\\n",
                "]"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Prepareer dataset - ImageFolder format\\n",
                "def create_yolo_dataset():\\n",
                "    \\"\\"\\"Converteer naar YOLO ImageFolder format\\"\\"\\"\\n",
                "    \\n",
                "    # Verwijder oude output\\n",
                "    if OUTPUT_DIR.exists():\\n",
                "        shutil.rmtree(OUTPUT_DIR)\\n",
                "    \\n",
                "    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)\\n",
                "    \\n",
                "    # Maak class folders: 0_ok, 1_nok_alles_weg, etc.\\n",
                "    for split in ['train', 'val']:\\n",
                "        for idx, name in enumerate(CLASS_NAMES):\\n",
                "            folder_name = f\\"{idx}_{name}\\"\\n",
                "            (OUTPUT_DIR / split / folder_name).mkdir(parents=True, exist_ok=True)\\n",
                "    \\n",
                "    print(\\"✅ Directory structuur (ImageFolder)\\\\n\\")\\n",
                "    \\n",
                "    # Verzamel images\\n",
                "    all_images = []\\n",
                "    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}\\n",
                "    \\n",
                "    for folder_name, class_id in CLASS_MAPPING.items():\\n",
                "        possible_paths = [\\n",
                "            RAW_DATA_DIR / folder_name,\\n",
                "            RAW_DATA_DIR / \\"AI afbeeldingen\\" / folder_name,\\n",
                "        ]\\n",
                "        \\n",
                "        folder_path = None\\n",
                "        for path in possible_paths:\\n",
                "            if path.exists():\\n",
                "                folder_path = path\\n",
                "                break\\n",
                "        \\n",
                "        if not folder_path:\\n",
                "            print(f\\"⚠️  Folder niet gevonden: {folder_name}\\")\\n",
                "            continue\\n",
                "        \\n",
                "        images = [f for f in folder_path.glob('*') if f.suffix.lower() in image_extensions]\\n",
                "        print(f\\"✅ {folder_name}: {len(images)} afbeeldingen (class {class_id})\\")\\n",
                "        \\n",
                "        for img_path in images:\\n",
                "            all_images.append((img_path, class_id))\\n",
                "    \\n",
                "    # Shuffle en split\\n",
                "    random.seed(42)\\n",
                "    random.shuffle(all_images)\\n",
                "    \\n",
                "    split_idx = int(len(all_images) * TRAIN_SPLIT)\\n",
                "    train_images = all_images[:split_idx]\\n",
                "    val_images = all_images[split_idx:]\\n",
                "    \\n",
                "    print(f\\"\\\\n✅ Split: {len(train_images)} train, {len(val_images)} val\\\\n\\")\\n",
                "    \\n",
                "    # Kopieer naar class folders\\n",
                "    for split_name, image_list in [('train', train_images), ('val', val_images)]:\\n",
                "        for idx, (img_path, class_id) in enumerate(image_list):\\n",
                "            class_name = CLASS_NAMES[class_id]\\n",
                "            folder_name = f\\"{class_id}_{class_name}\\"\\n",
                "            new_name = f\\"{split_name}_{idx}_{img_path.name}\\"\\n",
                "            dst_img = OUTPUT_DIR / split_name / folder_name / new_name\\n",
                "            shutil.copy2(img_path, dst_img)\\n",
                "    \\n",
                "    print(\\"✅ Dataset klaar! (ImageFolder format)\\")\\n",
                "    return OUTPUT_DIR\\n",
                "\\n",
                "# Run\\n",
                "print(\\"🚀 Start preprocessing...\\\\n\\")\\n",
                "dataset_path = create_yolo_dataset()\\n",
                "print(f\\"\\\\n✅ Dataset pad: {dataset_path}\\")"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Check resultaat\\n",
                "!ls -la /content/yolo_dataset/train/ | head -10"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## 4️⃣ Train YOLO Model"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Training configuratie\\n",
                "EPOCHS = 100\\n",
                "BATCH_SIZE = 16\\n",
                "IMAGE_SIZE = 640\\n",
                "MODEL_SIZE = 'n'  # nano (snel)\\n",
                "\\n",
                "print(\\"🎯 Configuratie:\\")\\n",
                "print(f\\"   Epochs: {EPOCHS}\\")\\n",
                "print(f\\"   Batch: {BATCH_SIZE}\\")\\n",
                "print(f\\"   Size: {IMAGE_SIZE}\\")\\n",
                "print(f\\"   Model: YOLOv8{MODEL_SIZE}-cls\\")"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Laad model\\n",
                "model = YOLO(f'yolov8{MODEL_SIZE}-cls.pt')\\n",
                "print(\\"✅ YOLO model geladen\\")"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# TRAIN! 🚀\\n",
                "print(\\"\\\\n\\" + \\"=\\"*60)\\n",
                "print(\\"🚀 START TRAINING\\")\\n",
                "print(\\"=\\"*60 + \\"\\\\n\\")\\n",
                "\\n",
                "results = model.train(\\n",
                "    data=str(dataset_path),  # ImageFolder path!\\n",
                "    epochs=EPOCHS,\\n",
                "    batch=BATCH_SIZE,\\n",
                "    imgsz=IMAGE_SIZE,\\n",
                "    device=0,\\n",
                "    project='runs/classify',\\n",
                "    name='werkplek_inspect',\\n",
                "    exist_ok=True,\\n",
                "    patience=20,\\n",
                "    save=True,\\n",
                "    plots=True,\\n",
                "    verbose=True,\\n",
                "    val=True\\n",
                ")\\n",
                "\\n",
                "print(\\"\\\\n✅ TRAINING COMPLEET!\\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## 5️⃣ Evaluatie"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Metrics\\n",
                "metrics = model.val()\\n",
                "print(f\\"\\\\nTop-1 Accuracy: {metrics.top1:.2%}\\")\\n",
                "print(f\\"Top-5 Accuracy: {metrics.top5:.2%}\\")"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Plots\\n",
                "from IPython.display import Image, display\\n",
                "\\n",
                "plots = ['results.png', 'confusion_matrix.png']\\n",
                "for plot in plots:\\n",
                "    path = f'runs/classify/werkplek_inspect/{plot}'\\n",
                "    if os.path.exists(path):\\n",
                "        print(f\\"\\\\n{plot}:\\")\\n",
                "        display(Image(filename=path, width=800))"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## 6️⃣ Download Model"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Copy best model\\n",
                "!cp runs/classify/werkplek_inspect/weights/best.pt /content/werkplek_classifier.pt\\n",
                "\\n",
                "size_mb = os.path.getsize('/content/werkplek_classifier.pt') / (1024*1024)\\n",
                "print(f\\"✅ Model: werkplek_classifier.pt ({size_mb:.1f} MB)\\")"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Download\\n",
                "from google.colab import files\\n",
                "files.download('/content/werkplek_classifier.pt')\\n",
                "print(\\"✅ Model gedownload!\\")\\n",
                "print(\\"\\\\n📁 Plaats in: backend/models/werkplek_classifier.pt\\")"
            ]
        }
    ],
    "metadata": {
        "accelerator": "GPU",
        "colab": {
            "gpuType": "T4",
            "provenance": []
        },
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.10.0"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 0
}

# Write notebook
output_file = "Werkplek_Inspectie_Training_UPDATED.ipynb"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=2, ensure_ascii=False)

print(f"✅ Created: {output_file}")
print("\\n📋 Upload dit bestand naar Google Colab")
print("⚡ Zet Runtime op GPU (T4)")
print("🚀 Run alle cellen")
