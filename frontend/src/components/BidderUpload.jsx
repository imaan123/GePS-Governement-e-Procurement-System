import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Trash2, Upload, FileText, X, AlertCircle } from 'lucide-react';
import { useDropzone } from 'react-dropzone';

const BidderUpload = () => {
  const { bidderCount, setBidderCount, bidderDocs, setBidderDocs, bidderNames, setBidderNames, setCurrentStep, tenderFile } = useApp();
  const [showWarning, setShowWarning] = useState(false);

  useEffect(() => {
    // Check if tender exists when component mounts
    if (!tenderFile) {
      setShowWarning(true);
    }
  }, [tenderFile]);

  const onDrop = (acceptedFiles, bidderId) => {
    setBidderDocs({
      ...bidderDocs,
      [bidderId]: [...(bidderDocs[bidderId] || []), ...acceptedFiles]
    });
  };

  const addBidder = () => {
    const newId = bidderCount + 1;
    setBidderCount(newId);
    setBidderNames({ ...bidderNames, [newId]: `Bidder ${newId}` });
    setBidderDocs({ ...bidderDocs, [newId]: [] });
  };

  const removeBidder = (id) => {
    const newDocs = { ...bidderDocs };
    const newNames = { ...bidderNames };
    delete newDocs[id];
    delete newNames[id];
    setBidderDocs(newDocs);
    setBidderNames(newNames);
  };

  const removeFile = (bidderId, fileIndex) => {
    setBidderDocs({
      ...bidderDocs,
      [bidderId]: bidderDocs[bidderId].filter((_, idx) => idx !== fileIndex)
    });
  };

  const updateBidderName = (id, name) => {
    setBidderNames({ ...bidderNames, [id]: name });
  };

  const handleProceed = () => {
    if (Object.keys(bidderDocs).length === 0) return;
    setCurrentStep(3);
  };

  // Show warning if no tender file
  if (showWarning && !tenderFile) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ maxWidth: 600, margin: '0 auto', textAlign: 'center', padding: 60 }}
      >
        <div style={{
          background: '#fef3c7',
          border: '1px solid #fde68a',
          borderRadius: 16,
          padding: 32,
        }}>
          <AlertCircle size={48} color="#d97706" style={{ margin: '0 auto 16px' }} />
          <h3 style={{ color: '#92400e', marginBottom: 12 }}>Tender Document Required</h3>
          <p style={{ color: '#92400e', marginBottom: 16 }}>
            Please upload a tender document first before adding bidders.
          </p>
          <button
            onClick={() => setCurrentStep(1)}
            style={{
              background: '#d97706',
              color: '#fff',
              border: 'none',
              padding: '10px 24px',
              borderRadius: 8,
              cursor: 'pointer',
            }}
          >
            Go to Tender Upload
          </button>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      style={{ maxWidth: 1200, margin: '0 auto' }}
    >
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <h2 style={{ fontSize: 28, marginBottom: 12, color: '#1e293b' }}>Bidder Documents Upload</h2>
        <p style={{ color: '#64748b' }}>
          Add bidders and upload their supporting documents
        </p>
        {tenderFile && (
          <div style={{
            marginTop: 12,
            padding: '8px 16px',
            background: '#f0fdf4',
            borderRadius: 8,
            display: 'inline-block',
            fontSize: 13,
            color: '#166534',
          }}>
            ✅ Tender uploaded: {tenderFile.name}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 24 }}>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={addBidder}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            background: 'linear-gradient(135deg, #1e40af, #2563eb)',
            border: 'none',
            padding: '10px 20px',
            borderRadius: 8,
            color: '#fff',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          <Plus size={18} /> Add Bidder
        </motion.button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        <AnimatePresence>
          {Object.keys(bidderDocs).map((bidderId) => (
            <motion.div
              key={bidderId}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              style={{
                background: '#ffffff',
                borderRadius: 16,
                padding: 24,
                border: '1px solid #e2e8f0',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                <input
                  type="text"
                  value={bidderNames[bidderId] || ''}
                  onChange={(e) => updateBidderName(bidderId, e.target.value)}
                  placeholder={`Bidder ${bidderId} Name`}
                  style={{
                    background: '#f8fafc',
                    border: '1px solid #e2e8f0',
                    borderRadius: 8,
                    padding: '8px 16px',
                    color: '#1e293b',
                    fontSize: 16,
                    fontWeight: 600,
                    width: 250,
                  }}
                />
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={() => removeBidder(bidderId)}
                  style={{
                    background: '#fef2f2',
                    border: 'none',
                    padding: 8,
                    borderRadius: 8,
                    cursor: 'pointer',
                  }}
                >
                  <Trash2 size={18} color="#dc2626" />
                </motion.button>
              </div>

              <BidderDropzone
                bidderId={bidderId}
                files={bidderDocs[bidderId] || []}
                onDrop={onDrop}
              />

              {bidderDocs[bidderId]?.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <div style={{ fontSize: 13, color: '#64748b', marginBottom: 8 }}>
                    Uploaded Documents ({bidderDocs[bidderId].length}):
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    {bidderDocs[bidderId].map((file, idx) => (
                      <div key={idx} style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        background: '#f8fafc',
                        padding: '4px 12px',
                        borderRadius: 6,
                        fontSize: 12,
                      }}>
                        <FileText size={12} />
                        <span>{file.name}</span>
                        <button
                          onClick={() => removeFile(bidderId, idx)}
                          style={{
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                            padding: 0,
                            marginLeft: 4,
                            display: 'flex',
                            alignItems: 'center',
                            color: '#dc2626',
                          }}
                          title="Delete this document"
                        >
                          <X size={14} />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {Object.keys(bidderDocs).length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          style={{ marginTop: 32, textAlign: 'center' }}
        >
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleProceed}
            style={{
              background: 'linear-gradient(135deg, #059669, #10b981)',
              border: 'none',
              padding: '14px 32px',
              borderRadius: 12,
              color: '#fff',
              fontSize: 16,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Start Evaluation →
          </motion.button>
        </motion.div>
      )}
    </motion.div>
  );
};

const BidderDropzone = ({ bidderId, files, onDrop }) => {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (acceptedFiles) => onDrop(acceptedFiles, bidderId),
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg'],
    },
  });

  return (
    <div
      {...getRootProps()}
      style={{
        background: isDragActive ? '#eff6ff' : '#f8fafc',
        border: `2px dashed ${isDragActive ? '#3b82f6' : '#cbd5e1'}`,
        borderRadius: 12,
        padding: 32,
        textAlign: 'center',
        cursor: 'pointer',
        transition: 'all 0.3s',
      }}
    >
      <input {...getInputProps()} />
      <Upload size={32} color="#3b82f6" style={{ marginBottom: 8 }} />
      <p style={{ fontSize: 14, color: '#64748b' }}>
        {isDragActive ? 'Drop documents here' : 'Drag & drop or click to upload documents'}
      </p>
      <p style={{ fontSize: 12, color: '#94a3b8' }}>PDF, PNG, JPG (max 20MB each)</p>
    </div>
  );
};

export default BidderUpload;