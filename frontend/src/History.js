import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './History.css';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, ArcElement, LineElement, PointElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar, Pie, Line } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, LineElement, PointElement, Title, Tooltip, Legend);

// API URL - Backend draait op HTTPS
const API_URL = window.location.hostname === 'localhost'
  ? 'https://localhost:8000'
  : `https://${window.location.hostname}:8000`;

function History({ onBack }) {
  const [analyses, setAnalyses] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [trainingStats, setTrainingStats] = useState(null);
  const [trainingCandidates, setTrainingCandidates] = useState([]);
  const [selectedCandidates, setSelectedCandidates] = useState([]);
  const [activeTab, setActiveTab] = useState('review'); // 'review', 'production', 'model', 'training'
  const [filter, setFilter] = useState('all'); // all, OK, NOK
  const [loading, setLoading] = useState(true);
  const [correctingId, setCorrectingId] = useState(null);
  const [confidenceThreshold, setConfidenceThreshold] = useState(70); // Drempelwaarde voor lage zekerheid (%)
  const [itemsMissing, setItemsMissing] = useState({
    hamer: false,
    schaar: false,
    sleutel: false
  });

  // Bepaal de juiste categorie op basis van ONTBREKENDE items
  const determineCategory = (missing) => {
    const { hamer, schaar, sleutel } = missing;

    // Niets ontbreekt = OK
    if (!hamer && !schaar && !sleutel) {
      return { class: '0', label: 'OK' };
    }

    // Alles ontbreekt
    if (hamer && schaar && sleutel) {
      return { class: '1', label: 'NOK-alles_weg' };
    }

    // Alleen hamer ontbreekt
    if (hamer && !schaar && !sleutel) {
      return { class: '2', label: 'NOK-hamer_weg' };
    }

    // Alleen schaar ontbreekt
    if (!hamer && schaar && !sleutel) {
      return { class: '3', label: 'NOK-schaar_weg' };
    }

    // Alleen sleutel ontbreekt
    if (!hamer && !schaar && sleutel) {
      return { class: '5', label: 'NOK-sleutel_weg' };
    }

    // Schaar en sleutel ontbreken (alleen hamer aanwezig)
    if (!hamer && schaar && sleutel) {
      return { class: '4', label: 'NOK-schaar_sleutel_weg' };
    }

    // Hamer en schaar ontbreken (alleen sleutel aanwezig)
    if (hamer && schaar && !sleutel) {
      return { class: '6', label: 'NOK-alleen_sleutel' };
    }

    // Hamer en sleutel ontbreken (alleen schaar aanwezig) - edge case
    if (hamer && !schaar && sleutel) {
      return { class: '4', label: 'NOK-schaar_sleutel_weg' };
    }

    // Default naar OK als we hier komen
    return { class: '0', label: 'OK' };
  };

  const startCorrecting = (analysisId) => {
    setCorrectingId(analysisId);
    // Reset items naar niets ontbreekt
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
    loadHistory();
    loadTimeline();
    loadTrainingStats();
  }, [filter]);

  useEffect(() => {
    if (activeTab === 'model') {
      loadTrainingCandidates();
    }
  }, [activeTab, confidenceThreshold]); // Herlaad ook bij threshold change

  const loadHistory = async () => {
    setLoading(true);
    try {
      const filterParam = filter !== 'all' ? `?status=${filter}` : '';
      const response = await axios.get(`${API_URL}/api/history${filterParam}`);
      setAnalyses(response.data.analyses);
      setStatistics(response.data.statistics);
    } catch (error) {
      console.error('Error loading history:', error);
      alert('Fout bij laden geschiedenis: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const loadTimeline = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/accuracy-timeline`);
      setTimeline(response.data.timeline || []);
    } catch (error) {
      console.error('Error loading timeline:', error);
    }
  };

  const loadTrainingStats = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/training/statistics`);
      setTrainingStats(response.data.statistics);
    } catch (error) {
      console.error('Error loading training stats:', error);
    }
  };

  const loadTrainingCandidates = async () => {
    try {
      // Stuur confidence threshold mee als query parameter
      const response = await axios.get(`${API_URL}/api/training/candidates`, {
        params: { confidence_threshold: confidenceThreshold }
      });
      setTrainingCandidates(response.data.candidates);
    } catch (error) {
      console.error('Error loading training candidates:', error);
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

      // Reset selectie en reload data
      setSelectedCandidates([]);
      loadTrainingCandidates();
      loadTrainingStats();
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
    if (!window.confirm('Weet je zeker dat je deze analyse wilt verwijderen? Dit kan niet ongedaan gemaakt worden.')) {
      return;
    }

    try {
      await axios.delete(`${API_URL}/api/analysis/${analysisId}`);
      alert('✓ Analyse verwijderd');

      // Reload data
      loadHistory();
      loadTrainingCandidates();
      loadTrainingStats();

      // Remove from selection if selected
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

    if (!window.confirm(`Weet je zeker dat je ${selectedCandidates.length} analyses wilt verwijderen? Dit kan niet ongedaan gemaakt worden.`)) {
      return;
    }

    try {
      // Verwijder alle geselecteerde analyses
      await Promise.all(
        selectedCandidates.map(id => axios.delete(`${API_URL}/api/analysis/${id}`))
      );

      alert(`✓ ${selectedCandidates.length} analyses verwijderd`);

      // Reset selectie en reload data
      setSelectedCandidates([]);
      loadHistory();
      loadTrainingCandidates();
      loadTrainingStats();
    } catch (error) {
      console.error('Error deleting analyses:', error);
      alert('Fout bij verwijderen: ' + error.message);
    }
  };

  const downloadCSV = async () => {
    try {
      window.open(`${API_URL}/api/export/csv`, '_blank');
    } catch (error) {
      alert('Fout bij downloaden CSV: ' + error.message);
    }
  };

  const correctAnalysis = async (analysisId, correctedClass, correctedLabel) => {
    try {
      await axios.post(`${API_URL}/api/correct/${analysisId}`, {
        corrected_class: correctedClass,
        corrected_label: correctedLabel,
        notes: "",
        confidence_threshold: confidenceThreshold // Stuur dynamische drempel mee
      });

      alert(`✓ Analyse gecorrigeerd naar: ${correctedLabel}`);
      setCorrectingId(null);
      loadHistory();
      loadTimeline(); // Reload timeline na correctie
      loadTrainingCandidates(); // Reload training candidates
      loadTrainingStats(); // Reload training statistics
    } catch (error) {
      console.error('Error correcting analysis:', error);
      alert('Fout bij opslaan correctie: ' + error.message);
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

  const prepareChartData = () => {
    if (!analyses || analyses.length === 0) return null;

    // Model Performance: bereken hoeveel AI goed/fout heeft
    const correctedAnalyses = analyses.filter(a => a.corrected_label);
    const correctPredictions = correctedAnalyses.filter(a => {
      return a.predicted_label === a.corrected_label;
    }).length;
    const incorrectPredictions = correctedAnalyses.length - correctPredictions;

    const accuracyData = {
      labels: ['Correct voorspeld', 'Fout voorspeld'],
      datasets: [{
        data: [correctPredictions, incorrectPredictions],
        backgroundColor: ['#48bb78', '#f56565'],
        borderColor: ['#fff', '#fff'],
        borderWidth: 2
      }]
    };

    // OK vs NOK pie chart
    const okCount = analyses.filter(a => a.status === 'OK').length;
    const nokCount = analyses.filter(a => a.status === 'NOK').length;

    const pieData = {
      labels: ['OK', 'NOK'],
      datasets: [{
        data: [okCount, nokCount],
        backgroundColor: ['#48bb78', '#f56565'],
        borderColor: ['#fff', '#fff'],
        borderWidth: 2
      }]
    };

    // NOK situaties bar chart
    const nokAnalyses = analyses.filter(a => a.status === 'NOK');
    const nokCounts = {};
    nokAnalyses.forEach(a => {
      nokCounts[a.predicted_label] = (nokCounts[a.predicted_label] || 0) + 1;
    });

    const barData = {
      labels: Object.keys(nokCounts),
      datasets: [{
        label: 'Aantal keer',
        data: Object.values(nokCounts),
        backgroundColor: '#f56565',
        borderColor: '#c53030',
        borderWidth: 1
      }]
    };

    // Timeline chart data
    const timelineData = timeline.length > 0 ? {
      labels: timeline.map(t => t.week.replace('W', ' Week ')),
      datasets: [{
        label: 'Model Accuracy (%)',
        data: timeline.map(t => t.accuracy),
        borderColor: '#667eea',
        backgroundColor: 'rgba(102, 126, 234, 0.1)',
        borderWidth: 3,
        tension: 0.4,
        fill: true,
        pointRadius: 5,
        pointHoverRadius: 7,
        pointBackgroundColor: '#667eea',
        pointBorderColor: '#fff',
        pointBorderWidth: 2
      }]
    } : null;

    return {
      accuracyData,
      pieData,
      barData,
      timelineData,
      modelAccuracy: correctedAnalyses.length > 0
        ? Math.round((correctPredictions / correctedAnalyses.length) * 100)
        : null
    };
  };

  const chartData = prepareChartData();

  if (loading) {
    return (
      <div className="history-container">
        <div className="loading">Laden...</div>
      </div>
    );
  }

  return (
    <div className="history-container">
      {/* Header */}
      <div className="history-header">
        <button onClick={onBack} className="back-button">
          ← Terug naar Inspectie
        </button>
        <h1>📊 Analyse Dashboard</h1>
      </div>

      {/* Tab Navigation - 2 TABS */}
      <div className="tab-navigation">
        <button
          className={`tab-btn ${activeTab === 'review' ? 'active' : ''}`}
          onClick={() => setActiveTab('review')}
        >
          ✏️ Beoordelings Analyse
        </button>
        <button
          className={`tab-btn ${activeTab === 'model' ? 'active' : ''}`}
          onClick={() => setActiveTab('model')}
        >
          🤖 Model Prestaties
        </button>
      </div>

      {/* ========================================
          TAB 1: BEOORDELINGS ANALYSE - Review en correctie functie
          ======================================== */}
      {activeTab === 'review' && (
        <div className="tab-content">
          {/* Statistics Dashboard */}
          {statistics && (() => {
            // Bereken statistieken
            const unreviewedCount = analyses.filter(a => !a.corrected_label).length;
            const reviewedCount = statistics.corrections_count || 0;

            return (
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
                    <div className="stat-value">{statistics.total_analyses}</div>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-icon">🎯</div>
                  <div className="stat-content">
                    <div className="stat-label">Voortgang</div>
                    <div className="stat-value">
                      {statistics.total_analyses > 0
                        ? Math.round((reviewedCount / statistics.total_analyses) * 100)
                        : 0}%
                    </div>
                  </div>
                </div>
              </div>
            );
          })()}

          {/* Filters and Actions */}
          <div className="history-controls">
            <div className="filter-buttons">
              <button
                className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
                onClick={() => setFilter('all')}
              >
                Alles ({statistics?.total_analyses || 0})
              </button>
              <button
                className={`filter-btn ${filter === 'OK' ? 'active' : ''}`}
                onClick={() => setFilter('OK')}
              >
                OK ({statistics?.ok_count || 0})
              </button>
              <button
                className={`filter-btn ${filter === 'NOK' ? 'active' : ''}`}
                onClick={() => setFilter('NOK')}
              >
                NOK ({statistics?.nok_count || 0})
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

          {/* Analyses Grid */}
          <div className="analyses-grid">
            {analyses.length === 0 ? (
              <div className="empty-state">
                <p>Geen analyses gevonden</p>
                <p className="empty-hint">Start met foto's analyseren om hier resultaten te zien</p>
              </div>
            ) : (
              analyses
                .filter(analysis => {
                  // Toon ALLEEN analyses die nog NIET beoordeeld zijn
                  // Na beoordeling verdwijnen ze uit deze lijst
                  return !analysis.corrected_label;
                })
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

                      {analysis.camera_info && (
                        <>
                          {analysis.camera_info.resolution_width && analysis.camera_info.resolution_height && (
                            <div className="meta-item">
                              <span className="meta-label">📷 Resolutie:</span>
                              <span className="meta-value">
                                {analysis.camera_info.resolution_width}x{analysis.camera_info.resolution_height}
                              </span>
                            </div>
                          )}
                          {analysis.camera_info.file_size_kb && (
                            <div className="meta-item">
                              <span className="meta-label">💾 Grootte:</span>
                              <span className="meta-value">{analysis.camera_info.file_size_kb} KB</span>
                            </div>
                          )}
                          {analysis.camera_info.camera_facing && (
                            <div className="meta-item">
                              <span className="meta-label">🎥 Camera:</span>
                              <span className="meta-value">
                                {analysis.camera_info.camera_facing === 'environment' ? 'Achterkant' : 'Webcam'}
                              </span>
                            </div>
                          )}
                        </>
                      )}

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
        </div>
      )}

      {/* ========================================
          TAB 2: MODEL PRESTATIES - ML Pipeline Management
          ======================================== */}
      {activeTab === 'model' && (
        <div className="tab-content">
          {/* Model Version & Stats Dashboard */}
          <div className="model-header">
            <div className="model-version-card">
              <h2>🤖 Model Versie 1.0</h2>
              <p className="model-date">Training datum: {new Date().toLocaleDateString('nl-NL')}</p>
            </div>
          </div>

          {/* Training Pipeline Stats */}
          {trainingStats && (
            <div className="stats-dashboard">
              <div className="stat-card">
                <div className="stat-icon">📊</div>
                <div className="stat-content">
                  <div className="stat-label">Totaal Beoordeeld</div>
                  <div className="stat-value">{analyses.filter(a => a.corrected_label).length}</div>
                </div>
              </div>

              {chartData && chartData.modelAccuracy !== null && (
                <div className="stat-card accuracy-card">
                  <div className="stat-icon">🎯</div>
                  <div className="stat-content">
                    <div className="stat-label">Model Accuraatheid</div>
                    <div className="stat-value">{chartData.modelAccuracy}%</div>
                  </div>
                </div>
              )}

              <div className="stat-card">
                <div className="stat-icon">⏳</div>
                <div className="stat-content">
                  <div className="stat-label">Nog te checken</div>
                  <div className="stat-value">{trainingStats.unreviewed_count}</div>
                  <small>Analyses zonder beoordeling</small>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon">📦</div>
                <div className="stat-content">
                  <div className="stat-label">Training Queue</div>
                  <div className="stat-value">{trainingStats.training_queue_count}/{trainingStats.training_target}</div>
                  <small>{trainingStats.training_progress_percent}% van doel</small>
                </div>
              </div>
            </div>
          )}

          {/* Training Progress Bar */}
          {trainingStats && (
            <div className="training-progress-section">
              <h3>🎯 Training Data Collectie</h3>
              <div className="progress-bar-container">
                <div
                  className="progress-bar-fill"
                  style={{width: `${trainingStats.training_progress_percent}%`}}
                >
                  {trainingStats.training_progress_percent}%
                </div>
              </div>
              <p className="progress-info">
                {trainingStats.training_queue_count} van {trainingStats.training_target} training samples verzameld
                {trainingStats.training_queue_count >= trainingStats.training_target &&
                  <span style={{color: '#48bb78', fontWeight: 'bold'}}> ✓ Doel bereikt!</span>
                }
              </p>
            </div>
          )}

          {/* Timeline Chart - Model verbetering over tijd */}
          {chartData && chartData.timelineData && timeline.length > 0 && (
            <div className="charts-section">
              <div className="timeline-chart-container">
                <div className="chart-card timeline-card">
                  <h3>📈 Model Prestatie Over Tijd</h3>
                  <div className="chart-container-large">
                    <Line data={chartData.timelineData} options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          display: true,
                          position: 'top'
                        },
                        tooltip: {
                          callbacks: {
                            label: function(context) {
                              return `Accuracy: ${context.parsed.y}%`;
                            },
                            afterLabel: function(context) {
                              const weekData = timeline[context.dataIndex];
                              return `Gebaseerd op ${weekData.total} beoordelingen`;
                            }
                          }
                        }
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                          max: 100,
                          ticks: {
                            callback: function(value) {
                              return value + '%';
                            }
                          },
                          title: {
                            display: true,
                            text: 'Accuracy (%)'
                          }
                        },
                        x: {
                          title: {
                            display: true,
                            text: 'Periode'
                          }
                        }
                      }
                    }} />
                  </div>
                  <div className="timeline-info">
                    <p>
                      📊 Deze grafiek toont hoe accuraat het AI model voorspellingen doet over tijd.
                      Een stijgende lijn betekent dat het model beter wordt!
                    </p>
                    {timeline.length >= 2 && (
                      <p className="trend-indicator">
                        {timeline[timeline.length - 1].accuracy > timeline[0].accuracy ? (
                          <span style={{color: '#48bb78', fontWeight: 'bold'}}>
                            ↗️ Model verbetert: {(timeline[timeline.length - 1].accuracy - timeline[0].accuracy).toFixed(1)}% stijging
                          </span>
                        ) : timeline[timeline.length - 1].accuracy < timeline[0].accuracy ? (
                          <span style={{color: '#f56565', fontWeight: 'bold'}}>
                            ↘️ Model verslechtert: {(timeline[0].accuracy - timeline[timeline.length - 1].accuracy).toFixed(1)}% daling
                          </span>
                        ) : (
                          <span style={{color: '#718096', fontWeight: 'bold'}}>
                            → Model stabiel
                          </span>
                        )}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Training Selector */}
          <div className="training-selector-section">
            <div className="section-header">
              <h3>🎓 Training Selector</h3>
              <p className="section-description">
                Selecteer analyses voor model retraining. Dit zijn automatisch gedetecteerde candidates:
                foutieve voorspellingen of lage zekerheid (&lt;70%)
              </p>
              <div className="selector-actions">
                <button onClick={selectAllCandidates} className="select-all-btn">
                  {selectedCandidates.length === trainingCandidates.length ? '⬜ Deselecteer alles' : '☑️ Selecteer alles'}
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
                  Training candidates worden automatisch gedetecteerd wanneer analyses fout voorspeld zijn of lage zekerheid hebben
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
                        onChange={() => {}}
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
                        onError={(e) => {
                          e.target.src = 'https://via.placeholder.com/150?text=Foto+niet+gevonden';
                        }}
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
      )}
    </div>
  );
}

export default History;
