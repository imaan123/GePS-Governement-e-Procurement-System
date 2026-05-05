import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { motion } from 'framer-motion';
import { CheckCircle, XCircle, AlertCircle, ChevronDown, ChevronUp, FileText, Play } from 'lucide-react';
import { MOCK_EVALUATION_RESULTS } from '../services/api';

const ResultsPage = () => {
  const { evaluationResults, setCurrentStep, bidderDocs, tenderFile } = useApp();
  const [expandedBidder, setExpandedBidder] = useState(null);

  const hasRealEvaluationData = evaluationResults !== null;
  const hasRealData = tenderFile !== null || Object.keys(bidderDocs).length > 0;
  
  // Use real results if available, otherwise use mock data for demo
  const displayResults = hasRealEvaluationData ? evaluationResults : MOCK_EVALUATION_RESULTS;
  const isDemoMode = !hasRealEvaluationData && !hasRealData;

  const getVerdictClass = (verdict) => {
    switch(verdict) {
      case 'ELIGIBLE': return 'badge-pass';
      case 'NOT ELIGIBLE': return 'badge-fail';
      default: return 'badge-review';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      style={{ maxWidth: 1400, margin: '0 auto' }}
    >
      <div style={{ marginBottom: 32 }}>
        {isDemoMode && (
          <div style={{
            display: 'inline-block',
            background: '#f3e8ff',
            color: '#6d28d9',
            padding: '4px 12px',
            borderRadius: 20,
            fontSize: 12,
            marginBottom: 12,
          }}>
            🎬 Demo Mode - Sample Evaluation Results
          </div>
        )}
        <h2 style={{ fontSize: 28, marginBottom: 8, color: '#1e293b' }}>
          {isDemoMode ? '🎬 Demo Evaluation Results' : '✅ Evaluation Results'}
        </h2>
        <p style={{ color: '#64748b' }}>
          {displayResults?.tender_name || 'Tender Evaluation'} • {displayResults?.evaluated_at ? new Date(displayResults.evaluated_at).toLocaleString() : new Date().toLocaleString()}
        </p>
        {isDemoMode && (
          <p style={{ color: '#6d28d9', fontSize: 13, marginTop: 8 }}>
            ℹ️ This is sample data showing how evaluation results appear. Upload real documents to see your actual results.
          </p>
        )}
      </div>

      {/* Summary Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: 20,
        marginBottom: 32,
      }}>
        {displayResults?.bidders?.map((bidder, idx) => (
          <motion.div
            key={bidder.bidder_id || idx}
            whileHover={{ scale: 1.02 }}
            style={{
              background: '#ffffff',
              borderRadius: 16,
              padding: 20,
              border: `1px solid ${bidder.overall_verdict === 'ELIGIBLE' ? '#bbf7d0' : 
                       bidder.overall_verdict === 'NOT ELIGIBLE' ? '#fecaca' : 
                       '#fed7aa'}`,
              boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <div style={{ fontWeight: 600, color: '#1e293b' }}>{bidder.bidder_name}</div>
              <div className={getVerdictClass(bidder.overall_verdict)}>
                {bidder.overall_verdict}
              </div>
            </div>
            <div style={{ fontSize: 13, color: '#64748b', marginBottom: 8 }}>
              Confidence: {(bidder.overall_confidence * 100).toFixed(0)}%
            </div>
            <div style={{ background: '#e2e8f0', borderRadius: 8, height: 4, overflow: 'hidden' }}>
              <div style={{
                width: `${bidder.overall_confidence * 100}%`,
                height: '100%',
                background: bidder.overall_verdict === 'ELIGIBLE' ? '#10b981' : 
                           bidder.overall_verdict === 'NOT ELIGIBLE' ? '#ef4444' : '#f59e0b',
              }} />
            </div>
            <button
              onClick={() => setExpandedBidder(expandedBidder === bidder.bidder_id ? null : bidder.bidder_id)}
              style={{
                marginTop: 16,
                width: '100%',
                background: '#f8fafc',
                border: '1px solid #e2e8f0',
                padding: '8px 16px',
                borderRadius: 8,
                color: '#475569',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
                fontSize: 13,
              }}
            >
              {expandedBidder === bidder.bidder_id ? 'Hide Details' : 'View Details'}
              {expandedBidder === bidder.bidder_id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>
          </motion.div>
        ))}
      </div>

      {/* Expanded Details */}
      {expandedBidder && displayResults?.bidders?.find(b => b.bidder_id === expandedBidder) && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ background: '#ffffff', borderRadius: 20, padding: 24, marginTop: 20, border: '1px solid #e2e8f0' }}
        >
          <h3 style={{ marginBottom: 20, color: '#1e293b' }}>
            {displayResults.bidders.find(b => b.bidder_id === expandedBidder)?.bidder_name} - Detailed Evaluation
          </h3>
          
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #e2e8f0', background: '#f8fafc' }}>
                  <th style={{ padding: 12, textAlign: 'left', color: '#475569' }}>Criterion</th>
                  <th style={{ padding: 12, textAlign: 'left', color: '#475569' }}>Extracted Value</th>
                  <th style={{ padding: 12, textAlign: 'left', color: '#475569' }}>Required</th>
                  <th style={{ padding: 12, textAlign: 'center', color: '#475569' }}>Result</th>
                  <th style={{ padding: 12, textAlign: 'center', color: '#475569' }}>Confidence</th>
                  <th style={{ padding: 12, textAlign: 'left', color: '#475569' }}>Source</th>
                </tr>
              </thead>
              <tbody>
                {displayResults.bidders
                  .find(b => b.bidder_id === expandedBidder)
                  ?.criteria?.map((criterion, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #e2e8f0' }}>
                      <td style={{ padding: 12 }}>
                        <div style={{ fontWeight: 500, color: '#1e293b' }}>{criterion.description}</div>
                        <div style={{ fontSize: 11, color: '#94a3b8' }}>{criterion.rule_id}</div>
                       </td>
                      <td style={{ padding: 12, color: '#475569' }}>{criterion.extracted_value || '—'}</td>
                      <td style={{ padding: 12, color: '#475569' }}>{criterion.threshold}</td>
                      <td style={{ padding: 12, textAlign: 'center' }}>
                        <span className={`badge ${
                          criterion.result === 'PASS' ? 'badge-pass' : 
                          criterion.result === 'FAIL' ? 'badge-fail' : 'badge-review'
                        }`}>
                          {criterion.result}
                        </span>
                      </td>
                      <td style={{ padding: 12, textAlign: 'center', color: '#475569' }}>
                        {(criterion.confidence * 100).toFixed(0)}%
                      </td>
                      <td style={{ padding: 12 }}>
                        {criterion.source_doc && (
                          <div style={{ fontSize: 12, display: 'flex', alignItems: 'center', gap: 4, color: '#64748b' }}>
                            <FileText size={12} />
                            {criterion.source_doc}
                            {criterion.source_page && ` (p.${criterion.source_page})`}
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>

          {displayResults.review_queue?.filter(rq => rq.bidder_id === expandedBidder).length > 0 && (
            <div style={{ marginTop: 24, padding: 16, background: '#fef3c7', borderRadius: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                <AlertCircle size={18} color="#d97706" />
                <strong style={{ color: '#92400e' }}>Items Needing Human Review</strong>
              </div>
              {displayResults.review_queue
                .filter(rq => rq.bidder_id === expandedBidder)
                .map((item, idx) => (
                  <div key={idx} style={{ marginBottom: 12, padding: 12, background: '#ffffff', borderRadius: 8, border: '1px solid #fde68a' }}>
                    <div><strong style={{ color: '#92400e' }}>{item.criterion}</strong></div>
                    <div style={{ fontSize: 13, color: '#92400e', marginTop: 4 }}>{item.evidence}</div>
                    <button
                      onClick={() => setCurrentStep(5)}
                      style={{
                        marginTop: 8,
                        background: '#d97706',
                        border: 'none',
                        padding: '4px 12px',
                        borderRadius: 6,
                        color: '#fff',
                        fontSize: 12,
                        cursor: 'pointer',
                      }}
                    >
                      Review Now →
                    </button>
                  </div>
                ))}
            </div>
          )}
        </motion.div>
      )}

      {/* Action Buttons for Demo Mode */}
      {isDemoMode && (
        <div style={{ display: 'flex', gap: 16, justifyContent: 'center', marginTop: 32 }}>
          <button
            onClick={() => setCurrentStep(1)}
            style={{
              background: 'linear-gradient(135deg, #1e40af, #2563eb)',
              color: '#fff',
              border: 'none',
              padding: '12px 24px',
              borderRadius: 8,
              cursor: 'pointer',
              fontWeight: 500,
            }}
          >
            📄 Upload Real Documents →
          </button>
          <button
            onClick={() => setCurrentStep(3)}
            style={{
              background: '#f3e8ff',
              color: '#6d28d9',
              border: '1px solid #c4b5fd',
              padding: '12px 24px',
              borderRadius: 8,
              cursor: 'pointer',
              fontWeight: 500,
            }}
          >
            🎬 Try Demo Evaluation Again
          </button>
        </div>
      )}
    </motion.div>
  );
};

export default ResultsPage;