import React, { createContext, useContext, useState } from 'react';

const AppContext = createContext(null);

export const AppProvider = ({ children }) => {
  const [tenderFile, setTenderFile] = useState(null);
  const [bidderCount, setBidderCount] = useState(0);
  const [bidderDocs, setBidderDocs] = useState({});
  const [bidderNames, setBidderNames] = useState({});
  const [processingStatus, setProcessingStatus] = useState(null);
  const [evaluationResults, setEvaluationResults] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [reviewQueue, setReviewQueue] = useState([]);
  const [feedbackLog, setFeedbackLog] = useState([]);
  const [auditLog, setAuditLog] = useState([]);

  const resetAll = () => {
    setTenderFile(null);
    setBidderCount(0);
    setBidderDocs({});
    setBidderNames({});
    setProcessingStatus(null);
    setEvaluationResults(null);
    setCurrentStep(0);
    setReviewQueue([]);
    setFeedbackLog([]);
    setAuditLog([]);
  };

  return (
    <AppContext.Provider value={{
      tenderFile, setTenderFile,
      bidderCount, setBidderCount,
      bidderDocs, setBidderDocs,
      bidderNames, setBidderNames,
      processingStatus, setProcessingStatus,
      evaluationResults, setEvaluationResults,
      currentStep, setCurrentStep,
      reviewQueue, setReviewQueue,
      feedbackLog, setFeedbackLog,
      auditLog, setAuditLog,
      resetAll
    }}>
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
};