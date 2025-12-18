import React, { useState, useRef, useCallback, useEffect } from 'react';
import Webcam from 'react-webcam';
import axios from 'axios';
import './App.css';
import { rotateImage } from './imageUtils';
// History is now integrated in Admin - Training Data tab
import Admin from './Admin';

// API URL - werkt zowel lokaal als op tablet
const API_URL = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : `http://${window.location.hostname}:8000`;

function App() {
  const webcamRef = useRef(null);

  // Views
  const [currentView, setCurrentView] = useState('inspect'); // 'inspect', 'history', 'admin'

  // Workplaces
  const [workplaces, setWorkplaces] = useState([]);
  const [selectedWorkplace, setSelectedWorkplace] = useState(null);
  const [hasActiveModel, setHasActiveModel] = useState(false);

  // Operator interface is always inspection mode (only workplaces with models are shown)

  // Single photo mode
  const [testImage, setTestImage] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState(null);
  const [cameraMode, setCameraMode] = useState(false);

  // Batch collection mode removed - moved to Admin only

  // Load workplaces on mount - ONLY with active models for operator
  useEffect(() => {
    loadWorkplacesWithModels();
  }, []);

  // Check if selected workplace has active model
  useEffect(() => {
    if (selectedWorkplace) {
      checkActiveModel(selectedWorkplace.id);
    }
  }, [selectedWorkplace]);

  const loadWorkplacesWithModels = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/workplaces`);
      if (response.data.success) {
        // Filter only workplaces with active models for operator interface
        const workplacesWithModels = [];

        for (const workplace of response.data.workplaces) {
          const modelsResponse = await axios.get(`${API_URL}/api/workplaces/${workplace.id}/models`);
          if (modelsResponse.data.success) {
            const hasActiveModel = modelsResponse.data.models.some(m => m.status === 'active');
            if (hasActiveModel) {
              workplacesWithModels.push(workplace);
            }
          }
        }

        setWorkplaces(workplacesWithModels);
        if (workplacesWithModels.length > 0) {
          setSelectedWorkplace(workplacesWithModels[0]);
        }
      }
    } catch (error) {
      console.error('Error loading workplaces:', error);
    }
  };

  const checkActiveModel = async (workplaceId) => {
    try {
      const response = await axios.get(`${API_URL}/api/workplaces/${workplaceId}/models`);
      if (response.data.success) {
        const activeModel = response.data.models.find(m => m.status === 'active');
        setHasActiveModel(!!activeModel);
      }
    } catch (error) {
      console.error('Error checking model:', error);
      setHasActiveModel(false);
    }
  };

  // Blur foto preview via backend
  const blurPhotoPreview = async (imageData) => {
    try {
      const blob = await (await fetch(imageData)).blob();
      const formData = new FormData();
      formData.append('file', blob, 'photo.jpg');

      const response = await axios.post(`${API_URL}/api/blur-preview`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      return response.data.blurred_image;
    } catch (error) {
      console.error('Blur preview error:', error);
      return imageData;
    }
  };

  // Capture foto van webcam
  const capturePhoto = useCallback(async () => {
    const imageSrc = webcamRef.current.getScreenshot();
    setCameraMode(false);

    const blurred = await blurPhotoPreview(imageSrc);
    setTestImage(blurred);
  }, [webcamRef]);

  // Upload single photo
  const handleSinglePhotoUpload = async (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = async () => {
        const blurred = await blurPhotoPreview(reader.result);
        setTestImage(blurred);
      };
      reader.readAsDataURL(file);
    }
  };

  // Batch upload removed - only in Admin

  // Roteer foto (90 graden rechtsom)
  const handleRotateImage = async () => {
    if (testImage) {
      const rotated = await rotateImage(testImage, 90);
      setTestImage(rotated);
    }
  };

  // Analyse werkplek (inspection mode)
  const analyzeWorkplace = async () => {
    if (!testImage) {
      alert('Upload of maak eerst een testfoto!');
      return;
    }

    if (!hasActiveModel) {
      alert('Geen actief model voor deze werkplek. Upload eerst een model in Admin.');
      return;
    }

    setAnalyzing(true);
    setResults(null);

    try {
      const blob = await (await fetch(testImage)).blob();
      const formData = new FormData();
      formData.append('file', blob, 'test.jpg');
      formData.append('blur_faces', 'true');
      formData.append('workplace_id', selectedWorkplace.id);

      const response = await axios.post(`${API_URL}/api/inspect`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setResults(response.data);
    } catch (error) {
      console.error('Error:', error);
      alert('Error tijdens analyse: ' + (error.response?.data?.detail || error.message));
    } finally {
      setAnalyzing(false);
    }
  };

  // Training data functions removed - moved to Admin only

  // Reset
  const reset = () => {
    setTestImage(null);
    setResults(null);
    setCameraMode(false);
  };

  // Show Admin view
  if (currentView === 'admin') {
    return <Admin onBack={() => setCurrentView('inspect')} />;
  }

  // History view removed - now in Admin → Training Data

  // Show Inspect view
  return (
    <div className="App">
      <header className="header">
        <div className="header-buttons">
          <button onClick={() => setCurrentView('admin')} className="admin-btn">
            Admin Dashboard
          </button>
        </div>
        <h1>Werkplek Inspectie AI</h1>
        <p>AI-powered kwaliteitscontrole</p>
      </header>

      <div className="container">
        {/* Werkplek Selectie */}
        <div className="section">
          <label className="label">SELECTEER WERKPLEK</label>
          {workplaces.length > 0 ? (
            <select
              className="dropdown"
              value={selectedWorkplace?.id || ''}
              onChange={(e) => {
                const wp = workplaces.find(w => w.id === parseInt(e.target.value));
                setSelectedWorkplace(wp);
              }}
            >
              {workplaces.map(wp => (
                <option key={wp.id} value={wp.id}>{wp.name}</option>
              ))}
            </select>
          ) : (
            <p className="no-workplaces">Geen werkplekken met actieve modellen. Configureer werkplekken in Admin.</p>
          )}

          {selectedWorkplace && (
            <div className="workplace-info">
              <div className="mode-badge" data-mode="inspection">
                Inspectie Mode (Model Actief)
              </div>
              <p className="workplace-items">
                Items: {selectedWorkplace.items.join(', ')}
              </p>
            </div>
          )}
        </div>

        {!selectedWorkplace && (
          <div className="empty-state">
            <p>Geen werkplekken met actieve modellen gevonden.</p>
            <p>Voeg werkplekken toe en koppel modellen via het Admin dashboard.</p>
          </div>
        )}

        {selectedWorkplace && (
          <>
            {/* Inspection Mode */}
            <div className="inspection-mode-section">
              <h2 className="section-title">Werkplek Inspecteren</h2>

              {/* 2-Column Photo Comparison */}
              <div className="photos-grid">
                {/* Reference Photo (Left) */}
                <div className="photo-card">
                  <div className="card-header">
                    <h3>Referentie Foto</h3>
                    <span className="badge">MASTER</span>
                  </div>
                  <div className="image-container">
                    {selectedWorkplace.reference_photo ? (
                      <img
                        src={`${API_URL}${selectedWorkplace.reference_photo}`}
                        alt="Referentie"
                        className="preview-image"
                      />
                    ) : (
                      <div className="placeholder">
                        <p>Geen referentie foto</p>
                        <small>Upload in Admin</small>
                      </div>
                    )}
                  </div>
                </div>

                {/* Test Photo (Right) */}
                <div className="photo-card">
                  <div className="card-header">
                    <h3>Huidige Foto</h3>
                    {testImage && <span className="badge success">PRIVACY OK</span>}
                  </div>
                  <div className="image-container">
                    {cameraMode ? (
                      <div className="camera-container">
                        <Webcam
                          audio={false}
                          ref={webcamRef}
                          screenshotFormat="image/jpeg"
                          className="webcam"
                          videoConstraints={{ facingMode: 'environment' }}
                        />
                        <button onClick={capturePhoto} className="capture-button">
                          Maak Foto
                        </button>
                      </div>
                    ) : testImage ? (
                      <div className="test-image-wrapper">
                        <img src={testImage} alt="Test" className="preview-image" />
                        {analyzing && <div className="scan-overlay"></div>}
                      </div>
                    ) : (
                      <div className="placeholder">
                        <p>Maak een foto of upload</p>
                      </div>
                    )}
                  </div>
                  <div className="button-group">
                    {!cameraMode && !testImage && (
                      <>
                        <button onClick={() => setCameraMode(true)} className="camera-button">
                          Open Camera
                        </button>
                        <input
                          type="file"
                          accept="image/*"
                          capture="environment"
                          onChange={handleSinglePhotoUpload}
                          className="file-input"
                          id="test-upload"
                        />
                        <label htmlFor="test-upload" className="upload-button secondary">
                          Upload Foto
                        </label>
                      </>
                    )}
                    {testImage && !analyzing && (
                      <>
                        <button onClick={handleRotateImage} className="rotate-button">
                          Roteer 90°
                        </button>
                        <button onClick={reset} className="reset-button">
                          Nieuwe Foto
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* Analyse Button */}
              {testImage && !results && (
                <button onClick={analyzeWorkplace} disabled={analyzing} className="analyze-button">
                  {analyzing ? (
                    <span className="spinner">Analyseren...</span>
                  ) : (
                    'Start Analyse'
                  )}
                </button>
              )}

              {/* Resultaten (Zonder duplicate foto) */}
              {results && (
                <div className="results-section">
                  <h2 className="results-title">Analyse Resultaten</h2>

                  <div className={`result-card ${results.step1_classification.status}`}>
                    <h3>Stap 1: Basis Controle</h3>
                    <div className="result-status">
                      <span className={`status-badge ${results.step1_classification.status}`}>
                        {results.step1_classification.result}
                      </span>
                      <span className="confidence">
                        Zekerheid: {(results.step1_classification.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  {results.step1_classification.status === 'nok' && (
                    <div className="result-card nok">
                      <h3>Stap 2: Probleem Detectie</h3>
                      <p className="description">{results.step2_analysis.description}</p>
                      {results.step2_analysis.missing_items.length > 0 && (
                        <div className="missing-items">
                          <p><strong>Ontbrekende items:</strong></p>
                          <ul>
                            {results.step2_analysis.missing_items.map((item, idx) => (
                              <li key={idx}>{item}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}

                  {results.step3_suggestions.length > 0 && (
                    <div className="result-card suggestions">
                      <h3>Stap 3: Herstel Acties</h3>
                      <div className="suggestions-list">
                        {results.step3_suggestions.map((suggestion, idx) => (
                          <div key={idx} className="suggestion-item">
                            <span className="suggestion-icon">Info</span>
                            <div>
                              <strong>{suggestion.item}</strong>
                              <p>{suggestion.action}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {results.privacy && results.privacy.faces_detected > 0 && (
                    <div className="privacy-info">
                      <p>Privacy beschermd: {results.privacy.faces_blurred} gezicht(en) geblurd</p>
                    </div>
                  )}

                  <button onClick={reset} className="new-check-button">
                    Nieuwe Controle
                  </button>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      <footer className="footer">
        <p>Powered by YOLO AI | Privacy Protected</p>
      </footer>
    </div>
  );
}

export default App;
