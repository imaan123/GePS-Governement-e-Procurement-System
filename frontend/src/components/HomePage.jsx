import React from 'react';
import { useApp } from '../context/AppContext';
import { motion } from 'framer-motion';
import { Upload, Users, FileCheck, TrendingUp, Shield, Zap } from 'lucide-react';
import { MOCK_EVALUATION_RESULTS } from '../services/api';

const HomePage = () => {
  const { setCurrentStep, tenderFile, bidderDocs, evaluationResults } = useApp();
  
  // Check if there's REAL data (not mock)
  const hasRealTenderData = tenderFile !== null;
  const hasRealBidderData = Object.keys(bidderDocs).length > 0;
  const hasRealEvaluationData = evaluationResults !== null;
  
  // Check if evaluation results are mock data
  const isShowingMockResults = evaluationResults === MOCK_EVALUATION_RESULTS;
  const isDemoMode = !hasRealTenderData && !hasRealBidderData && !hasRealEvaluationData;
  
  // If evaluation exists but it's mock data, treat as demo for display purposes
  const effectiveIsDemoMode = isDemoMode || (hasRealEvaluationData && isShowingMockResults);

  const canNavigateToStep = (stepId) => {
    switch(stepId) {
      case 1: // Tender upload - always allowed
        return { allowed: true, message: null };
      
      case 2: // Add Bidders - ONLY if real tender exists
        if (!hasRealTenderData) {
          return { allowed: false, message: '⚠️ Please upload a tender document first before adding bidders.' };
        }
        return { allowed: true, message: null };
      
      case 3: // AI Evaluation - ALWAYS allowed (shows demo if no data)
        return { allowed: true, message: null };
      
      case 4: // Results Dashboard - ALWAYS allowed (shows demo if no data)
        return { allowed: true, message: null };
      
      default:
        return { allowed: true, message: null };
    }
  };

  const handleNavigation = (stepId) => {
    const { allowed, message } = canNavigateToStep(stepId);
    if (allowed) {
      setCurrentStep(stepId);
    } else if (message) {
      alert(message);
    }
  };

  const getCardStatus = (stepId) => {
    switch(stepId) {
      case 1:
        if (hasRealTenderData) return { text: '✓ Tender Uploaded', color: '#059669', bg: '#f0fdf4' };
        return { text: '📄 Ready to upload', color: '#3b82f6', bg: '#eff6ff' };
      
      case 2:
        if (hasRealBidderData) return { text: `✓ ${Object.keys(bidderDocs).length} Bidder(s) Added`, color: '#059669', bg: '#f0fdf4' };
        if (hasRealTenderData) return { text: '👥 Ready to add bidders', color: '#3b82f6', bg: '#eff6ff' };
        return { text: '🔒 Upload tender first', color: '#94a3b8', bg: '#f1f5f9' };
      
      case 3:
        if (hasRealEvaluationData && !isShowingMockResults) return { text: '✓ Evaluation Complete', color: '#059669', bg: '#f0fdf4' };
        if (effectiveIsDemoMode) return { text: '🎬 Try Demo Evaluation', color: '#8b5cf6', bg: '#f3e8ff' };
        if (hasRealBidderData || hasRealTenderData) return { text: '🚀 Ready to Evaluate', color: '#d97706', bg: '#fef3c7' };
        return { text: '🎬 Try Demo Evaluation', color: '#8b5cf6', bg: '#f3e8ff' };
      
      case 4:
        if (hasRealEvaluationData && !isShowingMockResults) return { text: '📊 View Results', color: '#7c3aed', bg: '#f3e8ff' };
        if (effectiveIsDemoMode) return { text: '🎬 View Demo Results', color: '#8b5cf6', bg: '#f3e8ff' };
        if (hasRealBidderData || hasRealTenderData) return { text: '⚡ Run evaluation first', color: '#94a3b8', bg: '#f1f5f9' };
        return { text: '🎬 View Demo Results', color: '#8b5cf6', bg: '#f3e8ff' };
      
      default:
        return null;
    }
  };

  const features = [
    { icon: Upload, title: 'Upload Tender', description: 'Upload tender documents for AI-powered criteria extraction', color: '#1e40af', step: 1 },
    { icon: Users, title: 'Add Bidders', description: 'Upload bidder documents for evaluation', color: '#059669', step: 2 },
    { icon: FileCheck, title: 'AI Evaluation', description: 'Automated eligibility checking with confidence scoring', color: '#d97706', step: 3 },
    { icon: TrendingUp, title: 'Results Dashboard', description: 'View detailed evaluation results and analytics', color: '#7c3aed', step: 4 },
  ];

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto' }}>
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ textAlign: 'center', marginBottom: 64 }}
      >
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 8,
          background: '#eff6ff',
          padding: '6px 16px',
          borderRadius: 100,
          marginBottom: 24,
          border: '1px solid #bfdbfe',
        }}>
          <Zap size={16} color="#2563eb" />
          <span style={{ fontSize: 13, fontFamily: 'var(--font-mono)', color: '#1e40af' }}>
            AI-Powered Government Procurement System
          </span>
        </div>

        <h1 style={{
          fontSize: 'clamp(2rem, 5vw, 3.5rem)',
          fontWeight: 800,
          marginBottom: 16,
          color: '#1e293b',
        }}>
          Government e-Procurement System
        </h1>

        <p style={{
          fontSize: 18,
          color: '#475569',
          maxWidth: 600,
          margin: '0 auto 24px',
        }}>
          AI-based tender evaluation and eligibility analysis for CRPF procurement
        </p>

        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => handleNavigation(1)}
          style={{
            background: 'linear-gradient(135deg, #1e40af, #2563eb)',
            border: 'none',
            padding: '14px 36px',
            borderRadius: 40,
            color: '#fff',
            fontSize: 16,
            fontWeight: 600,
            cursor: 'pointer',
            fontFamily: 'var(--font-body)',
            boxShadow: '0 2px 8px rgba(30,64,175,0.3)',
          }}
        >
          Start New Evaluation →
        </motion.button>
      </motion.div>

      {/* Features Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: 24,
        marginBottom: 64,
      }}>
        {features.map((feature, idx) => {
          const { allowed } = canNavigateToStep(feature.step);
          const status = getCardStatus(feature.step);
          const isDemoCard = status?.text?.includes('Demo');
          
          return (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              onClick={() => handleNavigation(feature.step)}
              style={{
                background: '#ffffff',
                borderRadius: 20,
                padding: 28,
                cursor: allowed ? 'pointer' : 'not-allowed',
                border: `1px solid ${isDemoCard ? '#c4b5fd' : '#e2e8f0'}`,
                transition: 'all 0.3s',
                boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                opacity: allowed ? 1 : 0.6,
                position: 'relative',
              }}
              whileHover={allowed ? {
                scale: 1.03,
                borderColor: isDemoCard ? '#8b5cf6' : feature.color,
                boxShadow: `0 8px 25px ${isDemoCard ? '#8b5cf6' : feature.color}15`,
              } : {}}
            >
              <div style={{
                width: 56,
                height: 56,
                borderRadius: 16,
                background: isDemoCard ? '#f3e8ff' : `${feature.color}10`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: 20,
              }}>
                <feature.icon size={28} color={isDemoCard ? '#8b5cf6' : feature.color} />
              </div>
              <h3 style={{ marginBottom: 12, fontSize: 20, color: '#1e293b' }}>{feature.title}</h3>
              <p style={{ color: '#64748b', fontSize: 14, marginBottom: 12 }}>{feature.description}</p>
              
              {status && (
                <div style={{
                  marginTop: 12,
                  padding: '4px 12px',
                  borderRadius: 20,
                  fontSize: 11,
                  fontWeight: 500,
                  display: 'inline-block',
                  background: status.bg,
                  color: status.color,
                }}>
                  {status.text}
                </div>
              )}
              
              {!allowed && feature.step === 2 && (
                <div style={{ 
                  marginTop: 12, 
                  fontSize: 11, 
                  color: '#f59e0b',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                  justifyContent: 'center'
                }}>
                  <span>🔒</span> Upload tender first
                </div>
              )}
            </motion.div>
          );
        })}
      </div>

      {/* Stats Section */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-around',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 32,
        padding: 40,
        background: '#f8fafc',
        borderRadius: 24,
        border: '1px solid #e2e8f0',
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 36, fontWeight: 800, color: '#1e40af' }}>99%</div>
          <div style={{ fontSize: 13, color: '#64748b' }}>Extraction Accuracy</div>
        </div>
        <div style={{ width: 1, height: 40, background: '#e2e8f0' }} />
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 36, fontWeight: 800, color: '#059669' }}>75%</div>
          <div style={{ fontSize: 13, color: '#64748b' }}>Time Saved</div>
        </div>
        <div style={{ width: 1, height: 40, background: '#e2e8f0' }} />
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 36, fontWeight: 800, color: '#d97706' }}>100%</div>
          <div style={{ fontSize: 13, color: '#64748b' }}>Audit Traceability</div>
        </div>
        <div style={{ width: 1, height: 40, background: '#e2e8f0' }} />
        <div style={{ textAlign: 'center' }}>
          <Shield size={28} color="#7c3aed" style={{ margin: '0 auto 8px' }} />
          <div style={{ fontSize: 13, color: '#64748b' }}>AES-256 Encrypted</div>
        </div>
      </div>

      {/* Footer Note */}
      <div style={{ textAlign: 'center', marginTop: 48, padding: 20 }}>
        <p style={{ fontSize: 12, color: '#94a3b8' }}>
          Government of India | Ministry of Home Affairs | CRPF
        </p>
      </div>
    </div>
  );
};

export default HomePage;