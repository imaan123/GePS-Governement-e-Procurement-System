import React from 'react';
import { useApp } from '../context/AppContext';

const STEPS = [
  { id: 0, label: 'Home' },
  { id: 1, label: 'Tender' },
  { id: 2, label: 'Bidders' },
  { id: 3, label: 'Processing' },
  { id: 4, label: 'Results' },
  { id: 5, label: 'Review' },
  { id: 6, label: 'Feedback' },
];

const navStyle = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  zIndex: 100,
  background: '#eef2ff',
  backdropFilter: 'none',
  borderBottom: '1px solid #e2e8f0',
  display: 'flex',
  alignItems: 'center',
  padding: '0 32px',
  height: '64px',
  gap: '0',
  boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
};

const logoStyle = {
  fontFamily: 'var(--font-display)',
  fontSize: '22px',
  fontWeight: 800,
  color: '#1e40af',
  letterSpacing: '-0.02em',
  display: 'flex',
  alignItems: 'center',
  gap: '10px',
  marginRight: '48px',
  textDecoration: 'none',
  cursor: 'pointer',
};

const stepsStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '4px',
  flex: 1,
};

export default function Navbar() {
  const { currentStep, setCurrentStep, resetAll, tenderFile, bidderDocs, evaluationResults } = useApp();

  const canNavigate = (stepId) => {
    if (stepId === 0) return true;
    if (stepId === 1) return true;
    
    if (stepId === 2) {
      return !!tenderFile;
    }
    
    if (stepId === 3) {
      return !!(tenderFile && Object.keys(bidderDocs).length > 0);
    }
    
    if (stepId === 4 || stepId === 5) {
      return !!evaluationResults;
    }
    
    if (stepId === 6) {
      return true;
    }
    
    return true;
  };

  const getWarningMessage = (stepId) => {
    if (stepId === 2 && !tenderFile) {
      return '⚠️ Please upload a tender document first before adding bidders.';
    }
    if (stepId === 3 && !tenderFile) {
      return '⚠️ Please upload a tender document first.';
    }
    if (stepId === 3 && Object.keys(bidderDocs).length === 0) {
      return '⚠️ Please add at least one bidder with documents before processing.';
    }
    if ((stepId === 4 || stepId === 5) && !evaluationResults) {
      return '⚠️ Please complete the evaluation first. Go to Processing page.';
    }
    return null;
  };

  const handleNavigation = (stepId) => {
    if (canNavigate(stepId)) {
      setCurrentStep(stepId);
    } else {
      const warning = getWarningMessage(stepId);
      if (warning) {
        alert(warning);
      }
    }
  };

  return (
    <nav style={navStyle}>
      {/* Logo */}
      <div style={logoStyle} onClick={() => handleNavigation(0)}>
        <div style={{
          width: 36, height: 36,
          background: 'linear-gradient(135deg, #1e40af, #3b82f6)',
          borderRadius: 10,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 16, fontWeight: 800, color: '#fff',
          boxShadow: '0 2px 8px rgba(30,64,175,0.3)'
        }}>G</div>
        <span>GePS</span>
      </div>

      {/* Step breadcrumbs */}
      <div style={stepsStyle}>
        {STEPS.filter(s => s.id > 0).map((step, i) => {
          const isActive = currentStep === step.id;
          const isDone = currentStep > step.id;
          const isClickable = canNavigate(step.id);
          
          return (
            <React.Fragment key={step.id}>
              {i > 0 && (
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" style={{ flexShrink: 0 }}>
                  <path d="M6 4l4 4-4 4" stroke={isDone ? '#3b82f6' : '#cbd5e1'} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
              <button
                onClick={() => isClickable && handleNavigation(step.id)}
                disabled={!isClickable}
                style={{
                  background: isActive ? '#eff6ff' : 'none',
                  border: 'none',
                  cursor: isClickable ? 'pointer' : 'not-allowed',
                  padding: '6px 12px',
                  borderRadius: 8,
                  fontFamily: 'var(--font-body)',
                  fontSize: 14,
                  fontWeight: isActive ? 600 : 500,
                  color: '#000000', // Always black for visibility
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  whiteSpace: 'nowrap',
                  position: 'relative',
                }}
              >
                {/* Checkmark for completed stages */}
                {isDone && (
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <circle cx="8" cy="8" r="6" fill="#10b981" opacity="0.15"/>
                    <path d="M5 8L7.5 10.5L11 5.5" stroke="#10b981" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                )}
                
                {/* Step label */}
                <span>{step.label}</span>
                
                {/* Lock icon for inaccessible stages */}
                {!isClickable && step.id !== 1 && (
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" style={{ marginLeft: 2 }}>
                    <path d="M3.5 5V3.5C3.5 2.5 4.5 1.5 6 1.5C7.5 1.5 8.5 2.5 8.5 3.5V5M9 5H3V10H9V5Z" stroke="#94a3b8" strokeWidth="1" fill="none"/>
                  </svg>
                )}
                
                {/* Active indicator underline */}
                {isActive && (
                  <div style={{
                    position: 'absolute',
                    bottom: '-2px',
                    left: '12px',
                    right: '12px',
                    height: '2px',
                    background: '#3b82f6',
                    borderRadius: '2px',
                  }} />
                )}
              </button>
            </React.Fragment>
          );
        })}
      </div>

      {/* Right section */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{
          padding: '4px 14px',
          borderRadius: 100,
          background: '#f0fdf4',
          border: '1px solid #bbf7d0',
          fontSize: 12,
          fontFamily: 'var(--font-mono)',
          color: '#166534',
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          fontWeight: 500,
        }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#22c55e', display: 'inline-block' }} />
          CRPF Procurement
        </div>
        {currentStep > 0 && (
          <button
            onClick={() => {
              if (window.confirm('⚠️ This will reset all progress. Are you sure you want to start a new evaluation?')) {
                resetAll();
              }
            }}
            style={{
              background: '#fef2f2',
              border: '1px solid #fecaca',
              color: '#dc2626',
              borderRadius: 8,
              padding: '6px 16px',
              fontSize: 12,
              cursor: 'pointer',
              fontFamily: 'var(--font-body)',
              transition: 'all 0.15s',
              fontWeight: 500,
            }}
            onMouseEnter={e => { e.target.style.background = '#fee2e2'; e.target.style.borderColor = '#fca5a5'; }}
            onMouseLeave={e => { e.target.style.background = '#fef2f2'; e.target.style.borderColor = '#fecaca'; }}
          >
            New Evaluation
          </button>
        )}
      </div>
    </nav>
  );
}