#!/bin/bash

echo "===================================="
echo "WERKPLEK INSPECTIE AI - QUICK START"
echo "===================================="
echo ""

# Check if model exists
if [ ! -f "backend/models/werkplek_classifier.pt" ]; then
    echo "[!] Model niet gevonden!"
    echo ""
    echo "Train eerst je model in Google Colab:"
    echo "1. Open Werkplek_Inspectie_Training.ipynb in Colab"
    echo "2. Run alle cellen"
    echo "3. Download werkplek_classifier.pt"
    echo "4. Plaats in backend/models/"
    echo ""
    echo "Zie COLAB_TRAINING_GUIDE.md voor instructies"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[!] Python niet gevonden!"
    echo "Installeer Python 3.8+ eerst"
    exit 1
fi

echo "[*] Model gevonden!"
echo "[*] Python gevonden!"
echo ""

# Check if backend dependencies installed
echo "[*] Checking backend dependencies..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "[*] Installing backend dependencies..."
    cd backend
    pip3 install -r requirements.txt
    cd ..
else
    echo "[*] Backend dependencies OK"
fi

echo ""
echo "===================================="
echo "KIES ACTIE:"
echo "===================================="
echo "1. Start Backend API (FastAPI)"
echo "2. Start Frontend (React)"
echo "3. Start Beide (Backend + Frontend)"
echo "4. Test Setup"
echo "5. Exit"
echo ""

read -p "Kies optie (1-5): " choice

case $choice in
    1)
        echo ""
        echo "[*] Starting Backend..."
        cd backend
        python3 main.py
        ;;
    2)
        echo ""
        echo "[*] Starting Frontend..."
        cd frontend

        if [ ! -d "node_modules" ]; then
            echo "[*] Installing frontend dependencies..."
            npm install
        fi

        npm start
        ;;
    3)
        echo ""
        echo "[*] Starting Backend in background..."
        cd backend
        python3 main.py &
        BACKEND_PID=$!
        cd ..

        echo "[*] Waiting for backend to start..."
        sleep 3

        echo "[*] Starting Frontend..."
        cd frontend

        if [ ! -d "node_modules" ]; then
            echo "[*] Installing frontend dependencies..."
            npm install
        fi

        npm start

        # Cleanup on exit
        kill $BACKEND_PID 2>/dev/null
        ;;
    4)
        echo ""
        echo "[*] Running setup test..."
        python3 test_setup.py
        echo ""
        ;;
    5)
        echo ""
        echo "Bye!"
        exit 0
        ;;
    *)
        echo "Ongeldige keuze"
        exit 1
        ;;
esac
