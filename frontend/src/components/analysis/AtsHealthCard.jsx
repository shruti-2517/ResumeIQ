import React from 'react';
import './AtsHealthCard.css';

export default function AtsHealthCard({ atsHealth }) {
  if (!atsHealth) return null;

  const { ats_score = 0, readability_level = 'Low', warnings = [], found_sections = [], layout_hazards = [] } = atsHealth;

  const getScoreColor = (score) => {
    if (score >= 80) return '#10b981'; // Green
    if (score >= 60) return '#f59e0b'; // Yellow
    return '#ef4444'; // Red
  };

  const scoreColor = getScoreColor(ats_score);

  return (
    <div className="ats-health-card card">
      <div className="ats-card-header">
        <h3 className="label">ATS Readability Check</h3>
        <span className={`badge badge--${readability_level.toLowerCase()}`}>
          {readability_level} Readability
        </span>
      </div>

      <div className="ats-score-row">
        <div className="ats-gauge" style={{ borderColor: scoreColor, color: scoreColor }}>
          <span className="ats-score-num">{ats_score}</span>
          <span className="ats-score-denom">/100</span>
        </div>
        <div className="ats-sections">
          <p className="ats-sublabel">Detected Sections:</p>
          <div className="section-pills">
            {['Summary', 'Experience', 'Education', 'Skills'].map((section) => {
              const isFound = found_sections.includes(section);
              return (
                <span key={section} className={`section-pill ${isFound ? 'pill--found' : 'pill--missing'}`}>
                  {isFound ? '✓' : '✗'} {section}
                </span>
              );
            })}
          </div>
        </div>
      </div>

      {layout_hazards.length > 0 && (
        <div className="hazards-section">
          <p className="ats-sublabel">Layout Hazards Detected:</p>
          <div className="hazard-badges">
            {layout_hazards.map((hazard, idx) => (
              <span key={idx} className="badge badge--warning">
                ⚠️ {hazard.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </div>
      )}

      {warnings.length > 0 && (
        <div className="warnings-list">
          {warnings.map((w, idx) => (
            <div key={idx} className={`warning-item warning--${(w.severity || 'medium').toLowerCase()}`}>
              <span className="warning-icon">●</span>
              <span className="warning-text">{w.message}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
