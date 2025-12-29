import React, { useState, useEffect } from 'react';
import './Admin.css';
import './History.css'; // Import History styling voor Production Review
import axios from 'axios';

// API URL
const API_URL = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : `http://${window.location.hostname}:8000`;

function Admin({ onBack }) {
  const [activeTab, setActiveTab] = useState('workplaces');
  const [workplaces, setWorkplaces] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dataRefreshTrigger, setDataRefreshTrigger] = useState(0); // Trigger voor data refresh
  const [selectedWorkplace, setSelectedWorkplace] = useState(null); // Shared selected workplace across tabs
  const [toasts, setToasts] = useState([]); // Toast notificaties

  // Toast notificatie functie
  const showToast = (message, type = 'success') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4000);
  };

  // Load workplaces bij mount
  useEffect(() => {
    loadWorkplaces();
  }, []);

  // Auto-select eerste werkplek als default
  useEffect(() => {
    if (workplaces.length > 0 && !selectedWorkplace) {
      setSelectedWorkplace(workplaces[0]);
    }
  }, [workplaces, selectedWorkplace]);

  const loadWorkplaces = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/api/workplaces`);
      if (response.data.success) {
        setWorkplaces(response.data.workplaces);
      }
    } catch (error) {
      console.error('Error loading workplaces:', error);
      alert('Fout bij laden werkplekken');
    }
    setLoading(false);
  };

  return (
    <div className="admin-container">
      {/* Header */}
      <div className="admin-header">
        <div className="header-left">
          <button onClick={onBack} className="back-btn">
            ← Terug
          </button>
          <h1>Admin Dashboard</h1>
        </div>
        <p>Beheer werkplekken, training data en modellen</p>
      </div>

      {/* Tabs */}
      <div className="admin-tabs">
        <button
          className={activeTab === 'workplaces' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('workplaces')}
        >
          Werkplekken Beheer
        </button>
        <button
          className={activeTab === 'review' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('review')}
        >
          Beoordelings Analyse
        </button>
        <button
          className={activeTab === 'training' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('training')}
        >
          Training Data
        </button>
        <button
          className={activeTab === 'performance' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('performance')}
        >
          Model Prestaties
        </button>
      </div>

      {/* Content */}
      <div className="admin-content">
        {activeTab === 'workplaces' && (
          <WorkplacesManagementTab
            workplaces={workplaces}
            loading={loading}
            onRefresh={loadWorkplaces}
            showToast={showToast}
          />
        )}

        {activeTab === 'review' && (
          <ReviewAnalysisTab
            workplaces={workplaces}
            loading={loading}
            selectedWorkplace={selectedWorkplace}
            onWorkplaceChange={setSelectedWorkplace}
            onDataUpdate={() => setDataRefreshTrigger(prev => prev + 1)}
            showToast={showToast}
          />
        )}

        {activeTab === 'training' && (
          <TrainingDataTab
            workplaces={workplaces}
            loading={loading}
            selectedWorkplace={selectedWorkplace}
            onWorkplaceChange={setSelectedWorkplace}
            refreshTrigger={dataRefreshTrigger}
            showToast={showToast}
          />
        )}

        {activeTab === 'performance' && (
          <ModelPerformanceTab
            workplaces={workplaces}
            loading={loading}
            selectedWorkplace={selectedWorkplace}
            onWorkplaceChange={setSelectedWorkplace}
            showToast={showToast}
          />
        )}
      </div>

      {/* Toast Notificaties */}
      <div className="toast-container">
        {toasts.map(toast => (
          <div key={toast.id} className={`toast toast-${toast.type}`}>
            <span className="toast-icon">
              {toast.type === 'success' ? '✓' : toast.type === 'error' ? '✗' : 'ℹ'}
            </span>
            <span className="toast-message">{toast.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ==========================================
// MODEL MANAGEMENT SECTION (voor Werkplekken tab)
// ==========================================
function ModelManagementSection({ workplace, models, onModelsUpdate, showToast }) {
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadData, setUploadData] = useState({
    file: null,
    version: '',
    test_accuracy: '',
    notes: '',
    model_type: 'classification'
  });
  const [uploading, setUploading] = useState(false);

  const activeModel = models.find(m => m.status === 'active');

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file && file.name.endsWith('.pt')) {
      // Extract filename without .pt extension as version
      const originalName = file.name.replace('.pt', '');
      setUploadData({...uploadData, file: file, version: originalName});
    } else {
      alert('Alleen .pt bestanden zijn toegestaan');
      e.target.value = '';
    }
  };

  const handleModelUpload = async (e) => {
    e.preventDefault();
    if (!uploadData.file) {
      alert('Selecteer een model bestand (.pt)');
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', uploadData.file);
      if (uploadData.version) formData.append('version', uploadData.version);
      if (uploadData.test_accuracy) formData.append('test_accuracy', uploadData.test_accuracy);
      if (uploadData.notes) formData.append('notes', uploadData.notes);
      formData.append('model_type', uploadData.model_type);

      const response = await axios.post(`${API_URL}/api/workplaces/${workplace.id}/models`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (response.data.success) {
        showToast(`Model ${response.data.version} (${response.data.model_type}) geüpload! Bestand: ${response.data.model_path.split('/').pop()}`, 'success');
        setShowUploadModal(false);
        setUploadData({ file: null, version: '', test_accuracy: '', notes: '', model_type: 'classification' });
        onModelsUpdate();
      }
    } catch (error) {
      console.error('Error uploading model:', error);
      showToast('Fout bij uploaden model: ' + (error.response?.data?.detail || error.message), 'error');
    }
    setUploading(false);
  };

  const handleActivateModel = async (modelId) => {
    if (!window.confirm('Dit model activeren? Het huidige actieve model wordt gearchiveerd.')) {
      return;
    }

    try {
      const response = await axios.post(`${API_URL}/api/models/${modelId}/activate`);
      if (response.data.success) {
        showToast('Model geactiveerd!', 'success');
        onModelsUpdate();
      }
    } catch (error) {
      console.error('Error activating model:', error);
      showToast('Fout bij activeren model: ' + (error.response?.data?.detail || error.message), 'error');
    }
  };

  const handleDeleteModel = async (modelId) => {
    if (!window.confirm('⚠️ Dit model permanent verwijderen? Deze actie kan niet ongedaan gemaakt worden.')) {
      return;
    }

    try {
      const response = await axios.delete(`${API_URL}/api/models/${modelId}`);
      if (response.data.success) {
        showToast('Model verwijderd!', 'success');
        onModelsUpdate();
      }
    } catch (error) {
      console.error('Error deleting model:', error);
      showToast('Fout bij verwijderen model: ' + (error.response?.data?.detail || error.message), 'error');
    }
  };

  return (
    <div className="detail-section model-management-section">
      <div className="section-header">
        <h4>🤖 AI Modellen</h4>
        <button onClick={() => setShowUploadModal(true)} className="btn-primary btn-sm">
          ⬆️ Upload Model
        </button>
      </div>

      {/* Active Model Card */}
      {activeModel ? (
        <div className="model-card active" style={{
          padding: '15px',
          background: 'linear-gradient(135deg, #48bb78 0%, #38a169 100%)',
          color: 'white',
          borderRadius: '8px',
          marginBottom: '15px'
        }}>
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
            <div>
              <div className="model-badge" style={{background: 'rgba(255,255,255,0.3)', padding: '4px 8px', borderRadius: '4px', display: 'inline-block', marginBottom: '8px'}}>
                ✅ ACTIEF MODEL
              </div>
              <div><strong>Versie:</strong> {activeModel.version}</div>
              <div><strong>Type:</strong> {activeModel.model_type === 'detection' ? '🔍 Detection' : '📊 Classification'}</div>
              {activeModel.test_accuracy && <div><strong>Accuracy:</strong> {activeModel.test_accuracy}%</div>}
              <div style={{fontSize: '0.9em', opacity: 0.9}}>Geüpload: {new Date(activeModel.uploaded_at).toLocaleString('nl-NL')}</div>
            </div>
          </div>
        </div>
      ) : (
        <div className="empty-state-small" style={{padding: '15px', background: '#fff3cd', borderRadius: '8px', marginBottom: '15px'}}>
          <p>⚠️ Geen actief model. Upload een model of activeer een bestaand model.</p>
        </div>
      )}

      {/* Models List */}
      {models.length > 0 && (
        <details style={{marginTop: '15px'}} open={!activeModel}>
          <summary style={{cursor: 'pointer', fontWeight: 'bold', padding: '8px 0'}}>
            📋 Alle Modellen ({models.length})
          </summary>
          <div className="models-list" style={{marginTop: '10px'}}>
            {models.map(model => (
              <div key={model.id} style={{
                padding: '10px',
                marginBottom: '8px',
                background: model.status === 'active' ? '#f0fff4' : '#f7fafc',
                border: model.status === 'active' ? '2px solid #48bb78' : '1px solid #e2e8f0',
                borderRadius: '6px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <div style={{flex: 1}}>
                  <div style={{fontWeight: 'bold'}}>
                    {model.version}
                    {model.status === 'active' && <span style={{marginLeft: '8px', fontSize: '0.8em', color: '#48bb78'}}>● ACTIEF</span>}
                  </div>
                  <div style={{fontSize: '0.85em', color: '#666'}}>
                    {model.model_type === 'detection' ? '🔍 Detection' : '📊 Classification'}
                    {model.test_accuracy && ` • ${model.test_accuracy}% accuracy`}
                  </div>
                  <div style={{fontSize: '0.75em', color: '#999', marginTop: '4px', fontFamily: 'monospace'}}>
                    📁 {model.model_path ? model.model_path.split('/').pop() : 'Bestand niet beschikbaar'}
                  </div>
                  {model.notes && (
                    <div style={{fontSize: '0.75em', color: '#666', marginTop: '4px', fontStyle: 'italic'}}>
                      💬 {model.notes}
                    </div>
                  )}
                </div>
                <div style={{display: 'flex', gap: '8px'}}>
                  {model.status !== 'active' && (
                    <button
                      onClick={() => handleActivateModel(model.id)}
                      className="btn-secondary btn-sm"
                      style={{fontSize: '0.85em'}}
                    >
                      Activeer
                    </button>
                  )}
                  {model.status !== 'active' && (
                    <button
                      onClick={() => handleDeleteModel(model.id)}
                      className="btn-danger btn-sm"
                      style={{fontSize: '0.85em', background: '#e53e3e', color: 'white'}}
                    >
                      🗑️ Verwijder
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </details>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="modal-overlay" onClick={() => setShowUploadModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Model Uploaden voor {workplace.name}</h2>
            <p style={{color: '#666', marginBottom: '20px'}}>
              Upload een getraind YOLO model (.pt bestand). Het model wordt automatisch uniek benoemd met de werkplek naam.
            </p>

            <form onSubmit={handleModelUpload}>
              <div className="form-group">
                <label>Model Bestand (.pt) *</label>
                <input
                  type="file"
                  accept=".pt"
                  onChange={handleFileSelect}
                  required
                />
                {uploadData.file && (
                  <small className="file-selected" style={{color: '#48bb78'}}>
                    ✓ {uploadData.file.name}
                  </small>
                )}
              </div>

              <div className="form-group">
                <label>Model Type *</label>
                <select
                  value={uploadData.model_type}
                  onChange={(e) => setUploadData({...uploadData, model_type: e.target.value})}
                  required
                >
                  <option value="classification">📊 Classification - Voorspelt hele werkplek</option>
                  <option value="detection">🔍 Detection - Detecteert individuele objecten</option>
                </select>
                <small>Dit model is specifiek voor "{workplace.name}" met items: {workplace.items.join(', ')}</small>
              </div>

              <div className="form-group">
                <label>Versie</label>
                <input
                  type="text"
                  value={uploadData.version}
                  onChange={(e) => setUploadData({...uploadData, version: e.target.value})}
                  placeholder="Wordt automatisch ingevuld met bestandsnaam"
                />
                <small style={{color: '#666'}}>💡 De originele bestandsnaam wordt gebruikt als versie-identificatie</small>
              </div>

              <div className="form-group">
                <label>Test Accuracy (%)</label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="100"
                  value={uploadData.test_accuracy}
                  onChange={(e) => setUploadData({...uploadData, test_accuracy: e.target.value})}
                  placeholder="Bijv. 95.5"
                />
              </div>

              <div className="form-group">
                <label>Notities</label>
                <textarea
                  value={uploadData.notes}
                  onChange={(e) => setUploadData({...uploadData, notes: e.target.value})}
                  placeholder="Training details, dataset size, epochs, etc."
                  rows="3"
                />
              </div>

              <div className="modal-actions">
                <button type="button" onClick={() => setShowUploadModal(false)} className="btn-secondary">
                  Annuleren
                </button>
                <button type="submit" className="btn-primary" disabled={uploading}>
                  {uploading ? 'Uploaden...' : 'Upload Model'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// ==========================================
// TAB 1: WERKPLEKKEN BEHEER
// ==========================================
function WorkplacesManagementTab({ workplaces, loading, onRefresh, showToast }) {
  const [selectedWorkplace, setSelectedWorkplace] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [models, setModels] = useState([]);

  const [newWorkplace, setNewWorkplace] = useState({
    name: '',
    description: '',
    items: ''
  });

  const [editWorkplace, setEditWorkplace] = useState({
    id: null,
    name: '',
    description: '',
    items: ''
  });

  // Laad werkplek details
  const loadWorkplaceDetails = async (workplaceId) => {
    try {
      const response = await axios.get(`${API_URL}/api/workplaces/${workplaceId}`);
      if (response.data.success) {
        setSelectedWorkplace(response.data);
      }

      // Laad ook modellen voor deze werkplek
      const modelsResponse = await axios.get(`${API_URL}/api/workplaces/${workplaceId}/models`);
      if (modelsResponse.data.success) {
        setModels(modelsResponse.data.models);
      }
    } catch (error) {
      console.error('Error loading workplace details:', error);
    }
  };

  // Voeg nieuwe werkplek toe
  const handleAddWorkplace = async (e) => {
    e.preventDefault();
    try {
      const items = newWorkplace.items.split(',').map(item => item.trim()).filter(item => item);

      const response = await axios.post(`${API_URL}/api/workplaces`, {
        name: newWorkplace.name,
        description: newWorkplace.description,
        items: items
      });

      if (response.data.success) {
        showToast('Werkplek aangemaakt!', 'success');
        setShowAddModal(false);
        setNewWorkplace({ name: '', description: '', items: '' });
        onRefresh();
      }
    } catch (error) {
      console.error('Error adding workplace:', error);
      showToast('Fout bij toevoegen werkplek', 'error');
    }
  };

  // Edit werkplek
  const openEditModal = (workplace) => {
    setEditWorkplace({
      id: workplace.id,
      name: workplace.name,
      description: workplace.description || '',
      items: workplace.items.join(', ')
    });
    setShowEditModal(true);
  };

  const handleEditWorkplace = async (e) => {
    e.preventDefault();
    try {
      const items = editWorkplace.items.split(',').map(item => item.trim()).filter(item => item);

      const response = await axios.put(`${API_URL}/api/workplaces/${editWorkplace.id}`, {
        name: editWorkplace.name,
        description: editWorkplace.description,
        items: items
      });

      if (response.data.success) {
        showToast('Werkplek bijgewerkt!', 'success');
        setShowEditModal(false);
        onRefresh();
        if (selectedWorkplace && selectedWorkplace.workplace.id === editWorkplace.id) {
          loadWorkplaceDetails(editWorkplace.id);
        }
      }
    } catch (error) {
      console.error('Error updating workplace:', error);
      showToast('Fout bij bijwerken werkplek', 'error');
    }
  };

  // Verwijder werkplek
  const handleDeleteWorkplace = async (workplaceId) => {
    if (!window.confirm('Weet je zeker dat je deze werkplek wilt verwijderen?')) {
      return;
    }

    try {
      const response = await axios.delete(`${API_URL}/api/workplaces/${workplaceId}`);
      if (response.data.success) {
        showToast('Werkplek verwijderd!', 'success');
        setSelectedWorkplace(null);
        onRefresh();
      }
    } catch (error) {
      console.error('Error deleting workplace:', error);
      showToast('Fout bij verwijderen werkplek', 'error');
    }
  };


  // Upload referentie foto
  const handleReferencePhotoUpload = async (workplaceId, file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API_URL}/api/workplaces/${workplaceId}/reference-photo`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (response.data.success) {
        showToast('Referentie foto geüpload!', 'success');
        loadWorkplaceDetails(workplaceId);
      }
    } catch (error) {
      console.error('Error uploading reference photo:', error);
      showToast('Fout bij uploaden foto', 'error');
    }
  };

  return (
    <div className="workplaces-management-tab">
      <div className="tab-header">
        <h2>Werkplekken Beheer</h2>
        <div className="tab-actions">
          <button onClick={onRefresh} className="btn-secondary" disabled={loading}>
            Ververs
          </button>
          <button onClick={() => setShowAddModal(true)} className="btn-primary">
            + Nieuwe Werkplek
          </button>
        </div>
      </div>

      <div className="workplaces-grid">
        {/* Lijst van werkplekken */}
        <div className="workplaces-list">
          <h3>Alle Werkplekken ({workplaces.length})</h3>
          {loading && <p>Laden...</p>}
          {!loading && workplaces.length === 0 && (
            <p className="empty-state">Geen werkplekken gevonden.</p>
          )}
          {!loading && workplaces.map(workplace => (
            <div
              key={workplace.id}
              className={`workplace-card ${selectedWorkplace?.workplace?.id === workplace.id ? 'selected' : ''}`}
              onClick={() => loadWorkplaceDetails(workplace.id)}
            >
              <h4>{workplace.name}</h4>
              <p>{workplace.description || 'Geen beschrijving'}</p>
              <div className="workplace-items">
                {workplace.items.map((item, idx) => (
                  <span key={idx} className="item-badge">{item}</span>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Details van geselecteerde werkplek */}
        <div className="workplace-details">
          {!selectedWorkplace && (
            <div className="empty-state">
              <p>Selecteer een werkplek om details te zien</p>
            </div>
          )}

          {selectedWorkplace && (
            <>
              <div className="detail-header">
                <h3>{selectedWorkplace.workplace.name}</h3>
                <div className="detail-actions">
                  <button onClick={() => openEditModal(selectedWorkplace.workplace)} className="btn-secondary">
                    Bewerken
                  </button>
                  <button onClick={() => handleDeleteWorkplace(selectedWorkplace.workplace.id)} className="btn-danger">
                    Verwijderen
                  </button>
                </div>
              </div>

              <div className="detail-section">
                <h4>Informatie</h4>
                <p><strong>Beschrijving:</strong> {selectedWorkplace.workplace.description || 'Geen'}</p>
                <p><strong>Items:</strong> {selectedWorkplace.workplace.items.join(', ')}</p>
                <p><strong>Aangemaakt:</strong> {new Date(selectedWorkplace.workplace.created_at).toLocaleString('nl-NL')}</p>
              </div>

              <div className="detail-section">
                <h4>⚙️ Detection Instellingen</h4>
                <div className="form-group">
                  <label style={{display: 'flex', justifyContent: 'space-between', marginBottom: '8px'}}>
                    <span>Confidence Threshold:</span>
                    <strong>{Math.round((selectedWorkplace.workplace.confidence_threshold || 0.25) * 100)}%</strong>
                  </label>
                  <input
                    type="range"
                    min="10"
                    max="90"
                    value={Math.round((selectedWorkplace.workplace.confidence_threshold || 0.25) * 100)}
                    onChange={async (e) => {
                      const newThreshold = parseInt(e.target.value) / 100;
                      try {
                        await axios.put(`${API_URL}/api/workplaces/${selectedWorkplace.workplace.id}`, {
                          confidence_threshold: newThreshold
                        });
                        // Reload workplace details to update UI
                        loadWorkplaceDetails(selectedWorkplace.workplace.id);
                      } catch (error) {
                        console.error('Error updating threshold:', error);
                        alert('Fout bij bijwerken threshold');
                      }
                    }}
                    style={{width: '100%', cursor: 'pointer'}}
                  />
                  <small style={{color: '#666', fontSize: '12px'}}>
                    Minimale confidence voor object detectie. Hogere waarde = meer selectief, minder false positives.
                  </small>
                </div>
              </div>

              <div className="detail-section">
                <h4>Referentie Foto</h4>
                {selectedWorkplace.workplace.reference_photo ? (
                  <div className="reference-photo-container">
                    <img
                      src={`${API_URL}${selectedWorkplace.workplace.reference_photo}`}
                      alt="Referentie"
                      className="reference-photo-preview"
                    />
                    <button
                      onClick={() => document.getElementById(`reference-upload-${selectedWorkplace.workplace.id}`).click()}
                      className="btn-secondary"
                      style={{ marginTop: '10px' }}
                    >
                      Wijzig Foto
                    </button>
                  </div>
                ) : (
                  <div className="no-reference-photo">
                    <p>Geen referentie foto</p>
                    <button
                      onClick={() => document.getElementById(`reference-upload-${selectedWorkplace.workplace.id}`).click()}
                      className="btn-primary"
                    >
                      Upload Referentie Foto
                    </button>
                  </div>
                )}
                <input
                  type="file"
                  accept="image/*"
                  id={`reference-upload-${selectedWorkplace.workplace.id}`}
                  style={{ display: 'none' }}
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      handleReferencePhotoUpload(selectedWorkplace.workplace.id, e.target.files[0]);
                    }
                  }}
                />
              </div>

              {selectedWorkplace.workplace.reference_photo && (
                <WhiteboardRegionSelector
                  workplace={selectedWorkplace.workplace}
                  onRegionSaved={() => loadWorkplaceDetails(selectedWorkplace.workplace.id)}
                  showToast={showToast}
                />
              )}

              <ModelManagementSection
                workplace={selectedWorkplace.workplace}
                models={models}
                onModelsUpdate={() => loadWorkplaceDetails(selectedWorkplace.workplace.id)}
                showToast={showToast}
              />

              <div className="detail-section">
                <h4>Dataset Statistieken</h4>
                <div className="stats-grid">
                  <div className="stat-card">
                    <span className="stat-value">{selectedWorkplace.dataset_stats.total_images}</span>
                    <span className="stat-label">Totaal Images</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{selectedWorkplace.dataset_stats.validated_count}</span>
                    <span className="stat-label">Gelabeld</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{selectedWorkplace.dataset_stats.unvalidated_count}</span>
                    <span className="stat-label">Niet Gelabeld</span>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Nieuwe Werkplek Toevoegen</h2>
            <form onSubmit={handleAddWorkplace}>
              <div className="form-group">
                <label>Naam *</label>
                <input
                  type="text"
                  value={newWorkplace.name}
                  onChange={(e) => setNewWorkplace({...newWorkplace, name: e.target.value})}
                  placeholder="Bijv. Werkplek A - Gereedschap"
                  required
                />
              </div>

              <div className="form-group">
                <label>Beschrijving</label>
                <textarea
                  value={newWorkplace.description}
                  onChange={(e) => setNewWorkplace({...newWorkplace, description: e.target.value})}
                  placeholder="Optionele beschrijving"
                  rows="3"
                />
              </div>

              <div className="form-group">
                <label>Items (komma gescheiden) *</label>
                <input
                  type="text"
                  value={newWorkplace.items}
                  onChange={(e) => setNewWorkplace({...newWorkplace, items: e.target.value})}
                  placeholder="Bijv. hamer, schaar, sleutel"
                  required
                />
                <small>Deze items worden gebruikt als labels voor training</small>
              </div>

              <div className="modal-actions">
                <button type="button" onClick={() => setShowAddModal(false)} className="btn-secondary">
                  Annuleren
                </button>
                <button type="submit" className="btn-primary">
                  Toevoegen
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Werkplek Bewerken</h2>
            <form onSubmit={handleEditWorkplace}>
              <div className="form-group">
                <label>Naam *</label>
                <input
                  type="text"
                  value={editWorkplace.name}
                  onChange={(e) => setEditWorkplace({...editWorkplace, name: e.target.value})}
                  required
                />
              </div>

              <div className="form-group">
                <label>Beschrijving</label>
                <textarea
                  value={editWorkplace.description}
                  onChange={(e) => setEditWorkplace({...editWorkplace, description: e.target.value})}
                  rows="3"
                />
              </div>

              <div className="form-group">
                <label>Items (komma gescheiden) *</label>
                <input
                  type="text"
                  value={editWorkplace.items}
                  onChange={(e) => setEditWorkplace({...editWorkplace, items: e.target.value})}
                  required
                />
              </div>

              <div className="modal-actions">
                <button type="button" onClick={() => setShowEditModal(false)} className="btn-secondary">
                  Annuleren
                </button>
                <button type="submit" className="btn-primary">
                  Opslaan
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}


// ==========================================
// TAB 2: TRAINING DATA
// ==========================================
function TrainingDataTab({ workplaces, loading, refreshTrigger, selectedWorkplace, onWorkplaceChange, showToast }) {
  // Gebruik de shared selectedWorkplace van parent in plaats van lokale state
  const [hasActiveModel, setHasActiveModel] = useState(false);
  const [datasetStats, setDatasetStats] = useState(null);
  const [loadingStats, setLoadingStats] = useState(false);
  const [selectedModelVersion, setSelectedModelVersion] = useState(null);
  const [activeModelVersion, setActiveModelVersion] = useState(null);
  const [activeModelType, setActiveModelType] = useState(null);

  // Check of werkplek actief model heeft + laad beschikbare model versies
  useEffect(() => {
    if (selectedWorkplace) {
      checkActiveModel(selectedWorkplace.id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedWorkplace]);

  // Reload data when refresh trigger changes (na correctie in Review tab)
  useEffect(() => {
    if (selectedWorkplace && selectedModelVersion) {
      console.log('🔄 Refreshing Training Data dashboard...');
      loadDatasetStats(selectedWorkplace.id, selectedModelVersion);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshTrigger]);

  // Reload stats when model version filter changes
  useEffect(() => {
    if (selectedWorkplace && selectedModelVersion !== null) {
      loadDatasetStats(selectedWorkplace.id, selectedModelVersion);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedModelVersion]);

  const checkActiveModel = async (workplaceId) => {
    try {
      const response = await axios.get(`${API_URL}/api/workplaces/${workplaceId}/models`);
      if (response.data.success) {
        const hasActive = response.data.models.some(m => m.status === 'active');
        setHasActiveModel(hasActive);

        // Vind het actieve model en laad alleen zijn data
        const activeModel = response.data.models.find(m => m.status === 'active');
        if (activeModel && activeModel.version) {
          setActiveModelVersion(activeModel.version);
          setActiveModelType(activeModel.model_type); // 'detection' of 'classification'
          setSelectedModelVersion(activeModel.version);
          loadDatasetStats(workplaceId, activeModel.version);
        } else {
          // Geen actief model, toon alle data
          setActiveModelVersion(null);
          setActiveModelType(null);
          setSelectedModelVersion('all');
          loadDatasetStats(workplaceId, 'all');
        }
      }
    } catch (error) {
      console.error('Error checking model:', error);
      setHasActiveModel(false);
      setActiveModelVersion(null);
    }
  };


  const loadDatasetStats = async (workplaceId, modelVersion) => {
    setLoadingStats(true);
    try {
      const params = modelVersion && modelVersion !== 'all' ? `?model_version=${modelVersion}` : '';
      const response = await axios.get(`${API_URL}/api/workplaces/${workplaceId}/dataset-stats${params}`);
      console.log('📊 Dataset stats response:', response.data);
      if (response.data.success) {
        console.log('✅ Stats loaded:', response.data.stats);
        console.log('   - error_types:', response.data.stats.error_types);
        console.log('   - label_distribution:', response.data.stats.label_distribution);
        setDatasetStats(response.data.stats);
      }
    } catch (error) {
      console.error('❌ Error loading dataset stats:', error);
      setDatasetStats(null);
    } finally {
      setLoadingStats(false);
    }
  };

  return (
    <div className="training-data-tab">
      <div className="tab-header">
        <h2>📚 Training Data Management</h2>
        <p style={{color: '#666', fontSize: '14px', marginTop: '8px'}}>
          Beheer en exporteer training data voor model verbetering
        </p>
      </div>

      {/* Werkplek Selector */}
      <div className="workplace-selector" style={{marginBottom: '20px'}}>
        <label style={{fontWeight: 'bold', marginRight: '10px'}}>Selecteer Werkplek:</label>
        <select
          value={selectedWorkplace?.id || ''}
          onChange={(e) => {
            const wp = workplaces.find(w => w.id === parseInt(e.target.value));
            onWorkplaceChange(wp);
            // Model version wordt automatisch gezet in checkActiveModel
          }}
          className="workplace-select"
          style={{padding: '8px 12px', borderRadius: '4px', border: '1px solid #cbd5e0', minWidth: '250px'}}
        >
          <option value="">-- Kies een werkplek --</option>
          {workplaces.map(wp => (
            <option key={wp.id} value={wp.id}>{wp.name}</option>
          ))}
        </select>
      </div>

      {/* Active Model Info */}
      {selectedWorkplace && activeModelVersion && (
        <div className="active-model-info" style={{
          marginBottom: '20px',
          padding: '15px',
          background: 'linear-gradient(135deg, #48bb78 0%, #38a169 100%)',
          borderRadius: '8px',
          border: '2px solid #2f855a',
          color: 'white'
        }}>
          <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
            <div style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
              <span style={{fontSize: '24px'}}>✅</span>
              <div>
                <div style={{fontWeight: 'bold', fontSize: '16px'}}>
                  Actief Model: {activeModelVersion}
                </div>
                <small style={{opacity: 0.9}}>
                  Dashboard toont alleen data van het actieve model
                </small>
              </div>
            </div>
            <button
              onClick={() => {
                console.log('🔄 Manual refresh triggered');
                loadDatasetStats(selectedWorkplace.id, selectedModelVersion);
              }}
              style={{
                background: 'rgba(255,255,255,0.2)',
                border: '2px solid rgba(255,255,255,0.5)',
                color: 'white',
                padding: '8px 16px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: 'bold',
                fontSize: '14px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = 'rgba(255,255,255,0.3)';
                e.target.style.transform = 'scale(1.05)';
              }}
              onMouseLeave={(e) => {
                e.target.style.background = 'rgba(255,255,255,0.2)';
                e.target.style.transform = 'scale(1)';
              }}
            >
              🔄 Refresh Data
            </button>
          </div>
        </div>
      )}

      {/* Warning: No Data for Active Model */}
      {selectedWorkplace && activeModelVersion && datasetStats && datasetStats.total_images === 0 && (
        <div style={{
          marginBottom: '20px',
          padding: '15px',
          background: '#fffaf0',
          borderRadius: '8px',
          border: '2px solid #ed8936',
          color: '#7c2d12'
        }}>
          <div style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
            <span style={{fontSize: '24px'}}>⚠️</span>
            <div>
              <div style={{fontWeight: 'bold', fontSize: '14px', marginBottom: '5px'}}>
                Geen Data voor Actief Model
              </div>
              <div style={{fontSize: '13px'}}>
                Model <strong>{activeModelVersion}</strong> heeft nog geen analyses uitgevoerd.
                Start met het analyseren van foto's om training data te verzamelen.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Dataset Statistics Dashboard */}
      {selectedWorkplace && datasetStats && !loadingStats && (
        <div style={{
          background: '#f8f9fa',
          padding: '20px',
          borderRadius: '12px',
          marginBottom: '30px',
          border: '1px solid #e2e8f0'
        }}>
          <h3 style={{marginTop: 0, marginBottom: '20px'}}>📊 Dataset Overzicht - {selectedWorkplace.name}</h3>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '15px',
            marginBottom: '20px'
          }}>
            <div style={{
              background: 'white',
              padding: '15px',
              borderRadius: '8px',
              textAlign: 'center',
              border: '2px solid #4299e1'
            }}>
              <div style={{fontSize: '32px', fontWeight: 'bold', color: '#2b6cb0'}}>
                {datasetStats.total_images || 0}
              </div>
              <div style={{fontSize: '13px', color: '#2c5282', marginTop: '5px'}}>Totaal Images</div>
            </div>

            <div style={{
              background: 'white',
              padding: '15px',
              borderRadius: '8px',
              textAlign: 'center',
              border: '2px solid #48bb78'
            }}>
              <div style={{fontSize: '32px', fontWeight: 'bold', color: '#2f855a'}}>
                {datasetStats.labeled_count || 0}
              </div>
              <div style={{fontSize: '13px', color: '#276749', marginTop: '5px'}}>Gelabeld</div>
            </div>

            <div style={{
              background: 'white',
              padding: '15px',
              borderRadius: '8px',
              textAlign: 'center',
              border: '2px solid #ed8936'
            }}>
              <div style={{fontSize: '32px', fontWeight: 'bold', color: '#c05621'}}>
                {datasetStats.unlabeled_count || 0}
              </div>
              <div style={{fontSize: '13px', color: '#9c4221', marginTop: '5px'}}>Nog te Labelen</div>
            </div>

            <div style={{
              background: 'white',
              padding: '15px',
              borderRadius: '8px',
              textAlign: 'center',
              border: '2px solid #9f7aea'
            }}>
              <div style={{fontSize: '32px', fontWeight: 'bold', color: '#6b46c1'}}>
                {datasetStats.training_ready || 0}
              </div>
              <div style={{fontSize: '13px', color: '#553c9a', marginTop: '5px'}}>Training Ready</div>
            </div>
          </div>

          {/* Training Set Dashboard - Label Distributie */}
          {datasetStats.label_distribution && Object.keys(datasetStats.label_distribution).length > 0 && (
            <div style={{
              marginTop: '25px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: '12px',
              padding: '20px',
              boxShadow: '0 4px 15px rgba(102, 126, 234, 0.4)'
            }}>
              <h3 style={{
                color: 'white',
                fontSize: '18px',
                fontWeight: 'bold',
                marginBottom: '15px',
                display: 'flex',
                alignItems: 'center',
                gap: '10px'
              }}>
                📊 Training Set Overzicht
                <span style={{
                  background: 'rgba(255,255,255,0.2)',
                  padding: '4px 12px',
                  borderRadius: '20px',
                  fontSize: '14px'
                }}>
                  {datasetStats.labeled_count} gelabelde foto's
                </span>
              </h3>

              {/* Label Distribution Cards */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '15px',
                marginBottom: '20px'
              }}>
                {Object.entries(datasetStats.label_distribution)
                  .sort((a, b) => b[1] - a[1])
                  .map(([label, count]) => {
                    const percentage = datasetStats.labeled_count > 0
                      ? Math.round((count / datasetStats.labeled_count) * 100)
                      : 0;

                    // Color coding based on label
                    let bgColor = '#4299e1';
                    if (label.toLowerCase().includes('ok') && !label.toLowerCase().includes('nok')) {
                      bgColor = '#48bb78';
                    } else if (label.toLowerCase().includes('nok')) {
                      bgColor = '#f56565';
                    } else if (label.toLowerCase().includes('alles')) {
                      bgColor = '#ed8936';
                    }

                    return (
                      <div key={label} style={{
                        background: 'white',
                        borderRadius: '10px',
                        padding: '15px',
                        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                        transition: 'transform 0.2s ease',
                        cursor: 'default'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
                      onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
                      >
                        <div style={{
                          fontSize: '32px',
                          fontWeight: 'bold',
                          color: bgColor,
                          marginBottom: '8px'
                        }}>
                          {count}
                        </div>
                        <div style={{
                          fontSize: '14px',
                          fontWeight: '600',
                          color: '#2d3748',
                          marginBottom: '8px'
                        }}>
                          {label}
                        </div>
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px'
                        }}>
                          <div style={{
                            flex: 1,
                            height: '6px',
                            background: '#e2e8f0',
                            borderRadius: '3px',
                            overflow: 'hidden'
                          }}>
                            <div style={{
                              width: `${percentage}%`,
                              height: '100%',
                              background: bgColor,
                              transition: 'width 0.3s ease'
                            }} />
                          </div>
                          <span style={{
                            fontSize: '13px',
                            fontWeight: 'bold',
                            color: bgColor
                          }}>
                            {percentage}%
                          </span>
                        </div>
                      </div>
                    );
                  })}
              </div>

              {/* Balance Warning */}
              {(() => {
                const labels = Object.entries(datasetStats.label_distribution);
                if (labels.length < 2) return null;

                const sorted = labels.sort((a, b) => b[1] - a[1]);
                const highest = sorted[0][1];
                const lowest = sorted[sorted.length - 1][1];
                const ratio = highest / (lowest || 1);
                const isImbalanced = ratio > 3;

                return isImbalanced && (
                  <div style={{
                    background: 'rgba(237, 137, 54, 0.15)',
                    border: '2px solid rgba(237, 137, 54, 0.5)',
                    borderRadius: '8px',
                    padding: '12px 15px',
                    color: 'white',
                    fontSize: '13px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px'
                  }}>
                    <span style={{fontSize: '20px'}}>⚠️</span>
                    <div>
                      <strong>Dataset Imbalance Gedetecteerd</strong>
                      <div style={{fontSize: '12px', opacity: 0.9, marginTop: '3px'}}>
                        Label "{sorted[0][0]}" heeft {ratio.toFixed(1)}x meer foto's dan "{sorted[sorted.length - 1][0]}".
                        Dit kan de model accuracy beïnvloeden. Probeer een gelijkmatigere verdeling te krijgen.
                      </div>
                    </div>
                  </div>
                );
              })()}
            </div>
          )}

          {/* Detection Errors Dashboard - Per Object (ALLEEN VOOR DETECTION MODELS) */}
          {activeModelType === 'detection' && datasetStats.detection_errors && (
            <>
              {/* Missing Items (False Negatives) */}
              {Object.keys(datasetStats.detection_errors.missing || {}).length > 0 && (
                <div style={{
                  marginTop: '20px',
                  background: 'white',
                  borderRadius: '10px',
                  padding: '20px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                  border: '2px solid #f56565'
                }}>
                  <h4 style={{
                    fontSize: '16px',
                    fontWeight: 'bold',
                    color: '#c53030',
                    marginBottom: '15px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    ❌ Niet Gedetecteerd (False Negatives)
                  </h4>
                  <div style={{display: 'grid', gap: '10px'}}>
                    {Object.entries(datasetStats.detection_errors.missing)
                      .sort((a, b) => b[1] - a[1])
                      .map(([item, count]) => (
                        <div key={item} style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '10px 15px',
                          background: '#fff5f5',
                          borderRadius: '6px',
                          border: '1px solid #feb2b2'
                        }}>
                          <span style={{fontWeight: '600', color: '#2d3748'}}>
                            {item}
                          </span>
                          <span style={{
                            background: '#f56565',
                            color: 'white',
                            padding: '4px 12px',
                            borderRadius: '12px',
                            fontSize: '13px',
                            fontWeight: 'bold'
                          }}>
                            {count}x gemist
                          </span>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {/* False Positives */}
              {Object.keys(datasetStats.detection_errors.false_positive || {}).length > 0 && (
                <div style={{
                  marginTop: '20px',
                  background: 'white',
                  borderRadius: '10px',
                  padding: '20px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                  border: '2px solid #ed8936'
                }}>
                  <h4 style={{
                    fontSize: '16px',
                    fontWeight: 'bold',
                    color: '#c05621',
                    marginBottom: '15px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    ⚠️ Foutief Gedetecteerd (False Positives)
                  </h4>
                  <div style={{display: 'grid', gap: '10px'}}>
                    {Object.entries(datasetStats.detection_errors.false_positive)
                      .sort((a, b) => b[1] - a[1])
                      .map(([item, count]) => (
                        <div key={item} style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '10px 15px',
                          background: '#fffaf0',
                          borderRadius: '6px',
                          border: '1px solid #fbd38d'
                        }}>
                          <span style={{fontWeight: '600', color: '#2d3748'}}>
                            {item}
                          </span>
                          <span style={{
                            background: '#ed8936',
                            color: 'white',
                            padding: '4px 12px',
                            borderRadius: '12px',
                            fontSize: '13px',
                            fontWeight: 'bold'
                          }}>
                            {count}x fout gezien
                          </span>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {/* Count Errors */}
              {Object.keys(datasetStats.detection_errors.count_error || {}).length > 0 && (
                <div style={{
                  marginTop: '20px',
                  background: 'white',
                  borderRadius: '10px',
                  padding: '20px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                  border: '2px solid #4299e1'
                }}>
                  <h4 style={{
                    fontSize: '16px',
                    fontWeight: 'bold',
                    color: '#2c5282',
                    marginBottom: '15px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    🔢 Verkeerd Aantal Gedetecteerd
                  </h4>
                  <div style={{display: 'grid', gap: '10px'}}>
                    {Object.entries(datasetStats.detection_errors.count_error)
                      .sort((a, b) => b[1] - a[1])
                      .map(([itemDesc, count]) => (
                        <div key={itemDesc} style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '10px 15px',
                          background: '#ebf8ff',
                          borderRadius: '6px',
                          border: '1px solid #90cdf4'
                        }}>
                          <span style={{fontWeight: '600', color: '#2d3748'}}>
                            {itemDesc}
                          </span>
                          <span style={{
                            background: '#4299e1',
                            color: 'white',
                            padding: '4px 12px',
                            borderRadius: '12px',
                            fontSize: '13px',
                            fontWeight: 'bold'
                          }}>
                            {count}x verkeerd geteld
                          </span>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Readiness Indicator */}
          <div style={{
            marginTop: '15px',
            padding: '12px',
            background: datasetStats.training_ready >= 100 ? '#f0fff4' : '#fffaf0',
            borderRadius: '6px',
            border: `1px solid ${datasetStats.training_ready >= 100 ? '#48bb78' : '#ed8936'}`
          }}>
            <div style={{fontSize: '13px', fontWeight: 'bold', marginBottom: '5px'}}>
              {datasetStats.training_ready >= 100 ? '✅ Dataset Ready voor Training' : '⚠️ Meer Data Nodig'}
            </div>
            <div style={{fontSize: '12px', color: '#666'}}>
              {datasetStats.training_ready >= 100
                ? 'Je hebt voldoende gelabelde data om een model te trainen!'
                : `Minimaal 100 gelabelde images aanbevolen. Nog ${100 - datasetStats.training_ready} nodig.`
              }
            </div>
          </div>
        </div>
      )}

      {selectedWorkplace && loadingStats && (
        <div style={{textAlign: 'center', padding: '20px'}}>
          <div className="loading">Dashboard laden...</div>
        </div>
      )}

      {selectedWorkplace && (
        <>
          {hasActiveModel ? (
            <ProductionReviewSection workplace={selectedWorkplace} refreshTrigger={refreshTrigger} onDataUpdate={() => loadDatasetStats(selectedWorkplace.id)} />
          ) : (
            <NewWorkplaceTrainingSection workplace={selectedWorkplace} refreshTrigger={refreshTrigger} onDataUpdate={() => loadDatasetStats(selectedWorkplace.id)} />
          )}
        </>
      )}
    </div>
  );
}

// ==========================================
// TAB 2: BEOORDELINGS ANALYSE
// ==========================================
function ReviewAnalysisTab({ workplaces, loading: workplacesLoading, onDataUpdate, selectedWorkplace, onWorkplaceChange, showToast }) {
  // Gebruik de shared selectedWorkplace van parent in plaats van lokale state
  const [analyses, setAnalyses] = useState([]);
  // REMOVED: filter state - no longer using OK/NOK filters in Beoordelings Analyse
  const [loading, setLoading] = useState(true);
  const [correctingId, setCorrectingId] = useState(null);
  const [confidenceThreshold] = useState(70); // Vast op 70%, geen UI control meer
  const [itemsMissing, setItemsMissing] = useState({
    hamer: false,
    schaar: false,
    sleutel: false
  });

  // Nieuwe state voor gedetailleerde item beoordeling (detection modellen)
  const [itemFeedback, setItemFeedback] = useState({
    hamer: 'aanwezig',    // 'aanwezig', 'ontbreekt', 'fout_gedetecteerd', 'te_veel'
    schaar: 'aanwezig',
    sleutel: 'aanwezig'
  });

  // State voor aantal per item
  const [itemCounts, setItemCounts] = useState({
    hamer: 1,
    schaar: 1,
    sleutel: 1
  });

  // State voor actief model tracking
  const [activeModelVersion, setActiveModelVersion] = useState(null);
  const [reviewedCount, setReviewedCount] = useState(0);

  // Auto-select gebeurt nu in parent Admin component

  // Bepaal de juiste categorie op basis van ONTBREKENDE items
  const determineCategory = (missing) => {
    const { hamer, schaar, sleutel } = missing;

    if (!hamer && !schaar && !sleutel) {
      return { class: '0', label: 'OK' };
    }

    if (hamer && schaar && sleutel) {
      return { class: '1', label: 'NOK-alles_weg' };
    }

    if (hamer && !schaar && !sleutel) {
      return { class: '2', label: 'NOK-hamer_weg' };
    }

    if (!hamer && schaar && !sleutel) {
      return { class: '3', label: 'NOK-schaar_weg' };
    }

    if (!hamer && !schaar && sleutel) {
      return { class: '5', label: 'NOK-sleutel_weg' };
    }

    if (!hamer && schaar && sleutel) {
      return { class: '4', label: 'NOK-schaar_sleutel_weg' };
    }

    if (hamer && schaar && !sleutel) {
      return { class: '6', label: 'NOK-alleen_sleutel' };
    }

    if (hamer && !schaar && sleutel) {
      return { class: '4', label: 'NOK-schaar_sleutel_weg' };
    }

    return { class: '0', label: 'OK' };
  };

  const startCorrecting = (analysisId) => {
    const analysis = analyses.find(a => a.id === analysisId);
    setCorrectingId(analysisId);
    setItemsMissing({ hamer: false, schaar: false, sleutel: false });

    // Initialize item feedback based on detections (for detection models)
    if (analysis && analysis.model_type === 'detection') {
      setItemFeedback({
        hamer: 'aanwezig',
        schaar: 'aanwezig',
        sleutel: 'aanwezig'
      });

      // Initialize counts from detection data
      setItemCounts({
        hamer: analysis.detected_hamer || 0,
        schaar: analysis.detected_schaar || 0,
        sleutel: analysis.detected_sleutel || 0
      });
    }
  };

  const toggleMissingItem = (item) => {
    setItemsMissing(prev => ({
      ...prev,
      [item]: !prev[item]
    }));
  };

  const setItemStatus = (item, status) => {
    setItemFeedback(prev => ({
      ...prev,
      [item]: status
    }));
  };

  const submitCorrection = (analysisId) => {
    const category = determineCategory(itemsMissing);
    correctAnalysis(analysisId, category.class, category.label);
  };

  const submitDetailedCorrection = async (analysisId) => {
    try {
      // Bepaal welke items ontbreken, fout gedetecteerd zijn, of te veel zijn
      const missing_items = [];
      const false_positives = [];
      const incorrect_counts = {};

      const analysis = analyses.find(a => a.id === analysisId);

      Object.entries(itemFeedback).forEach(([item, status]) => {
        if (status === 'ontbreekt') {
          missing_items.push(item);
        } else if (status === 'fout_gedetecteerd') {
          false_positives.push(item);
        } else if (status === 'te_veel') {
          const detected = analysis ? (analysis[`detected_${item}`] || 0) : 0;
          const expected = itemCounts[item];
          incorrect_counts[item] = {
            detected: detected,       // Wat het model zag
            expected: expected,       // Wat er echt was
            issue: 'verkeerd_aantal'
          };
        }
      });

      // Bepaal overall status - NOK als er problemen zijn (ontbrekend, false positive, of verkeerd aantal)
      const hasIssues = missing_items.length > 0 || false_positives.length > 0 || Object.keys(incorrect_counts).length > 0;
      const corrected_label = hasIssues ? `NOK-${missing_items.join('_')}_ontbreekt` : 'OK';

      await axios.post(`${API_URL}/api/correct/${analysisId}`, {
        corrected_class: hasIssues ? '1' : '0',
        corrected_label: corrected_label,
        notes: JSON.stringify({
          missing_items,
          false_positives,
          incorrect_counts,
          detailed_feedback: itemFeedback
        }),
        confidence_threshold: confidenceThreshold
      });

      // Bouw feedback message
      let feedbackMsg = '✓ Gedetailleerde feedback opgeslagen!\n';
      feedbackMsg += `Ontbrekend: ${missing_items.join(', ') || 'Geen'}\n`;
      feedbackMsg += `Fout gedetecteerd: ${false_positives.join(', ') || 'Geen'}\n`;
      if (Object.keys(incorrect_counts).length > 0) {
        feedbackMsg += `Verkeerd aantal: ${Object.entries(incorrect_counts).map(([item, data]) =>
          `${item} (${data.detected}x ipv 1x)`).join(', ')}`;
      }

      alert(feedbackMsg);
      setCorrectingId(null);
      loadHistory();

      // Trigger data refresh in Training Data tab
      if (onDataUpdate) {
        onDataUpdate();
      }
    } catch (error) {
      console.error('Error submitting detailed correction:', error);
      alert('Fout bij opslaan feedback: ' + error.message);
    }
  };

  // Load actief model bij werkplek wijziging
  useEffect(() => {
    if (selectedWorkplace) {
      checkActiveModel(selectedWorkplace.id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedWorkplace]);

  // Laad analyses zodra actief model bekend is
  useEffect(() => {
    if (selectedWorkplace && activeModelVersion !== null) {
      loadHistory();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedWorkplace, activeModelVersion]);

  const checkActiveModel = async (workplaceId) => {
    try {
      const response = await axios.get(`${API_URL}/api/workplaces/${workplaceId}/models`);
      if (response.data.success) {
        const activeModel = response.data.models.find(m => m.status === 'active');
        if (activeModel && activeModel.version) {
          setActiveModelVersion(activeModel.version);
        } else {
          setActiveModelVersion(null);
        }
      }
    } catch (error) {
      console.error('Error checking model:', error);
      setActiveModelVersion(null);
    }
  };

  const loadHistory = async () => {
    if (!selectedWorkplace) return;

    setLoading(true);
    try {
      // Filter op workplace EN actief model
      const params = new URLSearchParams({
        workplace_id: selectedWorkplace.id,
        limit: 1000 // Verhoog limit om alle analyses op te halen
      });

      // Voeg model_version filter toe als er een actief model is
      if (activeModelVersion) {
        params.append('model_version', activeModelVersion);
      }

      const response = await axios.get(`${API_URL}/api/history?${params.toString()}`);

      if (response.data.analyses) {
        const allAnalyses = response.data.analyses;

        // Splits op beoordeeld vs onbeoordeeld
        const unreviewedAnalyses = allAnalyses.filter(a => !a.corrected_label);
        const reviewed = allAnalyses.filter(a => a.corrected_label);

        setAnalyses(unreviewedAnalyses);
        setReviewedCount(reviewed.length);
      }
    } catch (error) {
      console.error('Error loading history:', error);
      alert('Fout bij laden geschiedenis: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const addToTrainingData = async (analysis) => {
    try {
      // Verplaats de foto naar training data
      const formData = new FormData();
      formData.append('analysis_id', analysis.id);
      // Als niet gelabeld, gebruik "Onbekend" als label
      formData.append('label', analysis.corrected_label || 'Onbekend');

      await axios.post(
        `${API_URL}/api/workplaces/${selectedWorkplace.id}/training-images/from-analysis`,
        formData
      );

      showToast('Foto verplaatst naar trainingsdata!', 'success');

      // Refresh analyses list (foto is nu weg)
      loadHistory();

      // Trigger data refresh in Training Data tab
      if (onDataUpdate) {
        onDataUpdate();
      }
    } catch (error) {
      console.error('Error adding to training data:', error);
      showToast('Fout bij toevoegen aan trainingsdata: ' + (error.response?.data?.detail || error.message), 'error');
    }
  };

  const correctAnalysis = async (analysisId, correctedClass, correctedLabel) => {
    try {
      await axios.post(`${API_URL}/api/correct/${analysisId}`, {
        corrected_class: correctedClass,
        corrected_label: correctedLabel,
        notes: "",
        confidence_threshold: confidenceThreshold
      });

      showToast(`Analyse gecorrigeerd naar: ${correctedLabel}`, 'success');
      setCorrectingId(null);
      loadHistory();

      // Trigger data refresh in Training Data tab
      if (onDataUpdate) {
        onDataUpdate();
      }
    } catch (error) {
      console.error('Error correcting analysis:', error);
      showToast('Fout bij opslaan correctie: ' + error.message, 'error');
    }
  };


  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('nl-NL', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (workplacesLoading) {
    return <div className="loading">Laden...</div>;
  }

  if (workplaces.length === 0) {
    return (
      <div className="empty-state">
        <p>Geen werkplekken gevonden</p>
        <p className="empty-hint">Maak eerst een werkplek aan in Werkplekken Beheer</p>
      </div>
    );
  }

  // Bereken statistieken voor deze specifieke werkplek (van actief model)
  const unreviewedCount = analyses.length; // analyses bevat alleen onbeoordeelde
  // reviewedCount komt uit state (geladen via loadHistory)
  const totalCount = unreviewedCount + reviewedCount;

  return (
    <div className="review-analysis-tab">
      <h2>✏️ Beoordelings Analyse</h2>
      <p>Review en corrigeer AI voorspellingen voor model verbetering</p>

      {/* Werkplek Selectie */}
      <div className="workplace-selector" style={{ marginBottom: '20px', padding: '15px', background: '#f7fafc', borderRadius: '8px' }}>
        <label style={{ fontWeight: 'bold', marginRight: '10px' }}>Selecteer Werkplek:</label>
        <select
          value={selectedWorkplace?.id || ''}
          onChange={(e) => {
            const wp = workplaces.find(w => w.id === parseInt(e.target.value));
            onWorkplaceChange(wp);
          }}
          style={{ padding: '8px 12px', borderRadius: '4px', border: '1px solid #cbd5e0', minWidth: '250px' }}
        >
          {workplaces.map(wp => (
            <option key={wp.id} value={wp.id}>
              {wp.name}
            </option>
          ))}
        </select>
        <small style={{ marginLeft: '10px', color: '#718096' }}>
          Beoordeelde analyses worden gebruikt voor training van deze werkplek
        </small>
      </div>

      {!selectedWorkplace ? (
        <div className="empty-state">
          <p>Selecteer een werkplek om analyses te beoordelen</p>
        </div>
      ) : loading ? (
        <div className="loading">Laden...</div>
      ) : null}

      {/* Statistics Dashboard */}
      {selectedWorkplace && !loading && (
        <div className="stats-dashboard">
          <div className="stat-card">
            <div className="stat-icon">⏳</div>
            <div className="stat-content">
              <div className="stat-label">Nog te beoordelen</div>
              <div className="stat-value">{unreviewedCount}</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">✅</div>
            <div className="stat-content">
              <div className="stat-label">Beoordeeld</div>
              <div className="stat-value">{reviewedCount}</div>
              <small>Naar opslag/training</small>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">📊</div>
            <div className="stat-content">
              <div className="stat-label">Totaal Analyses</div>
              <div className="stat-value">{totalCount}</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">🎯</div>
            <div className="stat-content">
              <div className="stat-label">Voortgang</div>
              <div className="stat-value">
                {totalCount > 0
                  ? Math.round((reviewedCount / totalCount) * 100)
                  : 0}%
              </div>
            </div>
          </div>
        </div>
      )}

      {/* REMOVED: Confidence Threshold Control - niet nodig in Beoordelings Analyse */}

      {/* Analyses Grid */}
      {selectedWorkplace && !loading && (
        <div className="analyses-grid">
        {analyses.length === 0 ? (
          <div className="empty-state">
            <p>Geen analyses gevonden</p>
            <p className="empty-hint">Start met foto's analyseren om hier resultaten te zien</p>
          </div>
        ) : (
          analyses
            .filter(analysis => !analysis.corrected_label)
            .map((analysis) => (
            <div key={analysis.id} className={`analysis-card ${analysis.status.toLowerCase()}`}>
              {/* Image */}
              <div className="analysis-image">
                <img
                  src={`${API_URL}/${analysis.image_path}`}
                  alt={`Analyse ${analysis.id}`}
                  onError={(e) => {
                    e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg"/>';
                  }}
                />
                <div className={`status-badge ${analysis.status.toLowerCase()}`}>
                  {analysis.status}
                </div>
              </div>

              {/* Content */}
              <div className="analysis-content">
                <div className="analysis-header">
                  <h3>{analysis.predicted_label}</h3>
                  <span className="confidence">
                    {(analysis.confidence * 100).toFixed(1)}%
                  </span>
                </div>

                <div className="analysis-meta">
                  <div className="meta-item">
                    <span className="meta-label">Datum:</span>
                    <span className="meta-value">{formatDate(analysis.created_at)}</span>
                  </div>

                  <div className="meta-item">
                    <span className="meta-label">📱 Device:</span>
                    <span className="meta-value">{analysis.device_id || 'onbekend'}</span>
                  </div>

                  {analysis.missing_items && analysis.missing_items.length > 0 && (
                    <div className="meta-item">
                      <span className="meta-label">Ontbrekend:</span>
                      <span className="meta-value">
                        {analysis.missing_items.join(', ')}
                      </span>
                    </div>
                  )}

                  {analysis.face_count > 0 && (
                    <div className="meta-item privacy">
                      <span className="meta-label">🔒 Gezichten:</span>
                      <span className="meta-value">{analysis.face_count} geblurd</span>
                    </div>
                  )}

                  {analysis.model_type === 'detection' && analysis.total_detections !== undefined && (
                    <div className="meta-item detection-counts">
                      <span className="meta-label">🔍 Detecties:</span>
                      <span className="meta-value">
                        🔨:{analysis.detected_hamer || 0}
                        ✂️:{analysis.detected_schaar || 0}
                        🔑:{analysis.detected_sleutel || 0}
                        {analysis.total_detections > 3 && <strong style={{color: 'orange', marginLeft: '8px'}}>⚠️ Dubbel!</strong>}
                      </span>
                    </div>
                  )}
                </div>

                {analysis.corrected_label && (
                  <div className="correction-badge">
                    ✏️ Gecorrigeerd naar: {analysis.corrected_label}
                  </div>
                )}

                {/* Correction UI */}
                {correctingId === analysis.id ? (
                  <div className="correction-panel">
                    {/* Detection model: detailed per-item feedback */}
                    {analysis.model_type === 'detection' ? (
                      <div>
                        <p style={{fontWeight: 'bold', marginBottom: '12px', fontSize: '14px'}}>
                          🔍 Geef feedback per item (voor training):
                        </p>
                        <div style={{
                          background: '#f7fafc',
                          padding: '12px',
                          borderRadius: '6px',
                          marginBottom: '12px'
                        }}>
                          {['hamer', 'schaar', 'sleutel'].map(item => {
                            const icons = { hamer: '🔨', schaar: '✂️', sleutel: '🔑' };
                            const detected = analysis[`detected_${item}`] || 0;

                            return (
                              <div key={item} style={{
                                marginBottom: '10px',
                                padding: '10px',
                                background: 'white',
                                borderRadius: '4px',
                                border: '1px solid #e2e8f0'
                              }}>
                                <div style={{
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  alignItems: 'center',
                                  marginBottom: '8px'
                                }}>
                                  <span style={{fontWeight: 'bold', fontSize: '13px'}}>
                                    {icons[item]} {item.charAt(0).toUpperCase() + item.slice(1)}
                                  </span>
                                  <span style={{fontSize: '12px', color: '#666'}}>
                                    Model detecteerde: {detected}x
                                  </span>
                                </div>
                                <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px'}}>
                                  <button
                                    onClick={() => setItemStatus(item, 'aanwezig')}
                                    style={{
                                      padding: '6px',
                                      borderRadius: '4px',
                                      border: itemFeedback[item] === 'aanwezig' ? '2px solid #48bb78' : '1px solid #cbd5e0',
                                      background: itemFeedback[item] === 'aanwezig' ? '#f0fff4' : 'white',
                                      color: itemFeedback[item] === 'aanwezig' ? '#22543d' : '#4a5568',
                                      fontWeight: itemFeedback[item] === 'aanwezig' ? 'bold' : 'normal',
                                      cursor: 'pointer',
                                      fontSize: '11px'
                                    }}
                                  >
                                    ✅ Correct
                                  </button>
                                  <button
                                    onClick={() => setItemStatus(item, 'ontbreekt')}
                                    style={{
                                      padding: '6px',
                                      borderRadius: '4px',
                                      border: itemFeedback[item] === 'ontbreekt' ? '2px solid #ed8936' : '1px solid #cbd5e0',
                                      background: itemFeedback[item] === 'ontbreekt' ? '#fffaf0' : 'white',
                                      color: itemFeedback[item] === 'ontbreekt' ? '#7c2d12' : '#4a5568',
                                      fontWeight: itemFeedback[item] === 'ontbreekt' ? 'bold' : 'normal',
                                      cursor: 'pointer',
                                      fontSize: '11px'
                                    }}
                                  >
                                    ❌ Ontbreekt
                                  </button>
                                  <button
                                    onClick={() => setItemStatus(item, 'fout_gedetecteerd')}
                                    style={{
                                      padding: '6px',
                                      borderRadius: '4px',
                                      border: itemFeedback[item] === 'fout_gedetecteerd' ? '2px solid #e53e3e' : '1px solid #cbd5e0',
                                      background: itemFeedback[item] === 'fout_gedetecteerd' ? '#fff5f5' : 'white',
                                      color: itemFeedback[item] === 'fout_gedetecteerd' ? '#742a2a' : '#4a5568',
                                      fontWeight: itemFeedback[item] === 'fout_gedetecteerd' ? 'bold' : 'normal',
                                      cursor: 'pointer',
                                      fontSize: '11px'
                                    }}
                                  >
                                    ⚠️ Niet aanwezig
                                  </button>
                                  <button
                                    onClick={() => setItemStatus(item, 'te_veel')}
                                    style={{
                                      padding: '6px',
                                      borderRadius: '4px',
                                      border: itemFeedback[item] === 'te_veel' ? '2px solid #9f7aea' : '1px solid #cbd5e0',
                                      background: itemFeedback[item] === 'te_veel' ? '#faf5ff' : 'white',
                                      color: itemFeedback[item] === 'te_veel' ? '#553c9a' : '#4a5568',
                                      fontWeight: itemFeedback[item] === 'te_veel' ? 'bold' : 'normal',
                                      cursor: 'pointer',
                                      fontSize: '11px'
                                    }}
                                  >
                                    🔢 Te veel
                                  </button>
                                </div>

                                {/* Toon aantal input als "te_veel" geselecteerd is */}
                                {itemFeedback[item] === 'te_veel' && (
                                  <div style={{marginTop: '8px', padding: '8px', background: '#faf5ff', borderRadius: '4px'}}>
                                    <label style={{fontSize: '11px', color: '#553c9a', fontWeight: 'bold', display: 'block', marginBottom: '4px'}}>
                                      Hoeveel {item} zijn er ECHT aanwezig?
                                    </label>
                                    <input
                                      type="number"
                                      min="0"
                                      max="10"
                                      value={itemCounts[item]}
                                      onChange={(e) => setItemCounts({...itemCounts, [item]: parseInt(e.target.value) || 0})}
                                      style={{
                                        width: '60px',
                                        padding: '4px',
                                        border: '1px solid #9f7aea',
                                        borderRadius: '4px',
                                        fontSize: '12px'
                                      }}
                                    />
                                    <span style={{marginLeft: '8px', fontSize: '11px', color: '#666'}}>
                                      (Model detecteerde: {detected}x)
                                    </span>
                                  </div>
                                )}

                                <div style={{marginTop: '6px', fontSize: '10px', color: '#718096', fontStyle: 'italic'}}>
                                  {itemFeedback[item] === 'aanwezig' && '✓ Model heeft dit correct gezien'}
                                  {itemFeedback[item] === 'ontbreekt' && '⚠️ Model miste dit item (False Negative)'}
                                  {itemFeedback[item] === 'fout_gedetecteerd' && '⚠️ Model zag dit terwijl het er niet was (False Positive)'}
                                  {itemFeedback[item] === 'te_veel' && '⚠️ Model detecteerde verkeerd aantal (Count Error)'}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                        <div className="correction-actions">
                          <button onClick={() => submitDetailedCorrection(analysis.id)} className="submit-btn" style={{background: '#48bb78'}}>
                            ✓ Opslaan met Details
                          </button>
                          <button onClick={() => correctAnalysis(analysis.id, 'N/A', 'Mens in beeld - geen beoordeling')} className="correct-btn privacy">
                            🚫 Mens in beeld
                          </button>
                          <button onClick={() => setCorrectingId(null)} className="correct-btn cancel">
                            ✖ Annuleer
                          </button>
                        </div>
                      </div>
                    ) : (
                      /* Classification model: simple checkbox interface */
                      <div>
                        <p><strong>Welke items ontbreken?</strong></p>
                        <div className="checkbox-items">
                          <label className="checkbox-item">
                            <input
                              type="checkbox"
                              checked={itemsMissing.hamer}
                              onChange={() => toggleMissingItem('hamer')}
                            />
                            <span>🔨 Hamer ontbreekt</span>
                          </label>
                          <label className="checkbox-item">
                            <input
                              type="checkbox"
                              checked={itemsMissing.schaar}
                              onChange={() => toggleMissingItem('schaar')}
                            />
                            <span>✂️ Schaar ontbreekt</span>
                          </label>
                          <label className="checkbox-item">
                            <input
                              type="checkbox"
                              checked={itemsMissing.sleutel}
                              onChange={() => toggleMissingItem('sleutel')}
                            />
                            <span>🔑 Sleutel ontbreekt</span>
                          </label>
                        </div>
                        <div className="correction-actions">
                          <button onClick={() => submitCorrection(analysis.id)} className="submit-btn">
                            ✓ Opslaan
                          </button>
                          <button onClick={() => correctAnalysis(analysis.id, 'N/A', 'Mens in beeld - geen beoordeling')} className="correct-btn privacy">
                            🚫 Mens in beeld
                          </button>
                          <button onClick={() => setCorrectingId(null)} className="correct-btn cancel">
                            ✖ Annuleer
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="action-buttons">
                    <button
                      onClick={() => correctAnalysis(analysis.id, analysis.predicted_class, analysis.predicted_label)}
                      className="quick-approve-btn"
                      title="AI voorspelling is correct"
                    >
                      ✓ AI heeft gelijk
                    </button>
                    <button onClick={() => startCorrecting(analysis.id)} className="edit-btn">
                      ✏️ Corrigeer
                    </button>
                    <button
                      onClick={() => addToTrainingData(analysis)}
                      className="add-to-training-btn"
                      title="Voeg toe aan trainingsdata"
                    >
                      📚 Training
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        </div>
      )}
    </div>
  );
}

// ==========================================
// PRODUCTION REVIEW (voor bestaande modellen)
// ==========================================
function ProductionReviewSection({ workplace, refreshTrigger }) {
  const [loading, setLoading] = useState(false);
  const [trainingCandidates, setTrainingCandidates] = useState([]);
  const [selectedCandidates, setSelectedCandidates] = useState([]);
  const [confidenceThreshold, setConfidenceThreshold] = useState(70);

  useEffect(() => {
    loadTrainingCandidates();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workplace, confidenceThreshold]);

  // Reload when refreshTrigger changes (from ReviewAnalysisTab)
  useEffect(() => {
    if (workplace && refreshTrigger) {
      console.log('🔄 Refreshing training candidates list...');
      loadTrainingCandidates();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshTrigger]);

  const loadTrainingCandidates = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/api/training/candidates`, {
        params: { confidence_threshold: confidenceThreshold }
      });

      // Filter candidates by workplace
      const allCandidates = response.data.candidates;
      const workplaceCandidates = allCandidates.filter(c =>
        c.workplace_id === workplace.id
      );

      setTrainingCandidates(workplaceCandidates);
    } catch (error) {
      console.error('Error loading training candidates:', error);
    } finally {
      setLoading(false);
    }
  };

  const exportTrainingData = async () => {
    if (selectedCandidates.length === 0) {
      alert('Selecteer minimaal 1 analyse voor export');
      return;
    }

    try {
      const response = await axios.post(`${API_URL}/api/training/export`, {
        analysis_ids: selectedCandidates,
        export_name: `training_v${new Date().getTime()}`
      });

      alert(`✓ ${response.data.export.total_exported} analyses geëxporteerd!\n\nPad: ${response.data.export.export_path}\n\nKlasse verdeling:\n${JSON.stringify(response.data.export.class_distribution, null, 2)}`);

      setSelectedCandidates([]);
      loadTrainingCandidates();
    } catch (error) {
      console.error('Error exporting training data:', error);
      alert('Fout bij exporteren: ' + error.message);
    }
  };

  const toggleCandidateSelection = (analysisId) => {
    setSelectedCandidates(prev => {
      if (prev.includes(analysisId)) {
        return prev.filter(id => id !== analysisId);
      } else {
        return [...prev, analysisId];
      }
    });
  };

  const selectAllCandidates = () => {
    if (selectedCandidates.length === trainingCandidates.length) {
      setSelectedCandidates([]);
    } else {
      setSelectedCandidates(trainingCandidates.map(c => c.id));
    }
  };

  const deleteCandidate = async (analysisId) => {
    if (!window.confirm('Weet je zeker dat je deze analyse wilt verwijderen?')) {
      return;
    }

    try {
      await axios.delete(`${API_URL}/api/analysis/${analysisId}`);
      alert('✓ Analyse verwijderd');
      loadTrainingCandidates();
      setSelectedCandidates(prev => prev.filter(id => id !== analysisId));
    } catch (error) {
      console.error('Error deleting analysis:', error);
      alert('Fout bij verwijderen: ' + error.message);
    }
  };

  const deleteSelectedCandidates = async () => {
    if (selectedCandidates.length === 0) {
      alert('Selecteer minimaal 1 analyse om te verwijderen');
      return;
    }

    if (!window.confirm(`Weet je zeker dat je ${selectedCandidates.length} analyses wilt verwijderen?`)) {
      return;
    }

    try {
      await Promise.all(
        selectedCandidates.map(id => axios.delete(`${API_URL}/api/analysis/${id}`))
      );

      alert(`✓ ${selectedCandidates.length} analyses verwijderd`);
      setSelectedCandidates([]);
      loadTrainingCandidates();
    } catch (error) {
      console.error('Error deleting analyses:', error);
      alert('Fout bij verwijderen: ' + error.message);
    }
  };

  if (loading) {
    return <div className="loading">Laden...</div>;
  }

  return (
    <div className="production-review-section">
      {/* Training Selector */}
      <div className="training-selector-section" style={{marginTop: '40px'}}>
        <div className="section-header">
          <h3>🎓 Training Selector</h3>
          <p className="section-description">
            Selecteer beoordeelde analyses voor model retraining. Analyses met lage zekerheid (&lt;{confidenceThreshold}%) of foute voorspellingen worden automatisch gedetecteerd als trainings-kandidaten.
          </p>

          {/* Confidence Threshold Control */}
          <div className="confidence-threshold-control" style={{marginTop: '15px', marginBottom: '15px'}}>
            <label htmlFor="confidence-slider">
              🎯 Training Drempel: <strong>{confidenceThreshold}%</strong>
            </label>
            <input
              id="confidence-slider"
              type="range"
              min="50"
              max="95"
              step="5"
              value={confidenceThreshold}
              onChange={(e) => setConfidenceThreshold(Number(e.target.value))}
              className="confidence-slider"
            />
            <small>Analyses onder {confidenceThreshold}% worden automatisch geselecteerd voor retraining</small>
          </div>

          <div className="selector-actions">
            <button onClick={selectAllCandidates} className="select-all-btn">
              {selectedCandidates.length === trainingCandidates.length && trainingCandidates.length > 0 ? '⬜ Deselecteer alles' : '☑️ Selecteer alles'}
            </button>
            <button
              onClick={deleteSelectedCandidates}
              className="delete-btn"
              disabled={selectedCandidates.length === 0}
            >
              🗑️ Verwijder {selectedCandidates.length > 0 ? `(${selectedCandidates.length})` : ''}
            </button>
            <button
              onClick={exportTrainingData}
              className="export-btn"
              disabled={selectedCandidates.length === 0}
            >
              📤 Exporteer {selectedCandidates.length > 0 ? `(${selectedCandidates.length})` : ''}
            </button>
          </div>
        </div>

        {trainingCandidates.length === 0 ? (
          <div className="empty-state">
            <p>✅ Geen training candidates</p>
            <p className="empty-hint">
              Training candidates worden automatisch gedetecteerd wanneer beoordeelde analyses fout voorspeld zijn of lage zekerheid hebben
            </p>
          </div>
        ) : (
          <div className="candidates-grid">
            {trainingCandidates.map((candidate) => (
              <div
                key={candidate.id}
                className={`candidate-card ${selectedCandidates.includes(candidate.id) ? 'selected' : ''}`}
              >
                <div className="candidate-checkbox" onClick={() => toggleCandidateSelection(candidate.id)}>
                  <input
                    type="checkbox"
                    checked={selectedCandidates.includes(candidate.id)}
                    readOnly
                  />
                </div>
                <button
                  className="candidate-delete-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteCandidate(candidate.id);
                  }}
                  title="Verwijder deze analyse"
                >
                  🗑️
                </button>
                <div className="candidate-image" onClick={() => toggleCandidateSelection(candidate.id)}>
                  <img
                    src={`${API_URL}/${candidate.image_path}`}
                    alt={`Candidate ${candidate.id}`}
                  />
                </div>
                <div className="candidate-info" onClick={() => toggleCandidateSelection(candidate.id)}>
                  <div className="candidate-labels">
                    <div className="label-item">
                      <span className="label-title">AI:</span>
                      <span className="label-value predicted">{candidate.predicted_label}</span>
                    </div>
                    <div className="label-item">
                      <span className="label-title">Correct:</span>
                      <span className="label-value corrected">{candidate.corrected_label}</span>
                    </div>
                  </div>
                  <div className="candidate-meta">
                    <span className="confidence-badge" style={{
                      backgroundColor: candidate.confidence < 0.7 ? '#f56565' : '#48bb78'
                    }}>
                      {(candidate.confidence * 100).toFixed(1)}% zekerheid
                    </span>
                    {candidate.predicted_label !== candidate.corrected_label && (
                      <span className="error-badge">❌ Fout voorspeld</span>
                    )}
                    <span className="device-badge">
                      📱 {candidate.device_id || 'onbekend'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ==========================================
// NEW WORKPLACE TRAINING (voor nieuwe werkplekken)
// ==========================================
function NewWorkplaceTrainingSection({ workplace, refreshTrigger }) {
  const [trainingImages, setTrainingImages] = useState([]);
  const [filteredImages, setFilteredImages] = useState([]);
  const [datasetStats, setDatasetStats] = useState(null);
  const [uploadingFiles, setUploadingFiles] = useState(false);
  const [showBatchLabelModal, setShowBatchLabelModal] = useState(false);
  const [pendingPhotos, setPendingPhotos] = useState([]);
  const [missingItems, setMissingItems] = useState([]);
  const [readyForTraining, setReadyForTraining] = useState(false);
  const [labelFilter, setLabelFilter] = useState('all');
  const [editingImage, setEditingImage] = useState(null);
  const [newLabel, setNewLabel] = useState('');
  const [uploadProgress, setUploadProgress] = useState({ current: 0, total: 0 });

  // Load training data
  useEffect(() => {
    if (workplace) {
      loadTrainingData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workplace]);

  // Reload when refreshTrigger changes (from ReviewAnalysisTab)
  useEffect(() => {
    if (workplace && refreshTrigger) {
      console.log('🔄 Refreshing training images list...');
      loadTrainingData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshTrigger]);

  // Filter training images based on label filter
  useEffect(() => {
    if (labelFilter === 'all') {
      setFilteredImages(trainingImages);
    } else if (labelFilter === 'unlabeled') {
      setFilteredImages(trainingImages.filter(img => !img.label || img.label === 'unlabeled'));
    } else {
      setFilteredImages(trainingImages.filter(img => img.label === labelFilter));
    }
  }, [trainingImages, labelFilter]);

  const loadTrainingData = async () => {
    try {
      console.log('Loading training data for workplace:', workplace.id);
      const response = await axios.get(`${API_URL}/api/workplaces/${workplace.id}/training-images`);
      console.log('Training images response:', response.data);
      if (response.data.success) {
        console.log('Setting training images:', response.data.images);
        setTrainingImages(response.data.images);
        calculateDatasetStats(response.data.images);
      }
    } catch (error) {
      console.error('Error loading training data:', error);
    }
  };

  const calculateDatasetStats = (images) => {
    const labelCounts = {};
    images.forEach(img => {
      if (img.label && img.label !== 'unlabeled') {
        labelCounts[img.label] = (labelCounts[img.label] || 0) + 1;
      }
    });

    // Define required scenarios for optimal YOLO training
    const scenarios = [
      { label: 'OK', description: 'Alle items aanwezig', target: 100, isComplete: false },
      ...workplace.items.map(item => ({
        label: `NOK-${item}`,
        description: `Alleen ${item} ontbreekt`,
        target: 50,
        isComplete: false
      })),
      { label: 'Leeg', description: 'Alle items ontbreken', target: 30, isComplete: false }
    ];

    // Calculate completion for each scenario
    scenarios.forEach(scenario => {
      const count = labelCounts[scenario.label] || 0;
      scenario.count = count;
      scenario.isComplete = count >= scenario.target;
      scenario.progress = Math.min((count / scenario.target) * 100, 100);
    });

    // Check if all scenarios are complete
    const allReady = scenarios.every(s => s.isComplete);
    setReadyForTraining(allReady);

    // Find next recommended scenario to photograph
    const incomplete = scenarios.filter(s => !s.isComplete);
    const nextScenario = incomplete.length > 0
      ? incomplete.sort((a, b) => a.count - b.count)[0]
      : null;

    setDatasetStats({
      total: images.length,
      labeled: images.filter(img => img.label && img.label !== 'unlabeled').length,
      unlabeled: images.filter(img => !img.label || img.label === 'unlabeled').length,
      labelCounts: labelCounts,
      scenarios: scenarios,
      nextScenario: nextScenario,
      completionPercentage: Math.round((scenarios.filter(s => s.isComplete).length / scenarios.length) * 100)
    });
  };

  // Handle batch upload
  const handleBatchUpload = async (files) => {
    const photosArray = [];

    for (const file of files) {
      const reader = new FileReader();
      const photoData = await new Promise((resolve) => {
        reader.onloadend = () => resolve({ data: reader.result, name: file.name });
        reader.readAsDataURL(file);
      });
      photosArray.push(photoData);
    }

    setPendingPhotos(photosArray);
    setShowBatchLabelModal(true);
  };

  // Save batch with label
  const saveBatchWithLabel = async () => {
    // Generate label from missing items
    let label;
    if (missingItems.length === 0) {
      label = 'OK';
    } else if (missingItems.length === workplace.items.length) {
      label = 'Leeg';
    } else {
      label = `NOK-${missingItems.join('-')}`;
    }

    setUploadingFiles(true);
    setUploadProgress({ current: 0, total: pendingPhotos.length });

    try {
      console.log(`Starting upload of ${pendingPhotos.length} photos with label: ${label}`);
      console.log(`Missing items: ${missingItems.join(', ') || 'none'}`);
      let successCount = 0;
      let errorCount = 0;

      for (let i = 0; i < pendingPhotos.length; i++) {
        const photo = pendingPhotos[i];
        try {
          console.log(`Uploading photo ${i + 1}/${pendingPhotos.length}: ${photo.name}`);
          setUploadProgress({ current: i + 1, total: pendingPhotos.length });

          const blob = await (await fetch(photo.data)).blob();
          const formData = new FormData();
          formData.append('file', blob, photo.name);
          formData.append('label', label);

          const response = await axios.post(
            `${API_URL}/api/workplaces/${workplace.id}/training-images`,
            formData,
            {
              headers: { 'Content-Type': 'multipart/form-data' }
            }
          );

          console.log(`Photo ${i + 1} uploaded successfully:`, response.data);
          successCount++;
        } catch (photoError) {
          console.error(`Error uploading photo ${i + 1}:`, photoError);
          console.error('Error details:', photoError.response?.data || photoError.message);
          errorCount++;
        }
      }

      if (errorCount > 0) {
        alert(`${successCount} foto's opgeslagen, ${errorCount} mislukt. Check console voor details.`);
      } else {
        alert(`${successCount} foto's succesvol opgeslagen met label: ${label}`);
      }

      setShowBatchLabelModal(false);
      setPendingPhotos([]);
      setMissingItems([]);
      loadTrainingData();
    } catch (error) {
      console.error('Error saving batch:', error);
      alert('Fout bij opslaan foto\'s. Check console voor details.');
    }

    setUploadingFiles(false);
  };

  // Handle edit label
  const handleEditLabel = (image) => {
    setEditingImage(image);
    setNewLabel(image.label || '');
  };

  const saveEditedLabel = async () => {
    if (!newLabel.trim()) {
      alert('Vul een label in');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('label', newLabel);

      await axios.put(`${API_URL}/api/workplaces/${workplace.id}/training-images/${editingImage.id}`, formData);

      alert('Label succesvol bijgewerkt!');
      setEditingImage(null);
      setNewLabel('');
      loadTrainingData();
    } catch (error) {
      console.error('Error updating label:', error);
      alert('Fout bij bijwerken label');
    }
  };

  // Handle delete image
  const handleDeleteImage = async (imageId) => {
    if (!window.confirm('Weet je zeker dat je deze foto wilt verwijderen?')) {
      return;
    }

    try {
      await axios.delete(`${API_URL}/api/workplaces/${workplace.id}/training-images/${imageId}`);
      alert('Foto succesvol verwijderd!');
      loadTrainingData();
    } catch (error) {
      console.error('Error deleting image:', error);
      alert('Fout bij verwijderen foto');
    }
  };

  // Export dataset
  const handleExportDataset = async () => {
    if (!window.confirm('Dataset exporteren voor training?')) {
      return;
    }

    try {
      const response = await axios.post(`${API_URL}/api/workplaces/${workplace.id}/export-dataset`, {}, {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `dataset_${workplace.name}_${Date.now()}.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      alert('Dataset geëxporteerd! Upload naar Google Colab voor training.');
    } catch (error) {
      console.error('Error exporting dataset:', error);
      alert('Fout bij exporteren dataset');
    }
  };

  return (
    <div className="new-workplace-training-section">
      <div className="section-banner warning">
        <h3>📸 Training Data Verzamelen</h3>
        <p>Deze werkplek heeft nog geen model. Verzamel minimaal 30 foto's per object/scenario.</p>
      </div>

      {/* Dataset Stats */}
      {datasetStats && (
        <div className="dataset-stats">
          <h4>Dataset Overzicht</h4>
          <div className="stats-row">
            <div className="stat-box">
              <span className="stat-value">{datasetStats.total}</span>
              <span className="stat-label">Totaal Foto's</span>
            </div>
            <div className="stat-box">
              <span className="stat-value">{datasetStats.labeled}</span>
              <span className="stat-label">Gelabeld</span>
            </div>
            <div className="stat-box">
              <span className="stat-value">{datasetStats.unlabeled}</span>
              <span className="stat-label">Niet Gelabeld</span>
            </div>
          </div>

          {/* Guided Collection Dashboard */}
          <div className="guided-collection">
            <div className="collection-header">
              <h5>📋 Dataset Verzamelplan</h5>
              <div className="overall-progress">
                <span className="progress-label">{datasetStats.completionPercentage}% Compleet</span>
                <div className="mini-progress-bar">
                  <div
                    className="mini-progress-fill"
                    style={{ width: `${datasetStats.completionPercentage}%` }}
                  />
                </div>
              </div>
            </div>

            {datasetStats.nextScenario && (
              <div className="next-scenario-banner">
                <span className="next-icon">📸</span>
                <div className="next-info">
                  <strong>Volgende aanbeveling:</strong>
                  <p>Fotografeer werkplek: {datasetStats.nextScenario.description}</p>
                  <small>Nog {datasetStats.nextScenario.target - datasetStats.nextScenario.count} foto's nodig</small>
                </div>
              </div>
            )}

            <div className="scenarios-list">
              {datasetStats.scenarios.map(scenario => (
                <div key={scenario.label} className={`scenario-item ${scenario.isComplete ? 'complete' : 'incomplete'}`}>
                  <div className="scenario-header">
                    <span className="scenario-icon">{scenario.isComplete ? '✓' : '○'}</span>
                    <div className="scenario-info">
                      <strong>{scenario.label}</strong>
                      <small>{scenario.description}</small>
                    </div>
                    <span className="scenario-count">
                      {scenario.count} / {scenario.target}
                    </span>
                  </div>
                  <div className="scenario-progress-bar">
                    <div
                      className="scenario-progress-fill"
                      style={{
                        width: `${scenario.progress}%`,
                        backgroundColor: scenario.isComplete ? '#28a745' : '#667eea'
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>

            {readyForTraining && (
              <div className="ready-banner">
                <p>✅ Dataset is compleet en klaar voor training!</p>
                <button onClick={handleExportDataset} className="btn-success">
                  📦 Export Dataset voor Training
                </button>
              </div>
            )}

            {/* Export button altijd beschikbaar */}
            {!readyForTraining && datasetStats.labeled > 0 && (
              <div className="export-section">
                <p className="export-info">
                  💡 Je kunt ook exporteren met minder dan 30 foto's per label voor testdoeleinden.
                </p>
                <button onClick={handleExportDataset} className="btn-secondary">
                  📦 Export Huidige Dataset ({datasetStats.labeled} foto's)
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Upload Actions */}
      <div className="upload-actions">
        <h4>Foto's Toevoegen</h4>
        <div className="action-buttons">
          <input
            type="file"
            multiple
            accept="image/*"
            onChange={(e) => handleBatchUpload(Array.from(e.target.files))}
            style={{ display: 'none' }}
            id="batch-upload-input"
          />
          <label htmlFor="batch-upload-input" className="btn-primary btn-large">
            📤 Upload Meerdere Foto's
          </label>
        </div>
        <p className="upload-hint">Tip: Groepeer foto's per scenario en upload ze in batches voor sneller labelen</p>
      </div>

      {/* Training Images Grid */}
      {trainingImages.length > 0 && (
        <div className="training-images-grid">
          <div className="training-images-header">
            <h4>Training Images ({filteredImages.length} van {trainingImages.length})</h4>

            {/* Filter Dropdown */}
            <div className="filter-controls">
              <label>Filter op label:</label>
              <select
                value={labelFilter}
                onChange={(e) => setLabelFilter(e.target.value)}
                className="label-filter-select"
              >
                <option value="all">Alle ({trainingImages.length})</option>
                <option value="unlabeled">
                  Unlabeled ({trainingImages.filter(img => !img.label || img.label === 'unlabeled').length})
                </option>
                <option value="OK">
                  OK ({trainingImages.filter(img => img.label === 'OK').length})
                </option>
                {workplace.items.map(item => {
                  const label = `NOK-${item}`;
                  const count = trainingImages.filter(img => img.label === label).length;
                  return (
                    <option key={label} value={label}>
                      {label} ({count})
                    </option>
                  );
                })}
              </select>
            </div>
          </div>

          <div className="images-grid">
            {filteredImages.map(img => (
              <div key={img.id} className="training-image-card">
                <img
                  src={`${API_URL}/${img.image_path}`}
                  alt={img.label}
                />
                <div className="image-info">
                  <span className={`label-badge ${img.label && img.label !== 'unlabeled' ? 'labeled' : 'unlabeled'}`}>
                    {img.label || 'Unlabeled'}
                  </span>
                </div>
                <div className="image-actions">
                  <button
                    onClick={() => handleEditLabel(img)}
                    className="btn-edit"
                    title="Label bewerken"
                  >
                    ✏️
                  </button>
                  <button
                    onClick={() => handleDeleteImage(img.id)}
                    className="btn-delete"
                    title="Foto verwijderen"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Batch Label Modal */}
      {showBatchLabelModal && (
        <div className="modal-overlay" onClick={() => setShowBatchLabelModal(false)}>
          <div className="modal-content-large" onClick={(e) => e.stopPropagation()}>
            <h2>Label {pendingPhotos.length} Foto's</h2>

            <div className="batch-preview-grid">
              {pendingPhotos.slice(0, 6).map((photo, idx) => (
                <img key={idx} src={photo.data} alt={photo.name} className="batch-preview-img" />
              ))}
              {pendingPhotos.length > 6 && (
                <div className="more-photos">+{pendingPhotos.length - 6} meer</div>
              )}
            </div>

            <div className="form-group">
              <label>Welke items ontbreken op deze foto's?</label>
              <div className="checkbox-group">
                {workplace.items.map(item => (
                  <label key={item} className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={missingItems.includes(item)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setMissingItems([...missingItems, item]);
                        } else {
                          setMissingItems(missingItems.filter(i => i !== item));
                        }
                      }}
                    />
                    <span>{item}</span>
                  </label>
                ))}
              </div>
              <small>
                {missingItems.length === 0 && '✓ Alle items aanwezig (OK)'}
                {missingItems.length === workplace.items.length && '⚠ Alle items ontbreken (Leeg)'}
                {missingItems.length > 0 && missingItems.length < workplace.items.length &&
                  `⚠ ${missingItems.join(', ')} ontbreekt`}
              </small>
            </div>

            {uploadingFiles && (
              <div className="upload-progress">
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${(uploadProgress.current / uploadProgress.total) * 100}%` }}
                  />
                </div>
                <p className="progress-text">
                  Uploading {uploadProgress.current} van {uploadProgress.total} foto's...
                </p>
              </div>
            )}

            <div className="modal-actions">
              <button onClick={() => { setShowBatchLabelModal(false); setMissingItems([]); }} className="btn-secondary" disabled={uploadingFiles}>
                Annuleren
              </button>
              <button onClick={saveBatchWithLabel} disabled={uploadingFiles} className="btn-primary">
                {uploadingFiles ? `Uploading ${uploadProgress.current}/${uploadProgress.total}...` : `${pendingPhotos.length} Foto's Opslaan`}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Label Modal */}
      {editingImage && (
        <div className="modal-overlay" onClick={() => setEditingImage(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Label Bewerken</h2>

            <div className="edit-image-preview">
              <img
                src={`${API_URL}/${editingImage.image_path}`}
                alt={editingImage.label}
                style={{ maxWidth: '100%', maxHeight: '300px', objectFit: 'contain' }}
              />
            </div>

            <div className="form-group">
              <label>Huidig Label: <strong>{editingImage.label || 'Unlabeled'}</strong></label>
            </div>

            <div className="form-group">
              <label>Nieuw Label:</label>
              <select
                value={newLabel}
                onChange={(e) => setNewLabel(e.target.value)}
                className="label-select"
              >
                <option value="">-- Kies een label --</option>
                <option value="OK">OK - Alle items aanwezig</option>
                {workplace.items.map(item => (
                  <option key={item} value={`NOK-${item}`}>NOK - {item} ontbreekt</option>
                ))}
              </select>
            </div>

            <div className="modal-actions">
              <button onClick={() => setEditingImage(null)} className="btn-secondary">
                Annuleren
              </button>
              <button onClick={saveEditedLabel} disabled={!newLabel} className="btn-primary">
                Opslaan
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ==========================================
// HELPER: Accuracy Circle Chart
// ==========================================
function AccuracyCircle({ accuracy, size = 120 }) {
  if (accuracy === null) {
    return (
      <div style={{textAlign: 'center'}}>
        <div style={{
          width: size,
          height: size,
          borderRadius: '50%',
          background: '#f7fafc',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          border: '4px solid #e2e8f0',
          margin: '0 auto'
        }}>
          <div style={{fontSize: '16px', color: '#999'}}>N/A</div>
        </div>
        <div style={{marginTop: '8px', fontSize: '12px', color: '#666'}}>Geen beoordelingen</div>
      </div>
    );
  }

  const circumference = 2 * Math.PI * 54; // radius = 54
  const offset = circumference - (accuracy / 100) * circumference;

  let color = '#e53e3e'; // Rood voor lage accuracy
  if (accuracy >= 80) color = '#48bb78'; // Groen voor hoge accuracy
  else if (accuracy >= 60) color = '#ed8936'; // Oranje voor medium accuracy

  return (
    <div style={{textAlign: 'center'}}>
      <svg width={size} height={size} style={{transform: 'rotate(-90deg)'}}>
        {/* Background circle */}
        <circle
          cx={size/2}
          cy={size/2}
          r="54"
          fill="none"
          stroke="#f0f0f0"
          strokeWidth="12"
        />
        {/* Progress circle */}
        <circle
          cx={size/2}
          cy={size/2}
          r="54"
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{transition: 'stroke-dashoffset 0.5s ease'}}
        />
        {/* Center text */}
        <text
          x="50%"
          y="50%"
          textAnchor="middle"
          dy="0.3em"
          fontSize="28"
          fontWeight="bold"
          fill={color}
          style={{transform: 'rotate(90deg)', transformOrigin: 'center'}}
        >
          {accuracy}%
        </text>
      </svg>
      <div style={{marginTop: '8px', fontSize: '12px', color: '#666', fontWeight: 'bold'}}>Accuracy</div>
    </div>
  );
}

// ==========================================
// TAB 4: MODEL PRESTATIES
// ==========================================
function ModelPerformanceTab({ workplaces, loading: workplacesLoading, selectedWorkplace, onWorkplaceChange }) {
  // Gebruik de shared selectedWorkplace van parent in plaats van lokale state
  const [workplaceData, setWorkplaceData] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadWorkplaceData = async (workplaceId) => {
    setLoading(true);
    try {
      // Haal analyses op voor deze werkplek
      const analysesResponse = await axios.get(`${API_URL}/api/history?workplace_id=${workplaceId}`);
      const analyses = analysesResponse.data.analyses;

      // Haal modellen op voor deze werkplek
      const modelsResponse = await axios.get(`${API_URL}/api/workplaces/${workplaceId}/models`);
      const models = modelsResponse.data.models;

      // Bereken statistieken per model
      const modelStats = models.map(model => {
        // Filter analyses voor dit model (gebaseerd op timestamp van model upload)
        const modelAnalyses = analyses.filter(a => {
          const analysisDate = new Date(a.created_at);
          const modelDate = new Date(model.uploaded_at);
          // Analyses zijn voor dit model als ze NA upload zijn en geen nieuwer model er is
          return analysisDate >= modelDate;
        });

        const reviewed = modelAnalyses.filter(a => a.corrected_label);
        const correct = reviewed.filter(a => a.predicted_label === a.corrected_label);
        const incorrect = reviewed.filter(a => a.predicted_label !== a.corrected_label);
        const accuracy = reviewed.length > 0 ? Math.round((correct.length / reviewed.length) * 100) : null;

        // Analyseer waar het model het meest fout zit
        // Tel op welke labels het model fout voorspelt
        const errorsByLabel = {};
        incorrect.forEach(analysis => {
          const label = analysis.corrected_label || 'Unknown';
          errorsByLabel[label] = (errorsByLabel[label] || 0) + 1;
        });

        // Sorteer op meest voorkomende fouten
        const topErrors = Object.entries(errorsByLabel)
          .map(([label, count]) => ({ label, count }))
          .sort((a, b) => b.count - a.count)
          .slice(0, 5); // Top 5 fouten

        return {
          ...model,
          analyses_count: modelAnalyses.length,
          reviewed_count: reviewed.length,
          correct_count: correct.length,
          incorrect_count: incorrect.length,
          unreviewed_count: modelAnalyses.length - reviewed.length,
          accuracy: accuracy,
          top_errors: topErrors,
          incorrect_analyses: incorrect // Voor detail analyse
        };
      });

      setWorkplaceData({
        analyses,
        models: modelStats
      });
    } catch (error) {
      console.error('Error loading workplace data:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    if (selectedWorkplace) {
      loadWorkplaceData(selectedWorkplace.id);
    }
  }, [selectedWorkplace]);

  if (workplacesLoading) {
    return <div className="loading">Laden...</div>;
  }

  if (!workplaces || workplaces.length === 0) {
    return (
      <div className="empty-state">
        <p>⚠️ Geen werkplekken gevonden. Voeg eerst werkplekken toe in het Werkplekken Beheer tab.</p>
      </div>
    );
  }

  return (
    <div className="model-performance-tab">
      <h2>🤖 Model Prestaties per Werkplek</h2>
      <p style={{color: '#666', marginBottom: '20px'}}>
        Selecteer een werkplek om de prestaties van de verschillende model versies te bekijken
      </p>

      {/* Workplace Selector */}
      <div style={{marginBottom: '20px'}}>
        <label style={{fontWeight: 'bold', marginBottom: '8px', display: 'block'}}>Selecteer Werkplek:</label>
        <select
          value={selectedWorkplace?.id || ''}
          onChange={(e) => {
            const wp = workplaces.find(w => w.id === parseInt(e.target.value));
            onWorkplaceChange(wp);
          }}
          style={{
            padding: '10px',
            fontSize: '14px',
            borderRadius: '6px',
            border: '1px solid #e2e8f0',
            minWidth: '300px'
          }}
        >
          <option value="">-- Kies een werkplek --</option>
          {workplaces.map(wp => (
            <option key={wp.id} value={wp.id}>
              {wp.name} ({wp.items ? wp.items.join(', ') : 'Geen items'})
            </option>
          ))}
        </select>
      </div>

      {/* Loading State */}
      {loading && <div className="loading">Laden...</div>}

      {/* Workplace Data */}
      {!loading && selectedWorkplace && workplaceData && (
        <div>
          <div style={{
            background: '#f8f9fa',
            padding: '20px',
            borderRadius: '8px',
            marginBottom: '20px'
          }}>
            <h3 style={{marginTop: 0}}>{selectedWorkplace.name}</h3>
            <p style={{color: '#666', marginBottom: '10px'}}>
              Items: {selectedWorkplace.items ? selectedWorkplace.items.join(', ') : 'Geen items'}
            </p>
            <div style={{display: 'flex', gap: '20px', marginTop: '15px'}}>
              <div>
                <div style={{fontSize: '24px', fontWeight: 'bold', color: '#4299e1'}}>
                  {workplaceData.analyses.length}
                </div>
                <div style={{fontSize: '12px', color: '#666'}}>Totaal Analyses</div>
              </div>
              <div>
                <div style={{fontSize: '24px', fontWeight: 'bold', color: '#48bb78'}}>
                  {workplaceData.models.length}
                </div>
                <div style={{fontSize: '12px', color: '#666'}}>Geüploade Modellen</div>
              </div>
            </div>
          </div>

          {/* Model Stats with Charts */}
          {workplaceData.models.length > 0 ? (
            <div>
              {/* Comparison Chart */}
              {workplaceData.models.length > 1 && (
                <div style={{
                  background: '#f8f9fa',
                  padding: '20px',
                  borderRadius: '12px',
                  marginBottom: '30px',
                  border: '1px solid #e2e8f0'
                }}>
                  <h3 style={{marginTop: 0}}>📊 Model Vergelijking</h3>
                  <p style={{fontSize: '13px', color: '#666', marginBottom: '20px'}}>
                    Vergelijk alle model versies op accuracy en aantal analyses
                  </p>

                  {/* Accuracy Comparison Bar Chart */}
                  <div style={{marginBottom: '30px'}}>
                    <div style={{fontSize: '14px', fontWeight: 'bold', marginBottom: '15px', color: '#4a5568'}}>
                      Accuracy Vergelijking
                    </div>
                    {workplaceData.models.map((model, idx) => {
                      const hasAccuracy = model.accuracy !== null;
                      const accuracyColor = !hasAccuracy ? '#cbd5e0' :
                        model.accuracy >= 80 ? '#48bb78' :
                        model.accuracy >= 60 ? '#ed8936' : '#e53e3e';

                      return (
                        <div key={model.id} style={{marginBottom: '12px'}}>
                          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px'}}>
                            <div style={{flex: 1}}>
                              <span style={{fontSize: '13px', fontWeight: '500', color: '#2d3748'}}>
                                {model.version}
                              </span>
                              {model.status === 'active' && (
                                <span style={{
                                  marginLeft: '8px',
                                  fontSize: '11px',
                                  padding: '2px 6px',
                                  background: '#48bb78',
                                  color: 'white',
                                  borderRadius: '3px'
                                }}>
                                  ACTIEF
                                </span>
                              )}
                            </div>
                            <div style={{fontSize: '13px', fontWeight: 'bold', color: accuracyColor, minWidth: '60px', textAlign: 'right'}}>
                              {hasAccuracy ? `${model.accuracy}%` : 'N/A'}
                            </div>
                          </div>
                          <div style={{
                            height: '24px',
                            background: '#e2e8f0',
                            borderRadius: '6px',
                            overflow: 'hidden',
                            position: 'relative'
                          }}>
                            <div style={{
                              width: hasAccuracy ? `${model.accuracy}%` : '100%',
                              height: '100%',
                              background: accuracyColor,
                              display: 'flex',
                              alignItems: 'center',
                              paddingLeft: '8px',
                              color: 'white',
                              fontSize: '11px',
                              fontWeight: 'bold',
                              transition: 'width 0.5s ease'
                            }}>
                              {hasAccuracy && model.reviewed_count > 0 && `${model.reviewed_count} beoordeeld`}
                            </div>
                            {!hasAccuracy && (
                              <div style={{
                                position: 'absolute',
                                top: 0,
                                left: 0,
                                right: 0,
                                bottom: 0,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                color: '#718096',
                                fontSize: '11px',
                                fontStyle: 'italic'
                              }}>
                                Geen beoordelingen beschikbaar
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Volume Comparison */}
                  <div>
                    <div style={{fontSize: '14px', fontWeight: 'bold', marginBottom: '15px', color: '#4a5568'}}>
                      Aantal Analyses per Model
                    </div>
                    <div style={{display: 'flex', gap: '15px', alignItems: 'flex-end', height: '150px'}}>
                      {workplaceData.models.map(model => {
                        const maxAnalyses = Math.max(...workplaceData.models.map(m => m.analyses_count), 1);
                        const barHeight = (model.analyses_count / maxAnalyses) * 100;

                        return (
                          <div key={model.id} style={{
                            flex: 1,
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            height: '100%'
                          }}>
                            <div style={{flex: 1, display: 'flex', alignItems: 'flex-end', width: '100%'}}>
                              <div style={{
                                width: '100%',
                                height: `${barHeight}%`,
                                background: model.status === 'active'
                                  ? 'linear-gradient(180deg, #48bb78, #38a169)'
                                  : 'linear-gradient(180deg, #4299e1, #3182ce)',
                                borderRadius: '6px 6px 0 0',
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                justifyContent: 'flex-start',
                                paddingTop: '8px',
                                color: 'white',
                                fontSize: '14px',
                                fontWeight: 'bold',
                                minHeight: '30px',
                                transition: 'height 0.5s ease'
                              }}>
                                {model.analyses_count}
                              </div>
                            </div>
                            <div style={{
                              marginTop: '8px',
                              fontSize: '11px',
                              color: '#4a5568',
                              textAlign: 'center',
                              fontWeight: '500',
                              maxWidth: '100%',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }}>
                              {model.version.length > 15 ? model.version.substring(0, 12) + '...' : model.version}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}

              <h3>📊 Model Versie Prestaties</h3>
              <div style={{display: 'flex', flexDirection: 'column', gap: '20px'}}>
                {workplaceData.models.map(model => {
                  const maxCount = Math.max(model.analyses_count, 1);
                  const correctWidth = (model.correct_count / maxCount) * 100;
                  const incorrectWidth = (model.incorrect_count / maxCount) * 100;
                  const unreviewedWidth = (model.unreviewed_count / maxCount) * 100;

                  return (
                    <div key={model.id} style={{
                      padding: '20px',
                      background: model.status === 'active' ? '#f0fff4' : '#fff',
                      border: model.status === 'active' ? '2px solid #48bb78' : '1px solid #e2e8f0',
                      borderRadius: '12px',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
                    }}>
                      {/* Header */}
                      <div style={{marginBottom: '20px'}}>
                        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                          <div>
                            <div style={{fontWeight: 'bold', fontSize: '18px', marginBottom: '5px'}}>
                              {model.version}
                              {model.status === 'active' && (
                                <span style={{
                                  marginLeft: '10px',
                                  padding: '4px 10px',
                                  background: '#48bb78',
                                  color: 'white',
                                  borderRadius: '4px',
                                  fontSize: '12px'
                                }}>
                                  ● ACTIEF
                                </span>
                              )}
                            </div>
                            <div style={{fontSize: '13px', color: '#666'}}>
                              {model.model_type === 'detection' ? '🔍 Detection' : '📊 Classification'} •
                              Geüpload: {new Date(model.uploaded_at).toLocaleDateString('nl-NL')}
                            </div>
                          </div>
                          <AccuracyCircle accuracy={model.accuracy} size={100} />
                        </div>
                      </div>

                      {/* Stacked Bar Chart */}
                      <div style={{marginBottom: '15px'}}>
                        <div style={{fontSize: '13px', fontWeight: 'bold', marginBottom: '8px', color: '#4a5568'}}>
                          Analyse Overzicht ({model.analyses_count} totaal)
                        </div>
                        <div style={{
                          display: 'flex',
                          height: '30px',
                          borderRadius: '6px',
                          overflow: 'hidden',
                          background: '#f7fafc'
                        }}>
                          {model.correct_count > 0 && (
                            <div style={{
                              width: `${correctWidth}%`,
                              background: 'linear-gradient(90deg, #48bb78, #38a169)',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              color: 'white',
                              fontSize: '12px',
                              fontWeight: 'bold'
                            }}>
                              {model.correct_count > 0 && `${model.correct_count} ✓`}
                            </div>
                          )}
                          {model.incorrect_count > 0 && (
                            <div style={{
                              width: `${incorrectWidth}%`,
                              background: 'linear-gradient(90deg, #f56565, #e53e3e)',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              color: 'white',
                              fontSize: '12px',
                              fontWeight: 'bold'
                            }}>
                              {model.incorrect_count > 0 && `${model.incorrect_count} ✗`}
                            </div>
                          )}
                          {model.unreviewed_count > 0 && (
                            <div style={{
                              width: `${unreviewedWidth}%`,
                              background: 'linear-gradient(90deg, #cbd5e0, #a0aec0)',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              color: 'white',
                              fontSize: '12px',
                              fontWeight: 'bold'
                            }}>
                              {model.unreviewed_count > 0 && `${model.unreviewed_count} ⏳`}
                            </div>
                          )}
                        </div>
                        <div style={{display: 'flex', justifyContent: 'space-between', marginTop: '8px', fontSize: '11px'}}>
                          <span style={{color: '#48bb78'}}>✓ {model.correct_count} Correct</span>
                          <span style={{color: '#e53e3e'}}>✗ {model.incorrect_count} Fout</span>
                          <span style={{color: '#a0aec0'}}>⏳ {model.unreviewed_count} Onbeoordeeld</span>
                        </div>
                      </div>

                      {/* Details Grid */}
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                        gap: '12px',
                        marginTop: '15px'
                      }}>
                        <div style={{padding: '10px', background: '#ebf8ff', borderRadius: '6px'}}>
                          <div style={{fontSize: '20px', fontWeight: 'bold', color: '#2b6cb0'}}>
                            {model.analyses_count}
                          </div>
                          <div style={{fontSize: '11px', color: '#2c5282'}}>Totaal Analyses</div>
                        </div>
                        <div style={{padding: '10px', background: '#f0fff4', borderRadius: '6px'}}>
                          <div style={{fontSize: '20px', fontWeight: 'bold', color: '#2f855a'}}>
                            {model.reviewed_count}
                          </div>
                          <div style={{fontSize: '11px', color: '#276749'}}>Beoordeeld</div>
                        </div>
                        {model.test_accuracy && (
                          <div style={{padding: '10px', background: '#fef5e7', borderRadius: '6px'}}>
                            <div style={{fontSize: '20px', fontWeight: 'bold', color: '#c05621'}}>
                              {model.test_accuracy}%
                            </div>
                            <div style={{fontSize: '11px', color: '#9c4221'}}>Test Accuracy</div>
                          </div>
                        )}
                      </div>

                      {/* Error Analysis */}
                      {model.top_errors && model.top_errors.length > 0 && (
                        <div style={{marginTop: '20px', paddingTop: '15px', borderTop: '1px solid #e2e8f0'}}>
                          <div style={{fontSize: '14px', fontWeight: 'bold', marginBottom: '12px', color: '#e53e3e'}}>
                            ⚠️ Waar gaat het model fout? (Top {model.top_errors.length} fouten)
                          </div>
                          <div style={{
                            background: '#fff5f5',
                            padding: '12px',
                            borderRadius: '6px',
                            border: '1px solid #feb2b2'
                          }}>
                            {model.top_errors.map((error, idx) => {
                              const percentage = model.incorrect_count > 0
                                ? Math.round((error.count / model.incorrect_count) * 100)
                                : 0;

                              return (
                                <div key={idx} style={{marginBottom: idx < model.top_errors.length - 1 ? '10px' : '0'}}>
                                  <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px'}}>
                                    <span style={{fontSize: '13px', fontWeight: '500', color: '#742a2a'}}>
                                      {error.label}
                                    </span>
                                    <span style={{fontSize: '12px', color: '#9b2c2c'}}>
                                      {error.count}x ({percentage}% van fouten)
                                    </span>
                                  </div>
                                  <div style={{
                                    height: '8px',
                                    background: '#fed7d7',
                                    borderRadius: '4px',
                                    overflow: 'hidden'
                                  }}>
                                    <div style={{
                                      width: `${percentage}%`,
                                      height: '100%',
                                      background: 'linear-gradient(90deg, #fc8181, #e53e3e)',
                                      transition: 'width 0.3s ease'
                                    }} />
                                  </div>
                                </div>
                              );
                            })}
                            <div style={{
                              marginTop: '10px',
                              paddingTop: '10px',
                              borderTop: '1px solid #feb2b2',
                              fontSize: '11px',
                              color: '#9b2c2c',
                              fontStyle: 'italic'
                            }}>
                              💡 Tip: Focus training data op deze situaties om het model te verbeteren
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Notes & File */}
                      <div style={{marginTop: '15px', paddingTop: '15px', borderTop: '1px solid #e2e8f0'}}>
                        <div style={{fontSize: '11px', color: '#999', fontFamily: 'monospace', marginBottom: '5px'}}>
                          📁 {model.model_path ? model.model_path.split('/').pop() : 'N/A'}
                        </div>
                        {model.notes && (
                          <div style={{
                            fontSize: '12px',
                            fontStyle: 'italic',
                            color: '#666',
                            marginTop: '8px'
                          }}>
                            💬 {model.notes}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="empty-state-small" style={{padding: '20px', background: '#fff3cd', borderRadius: '8px'}}>
              <p>⚠️ Geen modellen gevonden voor deze werkplek. Upload een model in het Werkplekken Beheer tab.</p>
            </div>
          )}
        </div>
      )}

      {!loading && selectedWorkplace && !workplaceData && (
        <div className="empty-state-small" style={{padding: '20px', background: '#f7fafc', borderRadius: '8px'}}>
          <p>Selecteer een werkplek om de prestaties te bekijken</p>
        </div>
      )}
    </div>
  );
}

// Whiteboard Region Selector Component
function WhiteboardRegionSelector({ workplace, onRegionSaved, showToast }) {
  const [isDrawing, setIsDrawing] = useState(false);
  const [startPos, setStartPos] = useState(null);
  const [currentPos, setCurrentPos] = useState(null);
  const [savedRegion, setSavedRegion] = useState(workplace.whiteboard_region || null);
  const imageRef = React.useRef(null);

  const handleMouseDown = (e) => {
    if (!imageRef.current) return;
    const rect = imageRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;
    setStartPos({ x, y });
    setIsDrawing(true);
  };

  const handleMouseMove = (e) => {
    if (!isDrawing || !imageRef.current) return;
    const rect = imageRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;
    setCurrentPos({ x, y });
  };

  const handleMouseUp = async () => {
    if (!isDrawing || !startPos || !currentPos) return;
    setIsDrawing(false);

    // Bereken region (normaliseer zodat x1 < x2 en y1 < y2)
    const region = {
      x1: Math.min(startPos.x, currentPos.x),
      y1: Math.min(startPos.y, currentPos.y),
      x2: Math.max(startPos.x, currentPos.x),
      y2: Math.max(startPos.y, currentPos.y)
    };

    // Sla region op
    try {
      const response = await axios.post(
        `${API_URL}/api/workplaces/${workplace.id}/whiteboard-region`,
        region
      );
      if (response.data.success) {
        setSavedRegion(region);
        showToast('Whiteboard gebied opgeslagen', 'success');
        if (onRegionSaved) onRegionSaved();
      }
    } catch (error) {
      console.error('Error saving region:', error);
      showToast('Fout bij opslaan gebied', 'error');
    }

    setStartPos(null);
    setCurrentPos(null);
  };

  const clearRegion = async () => {
    try {
      const response = await axios.post(
        `${API_URL}/api/workplaces/${workplace.id}/whiteboard-region`,
        { x1: 0, y1: 0, x2: 0, y2: 0 }
      );
      if (response.data.success) {
        setSavedRegion(null);
        showToast('Whiteboard gebied verwijderd', 'success');
        if (onRegionSaved) onRegionSaved();
      }
    } catch (error) {
      console.error('Error clearing region:', error);
      showToast('Fout bij verwijderen gebied', 'error');
    }
  };

  const getBoxStyle = (region) => {
    if (!region || !imageRef.current) return {};
    const rect = imageRef.current.getBoundingClientRect();
    return {
      position: 'absolute',
      left: `${region.x1 * 100}%`,
      top: `${region.y1 * 100}%`,
      width: `${(region.x2 - region.x1) * 100}%`,
      height: `${(region.y2 - region.y1) * 100}%`,
      border: '3px solid #48bb78',
      boxShadow: '0 0 20px rgba(72, 187, 120, 0.6)',
      pointerEvents: 'none',
      zIndex: 10
    };
  };

  const getCurrentDrawingBox = () => {
    if (!isDrawing || !startPos || !currentPos) return null;
    return {
      x1: Math.min(startPos.x, currentPos.x),
      y1: Math.min(startPos.y, currentPos.y),
      x2: Math.max(startPos.x, currentPos.x),
      y2: Math.max(startPos.y, currentPos.y)
    };
  };

  return (
    <div className="detail-section">
      <h4>Whiteboard Gebied (Ghost Overlay)</h4>
      <p style={{ fontSize: '14px', color: '#666', marginBottom: '10px' }}>
        Sleep met de muis over de referentie foto om het whiteboard gebied te markeren.
        Dit gebied wordt gemarkeerd in de operator interface om de foto beter uit te lijnen.
      </p>
      <div style={{ position: 'relative', display: 'inline-block', width: '100%' }}>
        <img
          ref={imageRef}
          src={`${API_URL}${workplace.reference_photo}`}
          alt="Referentie"
          style={{
            width: '100%',
            maxWidth: '600px',
            cursor: 'crosshair',
            userSelect: 'none'
          }}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={() => {
            if (isDrawing) handleMouseUp();
          }}
        />
        {savedRegion && <div style={getBoxStyle(savedRegion)}></div>}
        {isDrawing && getCurrentDrawingBox() && (
          <div style={{ ...getBoxStyle(getCurrentDrawingBox()), border: '3px dashed #48bb78' }}></div>
        )}
      </div>
      {savedRegion && (
        <button
          onClick={clearRegion}
          className="btn-secondary"
          style={{ marginTop: '10px' }}
        >
          Verwijder Whiteboard Gebied
        </button>
      )}
    </div>
  );
}

export default Admin;
