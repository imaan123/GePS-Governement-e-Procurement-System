import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { useApp } from '../context/AppContext';
import { motion } from 'framer-motion';
import { Upload, FileText, CheckCircle, Trash2, AlertCircle } from 'lucide-react';

const TenderUpload = () => {
  const { setTenderFile, setCurrentStep } = useApp();
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    setError(null);
    
    if (rejectedFiles && rejectedFiles.length > 0) {
      setError('Only PDF files are accepted');
      return;
    }
    
    const uploadedFile = acceptedFiles[0];
    if (uploadedFile && uploadedFile.type === 'application/pdf') {
      if (uploadedFile.size > 50 * 1024 * 1024) {
        setError('File size must be less than 50MB');
        return;
      }
      setFile(uploadedFile);
    } else {
      setError('Please upload a valid PDF file');
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024,
  });

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    setTenderFile(file);
    alert('✅ Tender document uploaded successfully! Now you can add bidders.');
    setCurrentStep(2);
    setUploading(false);
  };

  const handleDeleteFile = () => {
    if (window.confirm('Remove this tender document?')) {
      setFile(null);
      setError(null);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      style={{ maxWidth: 800, margin: '0 auto' }}
    >
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <h2 style={{ fontSize: 28, marginBottom: 12, color: '#1e293b' }}>Tender Document Upload</h2>
        <p style={{ color: '#64748b' }}>
          Upload the tender PDF for AI-powered criteria extraction
        </p>
      </div>

      <div
        {...getRootProps()}
        style={{
          background: isDragActive ? '#eff6ff' : '#ffffff',
          border: `2px dashed ${isDragActive ? '#3b82f6' : '#cbd5e1'}`,
          borderRadius: 20,
          padding: 60,
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.3s',
        }}
      >
        <input {...getInputProps()} />
        <Upload size={48} color="#3b82f6" style={{ marginBottom: 16 }} />
        {isDragActive ? (
          <p style={{ fontSize: 18, color: '#1e293b' }}>Drop your tender PDF here...</p>
        ) : (
          <>
            <p style={{ fontSize: 18, marginBottom: 8, color: '#1e293b' }}>Drag & drop your tender document</p>
            <p style={{ fontSize: 14, color: '#94a3b8' }}>or click to browse (PDF only, max 50MB)</p>
          </>
        )}
      </div>

      {error && (
        <div style={{
          marginTop: 16,
          padding: 12,
          background: '#fef2f2',
          borderRadius: 8,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          color: '#dc2626',
          fontSize: 14,
        }}>
          <AlertCircle size={18} />
          {error}
        </div>
      )}

      {file && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            marginTop: 24,
            padding: 16,
            background: '#f8fafc',
            borderRadius: 12,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            border: '1px solid #e2e8f0',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <FileText size={24} color="#3b82f6" />
            <div>
              <div style={{ fontWeight: 500, color: '#1e293b' }}>{file.name}</div>
              <div style={{ fontSize: 12, color: '#64748b' }}>
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 12 }}>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleDeleteFile}
              disabled={uploading}
              style={{
                background: '#fef2f2',
                border: '1px solid #fecaca',
                padding: '8px 16px',
                borderRadius: 8,
                color: '#dc2626',
                fontWeight: 500,
                cursor: uploading ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                opacity: uploading ? 0.6 : 1,
              }}
            >
              <Trash2 size={18} /> Delete
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleUpload}
              disabled={uploading}
              style={{
                background: 'linear-gradient(135deg, #1e40af, #2563eb)',
                border: 'none',
                padding: '10px 24px',
                borderRadius: 8,
                color: '#fff',
                fontWeight: 600,
                cursor: uploading ? 'not-allowed' : 'pointer',
                opacity: uploading ? 0.6 : 1,
              }}
            >
              {uploading ? 'Processing...' : 'Upload & Continue'}
            </motion.button>
          </div>
        </motion.div>
      )}

      <div style={{
        marginTop: 32,
        padding: 20,
        background: '#eff6ff',
        borderRadius: 12,
        border: '1px solid #bfdbfe',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <CheckCircle size={18} color="#059669" />
          <span style={{ fontWeight: 600, color: '#1e293b' }}>What happens next?</span>
        </div>
        <ul style={{ color: '#475569', fontSize: 14, paddingLeft: 24 }}>
          <li>AI extracts eligibility criteria from the document</li>
          <li>Rules are classified into Financial, Technical, and Compliance categories</li>
          <li>Each rule gets a unique identifier and confidence score</li>
        </ul>
      </div>
    </motion.div>
  );
};

export default TenderUpload;