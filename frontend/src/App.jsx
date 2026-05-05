import React from 'react';
import { AppProvider, useApp } from './context/AppContext';
import Navbar from './components/Navbar';
import HomePage from './components/HomePage';
import TenderUpload from './components/TenderUpload';
import BidderUpload from './components/BidderUpload';
import ProcessingPage from './components/ProcessingPage';
import ResultsPage from './components/ResultsPage';
import HumanReviewPage from './components/HumanReviewPage';
import FeedbackPage from './components/FeedbackPage';
import { motion, AnimatePresence } from 'framer-motion';

function AppContent() {
  const { currentStep } = useApp();

  const renderStep = () => {
    switch(currentStep) {
      case 0: return <HomePage />;
      case 1: return <TenderUpload />;
      case 2: return <BidderUpload />;
      case 3: return <ProcessingPage />;
      case 4: return <ResultsPage />;
      case 5: return <HumanReviewPage />;
      case 6: return <FeedbackPage />;
      default: return <HomePage />;
    }
  };

  return (
    <div className="grid-bg" style={{ minHeight: '100vh', paddingTop: '64px', background: '#ffffff' }}>
      <Navbar />
      <AnimatePresence mode="wait">
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
          style={{ padding: '32px', maxWidth: '1400px', margin: '0 auto' }}
        >
          {renderStep()}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}

export default App;