@echo off
echo ====================================
echo WERKPLEK INSPECTIE AI - QUICK START
echo ====================================
echo.

:: Check if model exists
if not exist "backend\models\werkplek_classifier.pt" (
    echo [!] Model niet gevonden!
    echo.
    echo Train eerst je model in Google Colab:
    echo 1. Open Werkplek_Inspectie_Training.ipynb in Colab
    echo 2. Run alle cellen
    echo 3. Download werkplek_classifier.pt
    echo 4. Plaats in backend\models\
    echo.
    echo Zie COLAB_TRAINING_GUIDE.md voor instructies
    pause
    exit
)

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python niet gevonden!
    echo Installeer Python 3.8+ eerst
    pause
    exit
)

echo [*] Model gevonden!
echo [*] Python gevonden!
echo.

:: Check if backend dependencies installed
echo [*] Checking backend dependencies...
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo [*] Installing backend dependencies...
    cd backend
    pip install -r requirements.txt
    cd ..
) else (
    echo [*] Backend dependencies OK
)

echo.
echo ====================================
echo KIES ACTIE:
echo ====================================
echo 1. Start Backend API (FastAPI)
echo 2. Start Frontend (React)
echo 3. Start Beide (Backend + Frontend)
echo 4. Test Setup
echo 5. Exit
echo.

set /p choice="Kies optie (1-5): "

if "%choice%"=="1" goto backend
if "%choice%"=="2" goto frontend
if "%choice%"=="3" goto both
if "%choice%"=="4" goto test
if "%choice%"=="5" goto end

:backend
echo.
echo [*] Starting Backend...
cd backend
python main.py
goto end

:frontend
echo.
echo [*] Starting Frontend...
cd frontend

:: Check if node_modules exists
if not exist "node_modules" (
    echo [*] Installing frontend dependencies...
    call npm install
)

call npm start
goto end

:both
echo.
echo [*] Starting Backend in new window...
start cmd /k "cd backend && python main.py"
timeout /t 3 >nul

echo [*] Starting Frontend...
cd frontend

if not exist "node_modules" (
    echo [*] Installing frontend dependencies...
    call npm install
)

call npm start
goto end

:test
echo.
echo [*] Running setup test...
python test_setup.py
echo.
pause
goto end

:end
echo.
echo Bye!
