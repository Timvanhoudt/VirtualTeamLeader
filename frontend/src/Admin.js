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

  // Load workplaces bij mount
  useEffect(() => {
    loadWorkplaces();
  }, []);

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
          className={activeTab === 'models' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('models')}
        >
          Modellen
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
          />
        )}

        {activeTab === 'review' && (
          <ReviewAnalysisTab workplaces={workplaces} loading={loading} />
        )}

        {activeTab === 'training' && (
          <TrainingDataTab
            workplaces={workplaces}
            loading={loading}
          />
        )}

        {activeTab === 'models' && (
          <ModelsTab
            workplaces={workplaces}
            loading={loading}
          />
        )}

        {activeTab === 'performance' && (
          <ModelPerformanceTab workplaces={workplaces} loading={loading} />
        )}
      </div>
    </div>
  );
}

// ==========================================
// TAB 1: WERKPLEKKEN BEHEER
// ==========================================
function WorkplacesManagementTab({ workplaces, loading, onRefresh }) {
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
        alert('Werkplek aangemaakt!');
        setShowAddModal(false);
        setNewWorkplace({ name: '', description: '', items: '' });
        onRefresh();
      }
    } catch (error) {
      console.error('Error adding workplace:', error);
      alert('Fout bij toevoegen werkplek');
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
        alert('Werkplek bijgewerkt!');
        setShowEditModal(false);
        onRefresh();
        if (selectedWorkplace && selectedWorkplace.workplace.id === editWorkplace.id) {
          loadWorkplaceDetails(editWorkplace.id);
        }
      }
    } catch (error) {
      console.error('Error updating workplace:', error);
      alert('Fout bij bijwerken werkplek');
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
        alert('Werkplek verwijderd!');
        setSelectedWorkplace(null);
        onRefresh();
      }
    } catch (error) {
      console.error('Error deleting workplace:', error);
      alert('Fout bij verwijderen werkplek');
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
        alert('Referentie foto geüpload!');
        loadWorkplaceDetails(workplaceId);
      }
    } catch (error) {
      console.error('Error uploading reference photo:', error);
      alert('Fout bij uploaden foto');
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

              <div className="detail-section">
                <div className="section-header">
                  <h4>Gekoppeld Model</h4>
                </div>
                {models.length === 0 ? (
                  <p>Geen model gekoppeld. Ga naar Modellen tab om een model te uploaden en te activeren.</p>
                ) : (
                  <div className="active-model-info">
                    {models.find(m => m.status === 'active') ? (
                      <div className="model-card active">
                        <div className="model-badge">ACTIEF MODEL</div>
                        <p><strong>Versie:</strong> {models.find(m => m.status === 'active').version}</p>
                        {models.find(m => m.status === 'active').test_accuracy && (
                          <p><strong>Accuracy:</strong> {models.find(m => m.status === 'active').test_accuracy}%</p>
                        )}
                        <p><strong>Geüpload:</strong> {new Date(models.find(m => m.status === 'active').uploaded_at).toLocaleString('nl-NL')}</p>
                      </div>
                    ) : (
                      <p>Er zijn {models.length} model(len) beschikbaar maar geen is actief. Ga naar Modellen tab om een model te activeren.</p>
                    )}
                  </div>
                )}
              </div>

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
function TrainingDataTab({ workplaces, loading }) {
  const [selectedWorkplace, setSelectedWorkplace] = useState(null);
  const [hasActiveModel, setHasActiveModel] = useState(false);

  // Check of werkplek actief model heeft
  useEffect(() => {
    if (selectedWorkplace) {
      checkActiveModel(selectedWorkplace.id);
    }
  }, [selectedWorkplace]);

  const checkActiveModel = async (workplaceId) => {
    try {
      const response = await axios.get(`${API_URL}/api/workplaces/${workplaceId}/models`);
      if (response.data.success) {
        const hasActive = response.data.models.some(m => m.status === 'active');
        setHasActiveModel(hasActive);
      }
    } catch (error) {
      console.error('Error checking model:', error);
      setHasActiveModel(false);
    }
  };

  return (
    <div className="training-data-tab">
      <div className="tab-header">
        <h2>Training Data Management</h2>
      </div>

      {/* Werkplek Selector */}
      <div className="workplace-selector">
        <label>Selecteer Werkplek:</label>
        <select
          value={selectedWorkplace?.id || ''}
          onChange={(e) => {
            const wp = workplaces.find(w => w.id === parseInt(e.target.value));
            setSelectedWorkplace(wp);
          }}
          className="workplace-select"
        >
          <option value="">-- Kies een werkplek --</option>
          {workplaces.map(wp => (
            <option key={wp.id} value={wp.id}>{wp.name}</option>
          ))}
        </select>
      </div>

      {selectedWorkplace && (
        <>
          {hasActiveModel ? (
            <ProductionReviewSection workplace={selectedWorkplace} />
          ) : (
            <NewWorkplaceTrainingSection workplace={selectedWorkplace} />
          )}
        </>
      )}
    </div>
  );
}

// ==========================================
// TAB 2: BEOORDELINGS ANALYSE
// ==========================================
function ReviewAnalysisTab({ workplaces, loading: workplacesLoading }) {
  const [selectedWorkplace, setSelectedWorkplace] = useState(null);
  const [analyses, setAnalyses] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [correctingId, setCorrectingId] = useState(null);
  const [confidenceThreshold, setConfidenceThreshold] = useState(70);
  const [itemsMissing, setItemsMissing] = useState({
    hamer: false,
    schaar: false,
    sleutel: false
  });

  // Auto-select eerste werkplek
  useEffect(() => {
    if (workplaces.length > 0 && !selectedWorkplace) {
      setSelectedWorkplace(workplaces[0]);
    }
  }, [workplaces, selectedWorkplace]);

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
    setCorrectingId(analysisId);
    setItemsMissing({ hamer: false, schaar: false, sleutel: false });
  };

  const toggleMissingItem = (item) => {
    setItemsMissing(prev => ({
      ...prev,
      [item]: !prev[item]
    }));
  };

  const submitCorrection = (analysisId) => {
    const category = determineCategory(itemsMissing);
    correctAnalysis(analysisId, category.class, category.label);
  };

  useEffect(() => {
    if (selectedWorkplace) {
      loadHistory();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter, selectedWorkplace]);

  const loadHistory = async () => {
    if (!selectedWorkplace) return;

    setLoading(true);
    try {
      const filterParam = filter !== 'all' ? `?status=${filter}` : '';
      const response = await axios.get(`${API_URL}/api/history${filterParam}`);

      if (response.data.analyses) {
        const allAnalyses = response.data.analyses;

        // Filter: toon ALLEEN analyses die bij deze werkplek horen EN nog NIET beoordeeld zijn
        const workplaceAnalyses = allAnalyses.filter(a =>
          a.workplace_id === selectedWorkplace.id && !a.corrected_label
        );

        setAnalyses(workplaceAnalyses);
      }
    } catch (error) {
      console.error('Error loading history:', error);
      alert('Fout bij laden geschiedenis: ' + error.message);
    } finally {
      setLoading(false);
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

      alert(`✓ Analyse gecorrigeerd naar: ${correctedLabel}`);
      setCorrectingId(null);
      loadHistory();
    } catch (error) {
      console.error('Error correcting analysis:', error);
      alert('Fout bij opslaan correctie: ' + error.message);
    }
  };

  const downloadCSV = async () => {
    try {
      window.open(`${API_URL}/api/export/csv`, '_blank');
    } catch (error) {
      alert('Fout bij downloaden CSV: ' + error.message);
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

  // Bereken statistieken voor deze specifieke werkplek
  const unreviewedCount = analyses.filter(a => !a.corrected_label).length;
  const reviewedCount = analyses.filter(a => a.corrected_label).length;
  const totalCount = analyses.length;
  const okCount = analyses.filter(a => a.status === 'OK').length;
  const nokCount = analyses.filter(a => a.status === 'NOK').length;

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
            setSelectedWorkplace(wp);
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

      {/* Filters and Actions */}
      {selectedWorkplace && !loading && (
        <div className="history-controls">
          <div className="filter-buttons">
            <button
              className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
              onClick={() => setFilter('all')}
            >
              Alles ({totalCount})
            </button>
            <button
              className={`filter-btn ${filter === 'OK' ? 'active' : ''}`}
              onClick={() => setFilter('OK')}
            >
              OK ({okCount})
            </button>
            <button
              className={`filter-btn ${filter === 'NOK' ? 'active' : ''}`}
              onClick={() => setFilter('NOK')}
            >
              NOK ({nokCount})
            </button>
          </div>

        <div className="confidence-threshold-control">
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
          <small>Analyses onder {confidenceThreshold}% gaan naar Model Prestaties</small>
        </div>

          <button onClick={downloadCSV} className="download-btn">
            📥 Download CSV
          </button>
        </div>
      )}

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
                </div>

                {analysis.corrected_label && (
                  <div className="correction-badge">
                    ✏️ Gecorrigeerd naar: {analysis.corrected_label}
                  </div>
                )}

                {/* Correction UI */}
                {correctingId === analysis.id ? (
                  <div className="correction-panel">
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
function ProductionReviewSection({ workplace }) {
  const [loading, setLoading] = useState(false);
  const [trainingCandidates, setTrainingCandidates] = useState([]);
  const [selectedCandidates, setSelectedCandidates] = useState([]);
  const [confidenceThreshold, setConfidenceThreshold] = useState(70);

  useEffect(() => {
    loadTrainingCandidates();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workplace, confidenceThreshold]);

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
function NewWorkplaceTrainingSection({ workplace }) {
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
// TAB 3: MODELLEN
// ==========================================
function ModelsTab({ workplaces }) {
  const [selectedWorkplaceId, setSelectedWorkplaceId] = useState(null);
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadData, setUploadData] = useState({
    file: null,
    version: '',
    test_accuracy: '',
    notes: ''
  });
  const [uploading, setUploading] = useState(false);

  // Load models voor werkplek
  const loadModels = async (workplaceId) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/api/workplaces/${workplaceId}/models`);
      if (response.data.success) {
        setModels(response.data.models);
      }
    } catch (error) {
      console.error('Error loading models:', error);
      alert('Fout bij laden modellen');
    }
    setLoading(false);
  };

  // Handle werkplek selectie
  const handleWorkplaceSelect = (workplaceId) => {
    setSelectedWorkplaceId(workplaceId);
    loadModels(workplaceId);
  };

  // Handle file selection
  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file && file.name.endsWith('.pt')) {
      setUploadData({...uploadData, file: file});
    } else {
      alert('Alleen .pt bestanden zijn toegestaan');
      e.target.value = '';
    }
  };

  // Handle model upload
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

      const response = await axios.post(`${API_URL}/api/workplaces/${selectedWorkplaceId}/models`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (response.data.success) {
        alert(`Model ${response.data.version} succesvol geüpload!`);
        setShowUploadModal(false);
        setUploadData({ file: null, version: '', test_accuracy: '', notes: '' });
        loadModels(selectedWorkplaceId);
      }
    } catch (error) {
      console.error('Error uploading model:', error);
      alert('Fout bij uploaden model');
    }

    setUploading(false);
  };

  // Handle model activation
  const handleActivateModel = async (modelId) => {
    if (!window.confirm('Dit model activeren? Het huidige actieve model wordt gearchiveerd.')) {
      return;
    }

    try {
      const response = await axios.post(`${API_URL}/api/models/${modelId}/activate`);

      if (response.data.success) {
        alert('Model geactiveerd!');
        loadModels(selectedWorkplaceId);
      }
    } catch (error) {
      console.error('Error activating model:', error);
      alert('Fout bij activeren model');
    }
  };

  return (
    <div className="models-tab">
      <div className="tab-header">
        <h2>Model Management</h2>
        {selectedWorkplaceId && (
          <button onClick={() => setShowUploadModal(true)} className="btn-primary">
            ⬆️ Upload Model
          </button>
        )}
      </div>

      {/* Werkplek Selector */}
      <div className="workplace-selector">
        <label>Selecteer Werkplek:</label>
        <select
          value={selectedWorkplaceId || ''}
          onChange={(e) => handleWorkplaceSelect(e.target.value)}
          className="workplace-select"
        >
          <option value="">-- Kies een werkplek --</option>
          {workplaces.map(wp => (
            <option key={wp.id} value={wp.id}>{wp.name}</option>
          ))}
        </select>
      </div>

      {selectedWorkplaceId && (
        <>
          {loading && <p>Laden...</p>}

          {!loading && models.length === 0 && (
            <div className="empty-state">
              <p>Geen modellen gevonden. Upload een getraind model om te beginnen!</p>
            </div>
          )}

          {!loading && models.length > 0 && (
            <div className="models-list-section">
              <h3>Modellen ({models.length})</h3>
              <div className="models-table">
                <div className="table-header">
                  <span>Versie</span>
                  <span>Status</span>
                  <span>Accuracy</span>
                  <span>Upload Datum</span>
                  <span>Acties</span>
                </div>
                {models.map(model => (
                  <div key={model.id} className={`table-row ${model.status === 'active' ? 'active-row' : ''}`}>
                    <span className="model-version-cell">
                      {model.version}
                      {model.status === 'active' && <span className="active-badge">ACTIEF</span>}
                    </span>
                    <span>
                      <span className={`status-badge status-${model.status}`}>
                        {model.status}
                      </span>
                    </span>
                    <span className="accuracy-cell">
                      {model.test_accuracy ? `${model.test_accuracy}%` : '-'}
                    </span>
                    <span className="date-cell">
                      {new Date(model.uploaded_at).toLocaleString('nl-NL')}
                    </span>
                    <span className="actions-cell">
                      {model.status !== 'active' && (
                        <button
                          onClick={() => handleActivateModel(model.id)}
                          className="btn-activate"
                        >
                          Activeer
                        </button>
                      )}
                      {model.status === 'active' && (
                        <span className="current-label">In gebruik</span>
                      )}
                    </span>
                  </div>
                ))}
              </div>

              {/* Model Info */}
              <div className="model-info-section">
                <h4>ℹ️ Model Informatie</h4>
                <div className="info-grid">
                  <div className="info-item">
                    <strong>Actief Model:</strong>
                    <span>{models.find(m => m.status === 'active')?.version || 'Geen'}</span>
                  </div>
                  <div className="info-item">
                    <strong>Totaal Modellen:</strong>
                    <span>{models.length}</span>
                  </div>
                  <div className="info-item">
                    <strong>Gearchiveerd:</strong>
                    <span>{models.filter(m => m.status === 'archived').length}</span>
                  </div>
                  <div className="info-item">
                    <strong>Beste Accuracy:</strong>
                    <span>
                      {Math.max(...models.filter(m => m.test_accuracy).map(m => m.test_accuracy)) || '-'}
                      {models.some(m => m.test_accuracy) && '%'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="modal-overlay" onClick={() => setShowUploadModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Model Uploaden</h2>
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
                  <small className="file-selected">✓ {uploadData.file.name}</small>
                )}
              </div>

              <div className="form-group">
                <label>Versie</label>
                <input
                  type="text"
                  value={uploadData.version}
                  onChange={(e) => setUploadData({...uploadData, version: e.target.value})}
                  placeholder="Bijv. v1.0, v1.1 (optioneel, wordt auto-gegenereerd)"
                />
                <small>Laat leeg voor automatische versie nummering</small>
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
                <small>Accuracy van validation set uit training</small>
              </div>

              <div className="form-group">
                <label>Notities</label>
                <textarea
                  value={uploadData.notes}
                  onChange={(e) => setUploadData({...uploadData, notes: e.target.value})}
                  placeholder="Training details, dataset size, epochs, etc."
                  rows="4"
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
// TAB 4: MODEL PRESTATIES
// ==========================================
function ModelPerformanceTab({ workplaces, loading: workplacesLoading }) {
  const [analyses, setAnalyses] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // Load ALL analyses from ALL workplaces
      const analysesResponse = await axios.get(`${API_URL}/api/history`);
      const allAnalyses = analysesResponse.data.analyses;

      setAnalyses(allAnalyses);

      // Bereken globale statistieken voor alle werkplekken
      const globalStats = {
        total: allAnalyses.length,
        reviewed: allAnalyses.filter(a => a.corrected_label).length,
        ok: allAnalyses.filter(a => a.corrected_label === 'OK').length,
        nok: allAnalyses.filter(a => a.corrected_label && a.corrected_label !== 'OK').length,
        unreviewed: allAnalyses.filter(a => !a.corrected_label).length
      };
      setStatistics(globalStats);
    } catch (error) {
      console.error('Error loading model performance data:', error);
    }
    setLoading(false);
  };

  // Calculate global model accuracy
  const calculateModelAccuracy = () => {
    const correctedAnalyses = analyses.filter(a => a.corrected_label);
    if (correctedAnalyses.length === 0) return null;

    const correctPredictions = correctedAnalyses.filter(a =>
      a.predicted_label === a.corrected_label
    ).length;

    return Math.round((correctPredictions / correctedAnalyses.length) * 100);
  };

  const modelAccuracy = calculateModelAccuracy();

  if (loading) {
    return <div className="loading">Laden...</div>;
  }

  return (
    <div className="model-performance-tab">
      <h2>🤖 Model Prestaties Dashboard</h2>
      <p style={{color: '#666', marginBottom: '20px'}}>
        Overzicht van alle analyses en model prestaties voor alle werkplekken
      </p>

      {/* Global Statistics Dashboard */}
      {statistics && (
        <div className="stats-dashboard">
          <div className="stat-card">
            <div className="stat-icon">📊</div>
            <div className="stat-content">
              <div className="stat-label">Totaal Analyses</div>
              <div className="stat-value">{statistics.total}</div>
              <small>Alle werkplekken</small>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">✅</div>
            <div className="stat-content">
              <div className="stat-label">Beoordeeld</div>
              <div className="stat-value">{statistics.reviewed}</div>
              <small>Analyses met correctie</small>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">⏳</div>
            <div className="stat-content">
              <div className="stat-label">Nog te beoordelen</div>
              <div className="stat-value">{statistics.unreviewed}</div>
              <small>Analyses zonder beoordeling</small>
            </div>
          </div>

          {modelAccuracy !== null && (
            <div className="stat-card accuracy-card">
              <div className="stat-icon">🎯</div>
              <div className="stat-content">
                <div className="stat-label">Model Accuraatheid</div>
                <div className="stat-value">{modelAccuracy}%</div>
                <small>Globale nauwkeurigheid</small>
              </div>
            </div>
          )}

          <div className="stat-card">
            <div className="stat-icon">✔️</div>
            <div className="stat-content">
              <div className="stat-label">OK Status</div>
              <div className="stat-value">{statistics.ok}</div>
              <small>Goedgekeurde analyses</small>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">❌</div>
            <div className="stat-content">
              <div className="stat-label">NOK Status</div>
              <div className="stat-value">{statistics.nok}</div>
              <small>Afgekeurde analyses</small>
            </div>
          </div>
        </div>
      )}

      {/* Workplace Breakdown */}
      {workplaces && workplaces.length > 0 && (
        <div style={{marginTop: '30px'}}>
          <h3>📍 Per Werkplek Overzicht</h3>
          <div className="workplace-stats">
            {workplaces.map(workplace => {
              const wpAnalyses = analyses.filter(a => a.workplace_id === workplace.id);
              const wpReviewed = wpAnalyses.filter(a => a.corrected_label).length;
              const wpOK = wpAnalyses.filter(a => a.corrected_label === 'OK').length;
              const wpNOK = wpAnalyses.filter(a => a.corrected_label && a.corrected_label !== 'OK').length;

              return (
                <div key={workplace.id} className="workplace-stat-card" style={{
                  padding: '15px',
                  marginBottom: '10px',
                  background: '#f8f9fa',
                  borderRadius: '8px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div>
                    <strong>{workplace.name}</strong>
                    <div style={{fontSize: '12px', color: '#666', marginTop: '5px'}}>
                      Items: {workplace.items ? workplace.items.join(', ') : 'Geen items'}
                    </div>
                  </div>
                  <div style={{display: 'flex', gap: '20px'}}>
                    <div style={{textAlign: 'center'}}>
                      <div style={{fontSize: '20px', fontWeight: 'bold'}}>{wpAnalyses.length}</div>
                      <div style={{fontSize: '11px', color: '#666'}}>Totaal</div>
                    </div>
                    <div style={{textAlign: 'center'}}>
                      <div style={{fontSize: '20px', fontWeight: 'bold', color: '#48bb78'}}>{wpReviewed}</div>
                      <div style={{fontSize: '11px', color: '#666'}}>Beoordeeld</div>
                    </div>
                    <div style={{textAlign: 'center'}}>
                      <div style={{fontSize: '20px', fontWeight: 'bold', color: '#4299e1'}}>{wpOK}</div>
                      <div style={{fontSize: '11px', color: '#666'}}>OK</div>
                    </div>
                    <div style={{textAlign: 'center'}}>
                      <div style={{fontSize: '20px', fontWeight: 'bold', color: '#f56565'}}>{wpNOK}</div>
                      <div style={{fontSize: '11px', color: '#666'}}>NOK</div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default Admin;
