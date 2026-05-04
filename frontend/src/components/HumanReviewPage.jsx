import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { motion } from 'framer-motion';
import { CheckCircle, XCircle, AlertCircle, Send } from 'lucide-react';

const HumanReviewPage = () => {
  const { reviewQueue, setReviewQueue, feedbackLog, setFeedbackLog, setCurrentStep } = useApp();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [decision, setDecision] = useState(null);
  const [notes, setNotes] = useState('');
  const [errorType, setErrorType] = useState('');

  const currentItem = reviewQueue[currentIndex];

  const handleSubmit = () => {
    if (!decision) return;

    const feedback = {
      review_id: currentItem.review_id,
      decision,
      notes,
      error_type: errorType,
      timestamp: new Date().toISOString(),
    };
    
    setFeedbackLog([...feedbackLog, feedback]);
    setReviewQueue(reviewQueue.filter((_, i) => i !== currentIndex));
    
    if (currentIndex >= reviewQueue.length - 1) {
      alert('All reviews completed!');
      setCurrentStep(6);
    }
    
    setDecision(null);
    setNotes('');
    setErrorType('');
  };

  if (reviewQueue.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: 64 }}>
        <CheckCircle size={64} color="#10b981" style={{ margin: '0 auto 24px' }} />
        <h2>No Items to Review</h2>
        <p style={{ color: 'var(--text-muted)', marginTop: 8 }}>All evaluations have sufficient confidence.</p>
        <button
          onClick={() => setCurrentStep(6)}
          style={{
            marginTop: 32,
            background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
            border: 'none',
            padding: '10px 24px',
            borderRadius: 8,
            color: '#fff',
            cursor: 'pointer',
          }}
        >
          View Analytics →
        </button>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      style={{ maxWidth: 1000, margin: '0 auto' }}
    >
      <div style={{ marginBottom: 32 }}>
        <h2>Human Review Panel</h2>
        <p style={{ color: 'var(--text-muted)' }}>
          Reviewing {currentIndex + 1} of {reviewQueue.length}
        </p>
      </div>

      <div style={{ background: 'var(--bg-card)', borderRadius: 20, padding: 32, marginBottom: 24 }}>
        <div style={{ marginBottom: 24 }}>
          <div className="badge-review" style={{ display: 'inline-flex', marginBottom: 16 }}>
            Needs Review
          </div>
          <h3 style={{ marginBottom: 12 }}>{currentItem.criterion}</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>{currentItem.evidence}</p>
        </div>

        <div style={{
          padding: 16,
          background: 'var(--bg-elevated)',
          borderRadius: 12,
          marginBottom: 24,
        }}>
          <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 8 }}>Source Document</div>
          <div>{currentItem.source_doc} {currentItem.source_page && `(Page ${currentItem.source_page})`}</div>
        </div>

        <div style={{ marginBottom: 24 }}>
          <div style={{ fontWeight: 500, marginBottom: 12 }}>Your Decision *</div>
          <div style={{ display: 'flex', gap: 12 }}>
            <button
              onClick={() => setDecision('PASS')}
              style={{
                flex: 1,
                padding: 12,
                background: decision === 'PASS' ? 'rgba(16,185,129,0.2)' : 'var(--bg-elevated)',
                border: `1px solid ${decision === 'PASS' ? '#10b981' : 'var(--border-primary)'}`,
                borderRadius: 8,
                color: '#10b981',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
              }}
            >
              <CheckCircle size={18} /> Confirm PASS
            </button>
            <button
              onClick={() => setDecision('FAIL')}
              style={{
                flex: 1,
                padding: 12,
                background: decision === 'FAIL' ? 'rgba(239,68,68,0.2)' : 'var(--bg-elevated)',
                border: `1px solid ${decision === 'FAIL' ? '#ef4444' : 'var(--border-primary)'}`,
                borderRadius: 8,
                color: '#ef4444',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
              }}
            >
              <XCircle size={18} /> Override FAIL
            </button>
          </div>
        </div>

        {decision && decision !== 'PASS' && (
          <div style={{ marginBottom: 20 }}>
            <select
              value={errorType}
              onChange={(e) => setErrorType(e.target.value)}
              style={{
                width: '100%',
                padding: 12,
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-primary)',
                borderRadius: 8,
                color: 'var(--text-primary)',
              }}
            >
              <option value="">Select error type</option>
              <option value="OCR Error">OCR Error</option>
              <option value="Retrieval Failure">Retrieval Failure</option>
              <option value="Extraction Error">Extraction Error</option>
              <option value="Rule Interpretation Error">Rule Interpretation Error</option>
            </select>
          </div>
        )}

        <textarea
          placeholder="Add justification or notes..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={3}
          style={{
            width: '100%',
            padding: 12,
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-primary)',
            borderRadius: 8,
            color: 'var(--text-primary)',
            resize: 'vertical',
            marginBottom: 20,
          }}
        />

        <button
          onClick={handleSubmit}
          disabled={!decision}
          style={{
            width: '100%',
            padding: 14,
            background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
            border: 'none',
            borderRadius: 12,
            color: '#fff',
            fontWeight: 600,
            cursor: decision ? 'pointer' : 'not-allowed',
            opacity: decision ? 1 : 0.5,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
          }}
        >
          <Send size={18} /> Submit Review
        </button>
      </div>
    </motion.div>
  );
};

export default HumanReviewPage;