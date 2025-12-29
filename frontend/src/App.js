import React, { useState, useRef, useCallback, useEffect } from 'react';
import Webcam from 'react-webcam';
import axios from 'axios';
import './App.css';
import { rotateImage } from './imageUtils';
// History is now integrated in Admin - Training Data tab
import Admin from './Admin';

// API URL - HTTP backend, HTTPS frontend (mixed content toegestaan in dev)
const API_URL = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : `http://${window.location.hostname}:8000`;

function App() {
  const webcamRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const imageRef = useRef(null);
  const streamRef = useRef(null);

  // Views
  const [currentView, setCurrentView] = useState('inspect'); // 'inspect', 'history', 'admin'

  // Workplaces
  const [workplaces, setWorkplaces] = useState([]);
  const [selectedWorkplace, setSelectedWorkplace] = useState(null);
  const [hasActiveModel, setHasActiveModel] = useState(false);

  // Operator interface is always inspection mode (only workplaces with models are shown)
  // Model type (classification/detection) wordt beheerd in Admin interface

  // Single photo mode
  const [testImage, setTestImage] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState(null);
  const [cameraMode, setCameraMode] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [privacyWarning, setPrivacyWarning] = useState(null);
  const [useNativeCamera, setUseNativeCamera] = useState(false);

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

  // Start camera when video element is ready
  useEffect(() => {
    if (cameraMode && useNativeCamera && videoRef.current && !streamRef.current) {
      const startCamera = async () => {
        try {
          const constraints = {
            video: {
              facingMode: 'environment',
              width: { ideal: 1920 },
              height: { ideal: 1080 }
            },
            audio: false
          };

          const stream = await navigator.mediaDevices.getUserMedia(constraints);
          streamRef.current = stream;

          if (videoRef.current) {
            videoRef.current.srcObject = stream;
            await videoRef.current.play();
          }
        } catch (error) {
          console.error('Camera error:', error);
          alert('Kon camera niet starten: ' + error.message);
          setCameraMode(false);
          setUseNativeCamera(false);
        }
      };
      startCamera();
    }

    return () => {
      if (!cameraMode && streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
    };
  }, [cameraMode, useNativeCamera]);

  // Model type wordt beheerd in Admin - operators gebruiken actieve model

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
      // Als error status 403 is, betekent het dat er personen zijn gedetecteerd
      if (error.response && error.response.status === 403) {
        const message = error.response.data.detail || 'Privacy waarschuwing: Persoon gedetecteerd. Foto wordt niet getoond.';
        console.log('Setting privacy warning:', message);
        setPrivacyWarning(message);
        // Verberg waarschuwing na 5 seconden
        setTimeout(() => {
          console.log('Hiding privacy warning');
          setPrivacyWarning(null);
        }, 5000);
        throw new Error('PRIVACY_BLOCKED');
      }
      console.error('Blur preview error:', error);
      throw error;
    }
  };

  // Start native camera stream
  const startNativeCamera = () => {
    setUseNativeCamera(true);
    setCameraMode(true);
  };

  // Stop native camera stream
  const stopNativeCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  };

  // Capture foto van webcam (beide native en react-webcam)
  const capturePhoto = useCallback(async () => {
    let imageSrc;

    // Als we native camera gebruiken
    if (useNativeCamera && videoRef.current) {
      const canvas = document.createElement('canvas');
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(videoRef.current, 0, 0);
      imageSrc = canvas.toDataURL('image/jpeg');

      stopNativeCamera();
    } else if (webcamRef.current) {
      // React-webcam fallback
      imageSrc = webcamRef.current.getScreenshot();
    }

    if (!imageSrc) {
      alert('Kon geen foto maken. Probeer opnieuw.');
      return;
    }

    try {
      const blurred = await blurPhotoPreview(imageSrc);
      setCameraMode(false);
      setUseNativeCamera(false);
      setTestImage(blurred);
    } catch (error) {
      console.log('Foto geblokkeerd vanwege privacy');
      setCameraMode(false);
      setUseNativeCamera(false);
    }
  }, [useNativeCamera, videoRef, webcamRef]);

  // Upload single photo
  const handleSinglePhotoUpload = async (event) => {
    const file = event.target.files[0];
    if (file) {
      console.log('File selected:', file.name, file.size, file.type);
      setLoadingPreview(true);

      const reader = new FileReader();
      reader.onloadend = async () => {
        console.log('File read complete, starting blur check...');
        try {
          const blurred = await blurPhotoPreview(reader.result);
          console.log('Blur check passed, showing image');
          setTestImage(blurred);
        } catch (error) {
          // Foto wordt niet getoond als er personen zijn gedetecteerd
          console.log('Foto geblokkeerd vanwege privacy:', error);
        } finally {
          setLoadingPreview(false);
          // Reset file input zodat je opnieuw kan uploaden
          event.target.value = '';
        }
      };
      reader.onerror = (error) => {
        console.error('FileReader error:', error);
        setLoadingPreview(false);
        event.target.value = '';
        alert('Fout bij het lezen van het bestand');
      };
      reader.readAsDataURL(file);
    }
  };

  // Batch upload removed - only in Admin

  // Roteer foto (90 graden rechtsom)
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
    setUploadProgress(0);

    // Generate unique session ID
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    // Start SSE connection for progress updates
    const eventSource = new EventSource(`${API_URL}/api/inspect/progress/${sessionId}`);

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setUploadProgress(data.progress);

      if (data.done) {
        eventSource.close();
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
    };

    try {
      const blob = await (await fetch(testImage)).blob();
      const formData = new FormData();
      formData.append('file', blob, 'test.jpg');
      formData.append('blur_faces', 'true');
      formData.append('workplace_id', selectedWorkplace.id);
      formData.append('session_id', sessionId);  // Add session ID
      // Confidence threshold komt uit werkplek instellingen
      const threshold = selectedWorkplace.confidence_threshold || 0.25;
      formData.append('confidence_threshold', threshold.toString());

      // Use XMLHttpRequest for upload
      const response = await new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        // Handle completion
        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(JSON.parse(xhr.responseText));
          } else if (xhr.status === 403) {
            // Privacy error - persoon gedetecteerd
            const response = JSON.parse(xhr.responseText);
            const error = new Error(response.detail || 'Privacy waarschuwing: Persoon gedetecteerd');
            error.isPrivacyError = true;
            reject(error);
          } else {
            reject(new Error(`HTTP ${xhr.status}: ${xhr.statusText}`));
          }
        });

        xhr.addEventListener('error', () => reject(new Error('Network error')));
        xhr.addEventListener('abort', () => reject(new Error('Upload aborted')));

        xhr.open('POST', `${API_URL}/api/inspect`);
        xhr.send(formData);
      });

      setResults(response);

      // Debug detection results
      if (response.detection) {
        console.log('🔍 Detection Results:', response.detection);
        if (response.detection.debug) {
          console.log('📊 Debug Info:', response.detection.debug);
        }
      }

      // Draw bounding boxes if detection mode and boxes exist
      if (response.detection && response.detection.bounding_boxes) {
        console.log(`📦 Drawing ${response.detection.bounding_boxes.length} bounding boxes`);
        drawBoundingBoxes(response.detection.bounding_boxes);
      }

      // Scroll naar de foto's grid zodat de bovenkant van de foto's zichtbaar blijft
      setTimeout(() => {
        const photosGrid = document.querySelector('.photos-grid');
        if (photosGrid) {
          photosGrid.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 100);
    } catch (error) {
      console.error('Error:', error);
      eventSource.close();

      if (error.isPrivacyError) {
        // Privacy error - toon alleen rode banner
        setPrivacyWarning(error.message);
        setTimeout(() => setPrivacyWarning(null), 6000);
      } else {
        alert('Error tijdens analyse: ' + (error.message || 'Onbekende fout'));
      }
    } finally {
      setAnalyzing(false);
      setUploadProgress(0);
    }
  };

  // Draw bounding boxes on canvas overlay
  const drawBoundingBoxes = useCallback((boxes) => {
    if (!canvasRef.current || !imageRef.current) return;

    const canvas = canvasRef.current;
    const image = imageRef.current;
    const ctx = canvas.getContext('2d');

    // Get natural and container dimensions
    const naturalWidth = image.naturalWidth;
    const naturalHeight = image.naturalHeight;
    const containerWidth = image.offsetWidth;
    const containerHeight = image.offsetHeight;

    // Calculate actual rendered size (accounting for object-fit: contain)
    const naturalRatio = naturalWidth / naturalHeight;
    const containerRatio = containerWidth / containerHeight;

    let renderedWidth, renderedHeight, offsetX, offsetY;

    if (naturalRatio > containerRatio) {
      // Image is wider - fits to width
      renderedWidth = containerWidth;
      renderedHeight = containerWidth / naturalRatio;
      offsetX = 0;
      offsetY = (containerHeight - renderedHeight) / 2;
    } else {
      // Image is taller - fits to height
      renderedHeight = containerHeight;
      renderedWidth = containerHeight * naturalRatio;
      offsetX = (containerWidth - renderedWidth) / 2;
      offsetY = 0;
    }

    // Set canvas size to match container
    canvas.width = containerWidth;
    canvas.height = containerHeight;

    // Calculate scale factors based on rendered size
    const scaleX = renderedWidth / naturalWidth;
    const scaleY = renderedHeight / naturalHeight;

    // Clear previous drawings
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Color mapping for different objects
    const colors = {
      'hamer': '#FF6B6B',
      'schaar': '#4ECDC4',
      'sleutel': '#FFE66D'
    };

    // Draw each bounding box
    boxes.forEach(box => {
      const { x1, y1, x2, y2 } = box.bbox;
      const color = colors[box.object] || '#667eea';

      // Scale coordinates to rendered size and add offset
      const scaledX1 = (x1 * scaleX) + offsetX;
      const scaledY1 = (y1 * scaleY) + offsetY;
      const scaledX2 = (x2 * scaleX) + offsetX;
      const scaledY2 = (y2 * scaleY) + offsetY;

      // Draw rectangle with thicker border and shadow for better visibility
      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
      ctx.shadowBlur = 4;
      ctx.strokeRect(scaledX1, scaledY1, scaledX2 - scaledX1, scaledY2 - scaledY1);

      // Reset shadow voor text
      ctx.shadowColor = 'transparent';
      ctx.shadowBlur = 0;

      // Draw label background
      const label = `${box.object} (${(box.confidence * 100).toFixed(0)}%)`;
      ctx.font = 'bold 18px Arial';  // Grotere text: 16px → 18px
      const textMetrics = ctx.measureText(label);
      const textHeight = 22;  // Hoger: 20 → 22

      ctx.fillStyle = color;
      ctx.fillRect(scaledX1, scaledY1 - textHeight - 4, textMetrics.width + 10, textHeight + 4);

      // Draw label text with shadow for better readability
      ctx.shadowColor = 'rgba(0, 0, 0, 0.8)';
      ctx.shadowBlur = 2;
      ctx.fillStyle = '#FFFFFF';
      ctx.fillText(label, scaledX1 + 5, scaledY1 - 8);

      // Reset shadow
      ctx.shadowColor = 'transparent';
      ctx.shadowBlur = 0;
    });
  }, []);

  // Training data functions removed - moved to Admin only

  // Reset
  const reset = () => {
    setTestImage(null);
    setResults(null);
    setCameraMode(false);

    // Clear canvas
    if (canvasRef.current) {
      const ctx = canvasRef.current.getContext('2d');
      ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
    }
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
          <button onClick={() => setCurrentView('admin')} className="admin-btn" title="Instellingen">
            ⚙️
          </button>
        </div>
        <h1>Werkplek Inspectie AI</h1>
        <p>AI-powered kwaliteitscontrole</p>
      </header>

      {/* Privacy Warning Banner */}
      {privacyWarning && (
        <div className="privacy-warning-banner">
          <span className="warning-icon">⚠️</span>
          <span>{privacyWarning}</span>
        </div>
      )}

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
                        {useNativeCamera ? (
                          <video
                            ref={videoRef}
                            className="webcam"
                            autoPlay
                            playsInline
                            muted
                          />
                        ) : (
                          <Webcam
                            audio={false}
                            ref={webcamRef}
                            screenshotFormat="image/jpeg"
                            className="webcam"
                            videoConstraints={{ facingMode: 'environment' }}
                          />
                        )}
                        {selectedWorkplace.reference_photo && (
                          <div className="camera-ghost-frame">
                            {selectedWorkplace.whiteboard_region ? (
                              <div
                                className="whiteboard-highlight"
                                style={{
                                  left: `${selectedWorkplace.whiteboard_region.x1 * 100}%`,
                                  top: `${selectedWorkplace.whiteboard_region.y1 * 100}%`,
                                  width: `${(selectedWorkplace.whiteboard_region.x2 - selectedWorkplace.whiteboard_region.x1) * 100}%`,
                                  height: `${(selectedWorkplace.whiteboard_region.y2 - selectedWorkplace.whiteboard_region.y1) * 100}%`
                                }}
                              >
                                <img
                                  src={`${API_URL}${selectedWorkplace.reference_photo}`}
                                  alt="Ghost reference"
                                  className="whiteboard-ghost-image"
                                  style={{
                                    position: 'absolute',
                                    left: `${-selectedWorkplace.whiteboard_region.x1 / (selectedWorkplace.whiteboard_region.x2 - selectedWorkplace.whiteboard_region.x1) * 100}%`,
                                    top: `${-selectedWorkplace.whiteboard_region.y1 / (selectedWorkplace.whiteboard_region.y2 - selectedWorkplace.whiteboard_region.y1) * 100}%`,
                                    width: `${1 / (selectedWorkplace.whiteboard_region.x2 - selectedWorkplace.whiteboard_region.x1) * 100}%`,
                                    height: `${1 / (selectedWorkplace.whiteboard_region.y2 - selectedWorkplace.whiteboard_region.y1) * 100}%`
                                  }}
                                />
                              </div>
                            ) : (
                              <img
                                src={`${API_URL}${selectedWorkplace.reference_photo}`}
                                alt="Ghost reference"
                                className="ghost-reference-image"
                              />
                            )}
                          </div>
                        )}
                        <button onClick={capturePhoto} className="capture-button">
                          Maak Foto
                        </button>
                      </div>
                    ) : testImage ? (
                      <div className="test-image-wrapper">
                        <img
                          src={testImage}
                          alt="Test"
                          className="preview-image"
                          ref={imageRef}
                          onLoad={() => {
                            // Redraw bounding boxes after image loads
                            if (results && results.detection && results.detection.bounding_boxes) {
                              drawBoundingBoxes(results.detection.bounding_boxes);
                            }
                          }}
                        />
                        <canvas
                          ref={canvasRef}
                          className="bounding-box-canvas"
                        />
                        {analyzing && <div className="scan-overlay"></div>}
                        {results && (
                          <div className={`result-overlay ${results.step1_classification.status}`}>
                            <div className="result-icon">
                              {results.step1_classification.status === 'ok' ? '✓' : '✗'}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="placeholder">
                        <p>Maak een foto of upload</p>
                      </div>
                    )}
                  </div>
                  <div className="button-group">
                    {!cameraMode && !testImage && !loadingPreview && (
                      <>
                        <button onClick={startNativeCamera} className="camera-button">
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
                    {testImage && !analyzing && !results && (
                      <button onClick={reset} className="reset-button">
                        Nieuwe Foto
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Analyse Button */}
              {testImage && !results && (
                <button
                  onClick={analyzeWorkplace}
                  disabled={analyzing}
                  className={`analyze-button ${analyzing ? 'analyzing' : ''}`}
                >
                  {analyzing
                    ? `${Math.round(uploadProgress)}%`
                    : 'Start Analyse'
                  }
                </button>
              )}

              {/* Resultaten (Zonder duplicate foto) */}
              {results && (
                <div className="results-section">
                  {/* Probleem & Oplossing - alleen bij NOK */}
                  {results.model_type === 'detection' && results.step1_classification.status === 'nok' && (
                    <div className="problem-solution-container">
                      <div className="problem-section">
                        <h3>Wat Ontbreekt</h3>
                        {results.step2_analysis.missing_items.length > 0 && (
                          <ul className="missing-items-list">
                            {results.step2_analysis.missing_items.map((item, idx) => (
                              <li key={idx}>{item}</li>
                            ))}
                          </ul>
                        )}
                      </div>

                      <div className="solution-section">
                        <h3>Wat Te Doen</h3>
                        {results.step3_suggestions.length > 0 && (
                          <div className="action-list">
                            {results.step3_suggestions.map((suggestion, idx) => (
                              <div key={idx} className="action-item">
                                {suggestion.action}
                              </div>
                            ))}
                          </div>
                        )}
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
