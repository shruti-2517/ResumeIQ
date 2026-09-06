import React from 'react';
import './AuthenticityDiff.css';

export default function AuthenticityDiff({ authenticity }) {
  if (!authenticity) return null;

  const {
    authenticity_score = 100,
    hallucination_warnings = [],
    unverified_claims = [],
    verified_metrics = [],
  } = authenticity;

  const scoreColor = authenticity_score >= 80 ? '#10b981' : (authenticity_score >= 60 ? '#f59e0b' : '#ef4444');

  return (
    <div className="authenticity-diff-card card">
      <div className="auth-header">
        <h3 className="label">AI Authenticity & Verification Guardrail</h3>
        <div className="auth-score-badge" style={{ borderColor: scoreColor, color: scoreColor }}>
          Authenticity: {authenticity_score}%
        </div>
      </div>

      {hallucination_warnings.length > 0 && (
        <div className="auth-section">
          <p className="auth-title title--warning">⚠️ Flagged Metric/Skill Hallucinations ({hallucination_warnings.length})</p>
          <div className="auth-list">
            {hallucination_warnings.map((w, idx) => (
              <div key={idx} className="auth-item item--warning">
                <span className="auth-bullet">🚩</span>
                <span>{typeof w === 'string' ? w : (w.claim || w.message)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {unverified_claims.length > 0 && (
        <div className="auth-section">
          <p className="auth-title title--unverified">🟡 Unverified Claims ({unverified_claims.length})</p>
          <div className="auth-list">
            {unverified_claims.map((c, idx) => (
              <div key={idx} className="auth-item item--unverified">
                <span className="auth-bullet">❓</span>
                <span>{typeof c === 'string' ? c : (c.claim || c.message)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {verified_metrics.length > 0 && (
        <div className="auth-section">
          <p className="auth-title title--verified">🟢 Verified Original Claims ({verified_metrics.length})</p>
          <div className="auth-list">
            {verified_metrics.map((v, idx) => (
              <div key={idx} className="auth-item item--verified">
                <span className="auth-bullet">✓</span>
                <span>{typeof v === 'string' ? v : (v.claim || v.message)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
