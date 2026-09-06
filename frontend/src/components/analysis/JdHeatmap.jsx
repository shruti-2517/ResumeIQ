import React from 'react';
import './JdHeatmap.css';

export default function JdHeatmap({ keywordMatch }) {
  if (!keywordMatch) return null;

  const {
    match_percentage = 0,
    matched_keywords = [],
    missing_keywords = [],
    partial_keywords = [],
  } = keywordMatch;

  return (
    <div className="jd-heatmap-card card">
      <div className="heatmap-header">
        <h3 className="label">Job Description Keyword Heatmap</h3>
        <div className="match-percentage-badge">
          <span>Match: </span>
          <span className="match-num">{match_percentage}%</span>
        </div>
      </div>

      <div className="heatmap-matrix">
        {/* Matched Keywords */}
        <div className="heatmap-group">
          <p className="group-title title--matched">
            🟢 Matched Keywords ({matched_keywords.length})
          </p>
          <div className="keyword-pills">
            {matched_keywords.length > 0 ? (
              matched_keywords.map((kw, idx) => (
                <span key={idx} className="kw-pill kw--matched">
                  {kw}
                </span>
              ))
            ) : (
              <span className="kw-empty">None detected</span>
            )}
          </div>
        </div>

        {/* Missing Keywords */}
        <div className="heatmap-group">
          <p className="group-title title--missing">
            🔴 Missing Critical Keywords ({missing_keywords.length})
          </p>
          <div className="keyword-pills">
            {missing_keywords.length > 0 ? (
              missing_keywords.map((kw, idx) => (
                <span key={idx} className="kw-pill kw--missing">
                  {kw}
                </span>
              ))
            ) : (
              <span className="kw-empty">No missing critical keywords</span>
            )}
          </div>
        </div>

        {/* Partial Keywords */}
        {partial_keywords.length > 0 && (
          <div className="heatmap-group">
            <p className="group-title title--partial">
              🟡 Partial Keywords ({partial_keywords.length})
            </p>
            <div className="keyword-pills">
              {partial_keywords.map((kw, idx) => (
                <span key={idx} className="kw-pill kw--partial">
                  {kw}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
