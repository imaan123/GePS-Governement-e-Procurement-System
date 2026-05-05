import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { motion } from 'framer-motion';
import { Loader2, CheckCircle, FileText, Users, Scale, TrendingUp, AlertCircle, Play } from 'lucide-react';
import { MOCK_EVALUATION_RESULTS } from '../services/api';

const ProcessingPage = () => {
  const { 
    setEvaluationResults, 
    setReviewQueue, 
    setAuditLog, 
    setCurrentStep, 
    tenderFile, 
    bidderDocs,
    evaluationResults 
  } = useApp();
  
  const [progress, setProgress] = useState(0);
  const [currentStage, setCurrentStage] = useState(0);
  const [complete, setComplete] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingComplete, setProcessingComplete] = useState(false);
  const [shouldStartProcessing, setShouldStartProcessing] = useState(false);

  const stages = [
    { icon: FileText, label: 'Extracting tender criteria', percent: 25 },
    { icon: Users, label: 'Processing bidder documents', percent: 50 },
    { icon: Scale, label: 'Evaluating rules', percent: 75 },
    { icon: TrendingUp, label: 'Generating results', percent: 100 },
  ];

  const hasRealTenderData = tenderFile !== null;
  const hasRealBidderData = Object.keys(bidderDocs).length > 0;
  const hasRealEvaluationData = evaluationResults !== null;
  
  const hasRealData = hasRealTenderData || hasRealBidderData;
  
  // Check if current results are mock data
  const isShowingMockResults = evaluationResults === MOCK_EVALUATION_RESULTS;
  const isDemoMode = !hasRealData && !hasRealEvaluationData;
  const isDemoResult = hasRealEvaluationData && isShowingMockResults;

  // Function to start processing (for both real and demo)
  const startProcessing = () => {
    setProgress(0);
    setCurrentStage(0);
    setComplete(false);
    setProcessingComplete(false);
    setShouldStartProcessing(true);
    setIsProcessing(true);
  };

  // Effect for processing data (real or mock based on what's available)
  useEffect(() => {
    if ((isProcessing || shouldStartProcessing) && !complete && !processingComplete) {
      setShouldStartProcessing(false);
      
      const interval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 100) {
            clearInterval(interval);
            setTimeout(() => {
              // Use real results if they exist and are not mock, otherwise use mock data
              let resultsToUse;
              
              if (hasRealEvaluationData && !isShowingMockResults) {
                // Real results already exist
                resultsToUse = evaluationResults;
              } else if (hasRealData) {
                // Create results based on real uploaded data
                resultsToUse = {
                  tender_id: 'T-2026-001',
                  tender_name: tenderFile?.name || 'Uploaded Tender',
                  evaluated_at: new Date().toISOString(),
                  bidders: Object.keys(bidderDocs).map((id, idx) => ({
                    bidder_id: `B00${idx + 1}`,
                    bidder_name: bidderDocs[id]?.[0]?.name?.replace(/\.[^/.]+$/, '') || `Bidder ${id}`,
                    overall_verdict: idx === 0 ? 'ELIGIBLE' : idx === 1 ? 'NOT ELIGIBLE' : 'NEEDS REVIEW',
                    overall_confidence: idx === 0 ? 0.92 : idx === 1 ? 0.85 : 0.64,
                    criteria: [
                      {
                        rule_id: 'FIN-001',
                        category: 'Financial',
                        description: 'Average Annual Turnover ≥ ₹5 Crore (last 3 FY)',
                        extracted_value: idx === 0 ? '₹7.2 Cr (avg)' : idx === 1 ? '₹3.8 Cr (avg)' : 'Not found',
                        threshold: '₹5 Cr',
                        result: idx === 0 ? 'PASS' : idx === 1 ? 'FAIL' : 'NEEDS REVIEW',
                        confidence: idx === 0 ? 0.91 : idx === 1 ? 0.87 : 0.62,
                        source_doc: 'balance_sheet.pdf',
                        source_page: 4,
                      }
                    ]
                  })),
                  review_queue: [],
                  audit_log: [
                    { timestamp: new Date().toISOString(), actor: 'SYSTEM', action: 'Evaluation started', detail: 'Processing uploaded data' }
                  ]
                };
              } else {
                // Use mock data for demo
                resultsToUse = MOCK_EVALUATION_RESULTS;
              }
              
              setEvaluationResults(resultsToUse);
              setReviewQueue(resultsToUse.review_queue || []);
              setAuditLog(resultsToUse.audit_log || []);
              setComplete(true);
              setProcessingComplete(true);
              setIsProcessing(false);
              setShouldStartProcessing(false);
              setTimeout(() => setCurrentStep(4), 1500);
            }, 500);
            return 100;
          }
          
          if (prev >= 25 && currentStage < 1) setCurrentStage(1);
          if (prev >= 50 && currentStage < 2) setCurrentStage(2);
          if (prev >= 75 && currentStage < 3) setCurrentStage(3);
          
          return prev + 2;
        });
      }, 100);

      return () => clearInterval(interval);
    }
  }, [isProcessing, shouldStartProcessing, complete, processingComplete, currentStage, hasRealData, hasRealEvaluationData, isShowingMockResults, tenderFile, bidderDocs, evaluationResults, setEvaluationResults, setReviewQueue, setAuditLog, setCurrentStep]);

  // If evaluation results already exist and not in processing, show summary with working re-run button
  if (hasRealEvaluationData && !isProcessing && !processingComplete) {
    const isDemo = isDemoResult || isDemoMode;
    
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        style={{ maxWidth: 800, margin: '0 auto' }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <CheckCircle size={48} color={isDemo ? '#8b5cf6' : '#10b981'} style={{ margin: '0 auto 16px' }} />
          <h2 style={{ fontSize: 28, marginBottom: 12, color: '#1e293b' }}>
            {isDemo ? '🎬 Demo Evaluation Complete!' : '✅ Evaluation Complete'}
          </h2>
          <p style={{ color: '#64748b' }}>
            {isDemo 
              ? 'Sample evaluation results are ready to view. Upload real documents to evaluate your actual data.' 
              : 'Your evaluation results are ready to view'}
          </p>
        </div>

        <div style={{
          background: isDemo ? '#f3e8ff' : '#f0fdf4',
          border: `1px solid ${isDemo ? '#c4b5fd' : '#bbf7d0'}`,
          borderRadius: 16,
          padding: 24,
          marginBottom: 24,
        }}>
          <h3 style={{ marginBottom: 12, color: isDemo ? '#6d28d9' : '#166534' }}>Summary</h3>
          <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
            <div>
              <div style={{ fontSize: 12, color: isDemo ? '#6d28d9' : '#166534' }}>Total Bidders</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: isDemo ? '#6d28d9' : '#166534' }}>
                {evaluationResults.bidders?.length || 0}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 12, color: isDemo ? '#6d28d9' : '#166534' }}>Eligible</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: isDemo ? '#6d28d9' : '#166534' }}>
                {evaluationResults.bidders?.filter(b => b.overall_verdict === 'ELIGIBLE').length || 0}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 12, color: isDemo ? '#6d28d9' : '#166534' }}>Needs Review</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: isDemo ? '#6d28d9' : '#166534' }}>
                {evaluationResults.bidders?.filter(b => b.overall_verdict === 'NEEDS REVIEW').length || 0}
              </div>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 16, justifyContent: 'center' }}>
          <button
            onClick={() => setCurrentStep(4)}
            style={{
              background: isDemo ? '#8b5cf6' : '#3b82f6',
              color: '#fff',
              border: 'none',
              padding: '12px 24px',
              borderRadius: 8,
              cursor: 'pointer',
              fontWeight: 500,
            }}
          >
            {isDemo ? '🎬 View Demo Results →' : '📊 View Results Dashboard →'}
          </button>
          <button
            onClick={() => {
              // Clear current results and start new evaluation
              setEvaluationResults(null);
              setComplete(false);
              setProgress(0);
              setProcessingComplete(false);
              setCurrentStage(0);
              setShouldStartProcessing(false);
              // Small delay to ensure state updates
              setTimeout(() => {
                startProcessing();
              }, 100);
            }}
            style={{
              background: '#f8fafc',
              color: '#475569',
              border: '1px solid #e2e8f0',
              padding: '12px 24px',
              borderRadius: 8,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
            onMouseEnter={e => { e.target.style.background = '#f1f5f9'; }}
            onMouseLeave={e => { e.target.style.background = '#f8fafc'; }}
          >
            <Play size={16} /> Re-run Evaluation
          </button>
        </div>
      </motion.div>
    );
  }

  // Show start evaluation button (not processing yet)
  if (!isProcessing && !complete && !processingComplete && !shouldStartProcessing) {
    const isDemo = !hasRealData && !hasRealEvaluationData;
    
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        style={{ maxWidth: 800, margin: '0 auto' }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          {isDemo && (
            <div style={{
              display: 'inline-block',
              background: '#f3e8ff',
              color: '#6d28d9',
              padding: '4px 12px',
              borderRadius: 20,
              fontSize: 12,
              marginBottom: 12,
            }}>
              🎬 Demo Mode - Preview with Sample Data
            </div>
          )}
          <h2 style={{ fontSize: 28, marginBottom: 12, color: '#1e293b' }}>AI Evaluation</h2>
          <p style={{ color: '#64748b' }}>
            {isDemo 
              ? 'Try the evaluation with sample data to see how it works' 
              : 'Our AI will analyze your uploaded bidder documents against tender criteria'}
          </p>
        </div>

        {/* Data Summary */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 20,
          marginBottom: 32,
        }}>
          <div style={{
            background: '#ffffff',
            border: `1px solid ${isDemo ? '#c4b5fd' : '#e2e8f0'}`,
            borderRadius: 16,
            padding: 20,
            textAlign: 'center',
          }}>
            <FileText size={32} color={isDemo ? '#8b5cf6' : '#3b82f6'} style={{ margin: '0 auto 8px' }} />
            <div style={{ fontSize: 24, fontWeight: 700, color: '#1e293b' }}>
              {hasRealTenderData ? '✓' : (isDemo ? '📋' : '❌')}
            </div>
            <div style={{ fontSize: 13, color: '#64748b' }}>Tender Document</div>
            {hasRealTenderData && <div style={{ fontSize: 11, color: '#059669' }}>{tenderFile.name}</div>}
            {isDemo && !hasRealTenderData && <div style={{ fontSize: 11, color: '#8b5cf6' }}>Sample Tender Data</div>}
          </div>
          
          <div style={{
            background: '#ffffff',
            border: `1px solid ${isDemo ? '#c4b5fd' : '#e2e8f0'}`,
            borderRadius: 16,
            padding: 20,
            textAlign: 'center',
          }}>
            <Users size={32} color={isDemo ? '#8b5cf6' : '#059669'} style={{ margin: '0 auto 8px' }} />
            <div style={{ fontSize: 24, fontWeight: 700, color: '#1e293b' }}>
              {hasRealBidderData ? Object.keys(bidderDocs).length : (isDemo ? '3' : '0')}
            </div>
            <div style={{ fontSize: 13, color: '#64748b' }}>Bidder(s) Added</div>
            {hasRealBidderData && Object.keys(bidderDocs).length > 0 && (
              <div style={{ fontSize: 11, color: '#059669' }}>
                {Object.values(bidderDocs).flat().length} document(s)
              </div>
            )}
            {isDemo && !hasRealBidderData && (
              <div style={{ fontSize: 11, color: '#8b5cf6' }}>3 Sample Bidders</div>
            )}
          </div>
        </div>

        <div style={{
          background: isDemo ? '#f3e8ff' : '#eff6ff',
          borderRadius: 16,
          padding: 20,
          marginBottom: 24,
          border: `1px solid ${isDemo ? '#c4b5fd' : '#bfdbfe'}`,
        }}>
          <h4 style={{ marginBottom: 12, color: isDemo ? '#6d28d9' : '#1e40af' }}>What will be evaluated:</h4>
          <ul style={{ color: '#475569', paddingLeft: 20 }}>
            <li>Financial criteria (turnover, net worth)</li>
            <li>Technical criteria (project experience)</li>
            <li>Compliance documents (GST, registrations)</li>
            <li>Certifications (ISO, quality standards)</li>
          </ul>
        </div>

        <button
          onClick={startProcessing}
          style={{
            width: '100%',
            background: isDemo 
              ? 'linear-gradient(135deg, #8b5cf6, #7c3aed)'
              : 'linear-gradient(135deg, #1e40af, #2563eb)',
            border: 'none',
            padding: '16px',
            borderRadius: 12,
            color: '#fff',
            fontSize: 16,
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
          }}
        >
          <Play size={20} /> {isDemo ? '🎬 Try Demo Evaluation' : '🚀 Start AI Evaluation'}
        </button>
        
        {isDemo && (
          <p style={{ fontSize: 12, color: '#94a3b8', textAlign: 'center', marginTop: 12 }}>
            ℹ️ Demo mode shows how the evaluation works. Upload real documents to evaluate your actual data.
          </p>
        )}
      </motion.div>
    );
  }

  // Show processing animation
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      style={{ maxWidth: 800, margin: '0 auto', textAlign: 'center' }}
    >
      <div style={{ marginBottom: 48 }}>
        <Loader2 size={64} style={{ animation: 'spin 2s linear infinite', margin: '0 auto 24px', color: '#3b82f6' }} />
        
        <h2 style={{ fontSize: 28, marginBottom: 12, color: '#1e293b' }}>
          {isDemoMode ? '🎬 Processing Demo Data...' : (hasRealData ? '📄 Processing Your Documents' : 'Processing...')}
        </h2>
        <p style={{ color: '#64748b' }}>
          {isDemoMode 
            ? 'Loading sample evaluation data to demonstrate the system' 
            : (hasRealData 
              ? 'Our AI is analyzing your tender criteria and bidder documents' 
              : 'Please wait while we process your request')}
        </p>
      </div>

      {/* Progress Bar */}
      <div style={{
        background: '#e2e8f0',
        borderRadius: 12,
        padding: 4,
        marginBottom: 32,
      }}>
        <div style={{
          width: `${progress}%`,
          height: 8,
          background: 'linear-gradient(90deg, #1e40af, #3b82f6)',
          borderRadius: 8,
          transition: 'width 0.3s ease',
        }} />
      </div>

      {/* Stages */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {stages.map((stage, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.1 }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              padding: 16,
              background: progress >= stage.percent ? '#eff6ff' : '#ffffff',
              borderRadius: 12,
              border: `1px solid ${progress >= stage.percent ? '#bfdbfe' : '#e2e8f0'}`,
            }}
          >
            <div style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              background: progress >= stage.percent ? '#3b82f6' : '#f1f5f9',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              {progress >= stage.percent ? (
                <CheckCircle size={18} color="#fff" />
              ) : (
                <stage.icon size={18} color="#94a3b8" />
              )}
            </div>
            <div style={{ flex: 1, textAlign: 'left' }}>
              <div style={{ fontWeight: 500, color: '#1e293b' }}>{stage.label}</div>
              <div style={{ fontSize: 12, color: '#94a3b8' }}>
                {progress >= stage.percent ? 'Complete' : 'Pending'}
              </div>
            </div>
            {progress >= stage.percent && (
              <div style={{ fontSize: 12, color: '#059669' }}>✓ Done</div>
            )}
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};

export default ProcessingPage;