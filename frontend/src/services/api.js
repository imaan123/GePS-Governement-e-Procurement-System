// api.js — API service layer for GePS backend
// Replace BASE_URL with your actual backend endpoint

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// ─── Helpers ───────────────────────────────────────────────────────────────

const handleResponse = async (res) => {
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
};

// ─── Tender APIs ───────────────────────────────────────────────────────────

export const uploadTender = async (file) => {
  const formData = new FormData();
  formData.append('tender_file', file);
  const res = await fetch(`${BASE_URL}/tender/upload`, { method: 'POST', body: formData });
  return handleResponse(res);
};

export const getTenderRules = async (tenderId) => {
  const res = await fetch(`${BASE_URL}/tender/${tenderId}/rules`);
  return handleResponse(res);
};

// ─── Bidder APIs ────────────────────────────────────────────────────────────

export const uploadBidderDocuments = async (tenderId, bidderId, bidderName, files) => {
  const formData = new FormData();
  formData.append('tender_id', tenderId);
  formData.append('bidder_id', bidderId);
  formData.append('bidder_name', bidderName);
  files.forEach(f => formData.append('documents', f));
  const res = await fetch(`${BASE_URL}/bidder/upload`, { method: 'POST', body: formData });
  return handleResponse(res);
};

export const getBidderProfile = async (bidderId) => {
  const res = await fetch(`${BASE_URL}/bidder/${bidderId}/profile`);
  return handleResponse(res);
};

// ─── Evaluation APIs ────────────────────────────────────────────────────────

export const triggerEvaluation = async (tenderId, bidderIds) => {
  const res = await fetch(`${BASE_URL}/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tender_id: tenderId, bidder_ids: bidderIds }),
  });
  return handleResponse(res);
};

export const getEvaluationStatus = async (jobId) => {
  const res = await fetch(`${BASE_URL}/evaluate/${jobId}/status`);
  return handleResponse(res);
};

export const getEvaluationResults = async (jobId) => {
  const res = await fetch(`${BASE_URL}/evaluate/${jobId}/results`);
  return handleResponse(res);
};

// ─── Human Review APIs ──────────────────────────────────────────────────────

export const getReviewQueue = async (jobId) => {
  const res = await fetch(`${BASE_URL}/review/${jobId}/queue`);
  return handleResponse(res);
};

export const submitReviewDecision = async (reviewId, decision) => {
  const res = await fetch(`${BASE_URL}/review/${reviewId}/decide`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(decision),
  });
  return handleResponse(res);
};

// ─── Feedback APIs ──────────────────────────────────────────────────────────

export const submitFeedback = async (feedback) => {
  const res = await fetch(`${BASE_URL}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(feedback),
  });
  return handleResponse(res);
};

export const getFeedbackStats = async () => {
  const res = await fetch(`${BASE_URL}/feedback/stats`);
  return handleResponse(res);
};

// ─── Audit APIs ─────────────────────────────────────────────────────────────

export const getAuditLog = async (jobId) => {
  const res = await fetch(`${BASE_URL}/audit/${jobId}/log`);
  return handleResponse(res);
};

export const exportAuditReport = async (jobId) => {
  const res = await fetch(`${BASE_URL}/audit/${jobId}/export`);
  if (!res.ok) throw new Error('Export failed');
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `geps_audit_report_${jobId}.pdf`;
  a.click();
  URL.revokeObjectURL(url);
};

// ─── Mock data for UI development without backend ──────────────────────────

export const MOCK_EVALUATION_RESULTS = {
  tender_id: 'T-2026-001',
  tender_name: 'CRPF Infrastructure Development Tender',
  evaluated_at: new Date().toISOString(),
  bidders: [
    {
      bidder_id: 'B001',
      bidder_name: 'ABC Infrastructure Pvt. Ltd.',
      overall_verdict: 'ELIGIBLE',
      overall_confidence: 0.92,
      criteria: [
        {
          rule_id: 'FIN-001',
          category: 'Financial',
          description: 'Average Annual Turnover ≥ ₹5 Crore (last 3 FY)',
          extracted_value: '₹7.2 Cr (avg)',
          threshold: '₹5 Cr',
          result: 'PASS',
          confidence: 0.91,
          source_doc: 'balance_sheet_2024.pdf',
          source_page: 4,
          raw_text: 'Total revenue from operations: ₹7.2 Cr (2021-22), ₹6.8 Cr (2022-23), ₹7.9 Cr (2023-24)',
          evaluation_logic: 'average_turnover (72,000,000) >= required (50,000,000)'
        },
        {
          rule_id: 'TECH-001',
          category: 'Technical',
          description: 'Minimum 3 similar completed projects',
          extracted_value: '4 projects',
          threshold: '3 projects',
          result: 'PASS',
          confidence: 0.88,
          source_doc: 'project_certificates.pdf',
          source_page: 2,
          raw_text: 'Completion certificates for 4 road construction projects',
          evaluation_logic: 'completed_projects (4) >= required (3)'
        },
        {
          rule_id: 'COMP-001',
          category: 'Compliance',
          description: 'Valid GST Registration',
          extracted_value: 'GSTIN: 27AABCA1234F1Z5',
          threshold: 'EXISTS',
          result: 'PASS',
          confidence: 0.97,
          source_doc: 'gst_certificate.pdf',
          source_page: 1,
          raw_text: 'GST Registration Certificate — GSTIN: 27AABCA1234F1Z5',
          evaluation_logic: 'gst_registration EXISTS'
        },
        {
          rule_id: 'CERT-001',
          category: 'Certification',
          description: 'ISO 9001:2015 Certification',
          extracted_value: 'ISO 9001:2015',
          threshold: 'EXISTS',
          result: 'PASS',
          confidence: 0.94,
          source_doc: 'iso_certificate.pdf',
          source_page: 1,
          raw_text: 'ISO 9001:2015 Quality Management System Certificate',
          evaluation_logic: 'iso_certification EXISTS'
        },
        {
          rule_id: 'FIN-002',
          category: 'Financial',
          description: 'Net Worth ≥ ₹2 Crore',
          extracted_value: '₹4.5 Cr',
          threshold: '₹2 Cr',
          result: 'PASS',
          confidence: 0.89,
          source_doc: 'balance_sheet_2024.pdf',
          source_page: 6,
          raw_text: 'Net worth as of March 2024: ₹4.5 Crore',
          evaluation_logic: 'net_worth (45,000,000) >= required (20,000,000)'
        },
      ]
    },
    {
      bidder_id: 'B002',
      bidder_name: 'XYZ Construction Ltd.',
      overall_verdict: 'NOT ELIGIBLE',
      overall_confidence: 0.85,
      criteria: [
        {
          rule_id: 'FIN-001',
          category: 'Financial',
          description: 'Average Annual Turnover ≥ ₹5 Crore (last 3 FY)',
          extracted_value: '₹3.8 Cr (avg)',
          threshold: '₹5 Cr',
          result: 'FAIL',
          confidence: 0.87,
          source_doc: 'financials_2024.pdf',
          source_page: 3,
          raw_text: 'Annual revenue: ₹3.6 Cr, ₹3.9 Cr, ₹3.8 Cr',
          evaluation_logic: 'average_turnover (38,000,000) < required (50,000,000)'
        },
        {
          rule_id: 'TECH-001',
          category: 'Technical',
          description: 'Minimum 3 similar completed projects',
          extracted_value: '2 projects',
          threshold: '3 projects',
          result: 'FAIL',
          confidence: 0.82,
          source_doc: 'project_list.pdf',
          source_page: 1,
          raw_text: 'Submitted completion certificates for 2 projects',
          evaluation_logic: 'completed_projects (2) < required (3)'
        },
        {
          rule_id: 'COMP-001',
          category: 'Compliance',
          description: 'Valid GST Registration',
          extracted_value: 'GSTIN: 07AABCX5678G1Z3',
          threshold: 'EXISTS',
          result: 'PASS',
          confidence: 0.96,
          source_doc: 'compliance_docs.pdf',
          source_page: 2,
          raw_text: 'GST Certificate — GSTIN: 07AABCX5678G1Z3',
          evaluation_logic: 'gst_registration EXISTS'
        },
        {
          rule_id: 'CERT-001',
          category: 'Certification',
          description: 'ISO 9001:2015 Certification',
          extracted_value: 'Not found',
          threshold: 'EXISTS',
          result: 'FAIL',
          confidence: 0.79,
          source_doc: null,
          source_page: null,
          raw_text: null,
          evaluation_logic: 'iso_certification NOT EXISTS'
        },
        {
          rule_id: 'FIN-002',
          category: 'Financial',
          description: 'Net Worth ≥ ₹2 Crore',
          extracted_value: '₹1.8 Cr',
          threshold: '₹2 Cr',
          result: 'FAIL',
          confidence: 0.84,
          source_doc: 'financials_2024.pdf',
          source_page: 7,
          raw_text: 'Net worth: ₹1.8 Crore (audited)',
          evaluation_logic: 'net_worth (18,000,000) < required (20,000,000)'
        },
      ]
    },
    {
      bidder_id: 'B003',
      bidder_name: 'Sunrise Builders & Co.',
      overall_verdict: 'NEEDS REVIEW',
      overall_confidence: 0.64,
      criteria: [
        {
          rule_id: 'FIN-001',
          category: 'Financial',
          description: 'Average Annual Turnover ≥ ₹5 Crore (last 3 FY)',
          extracted_value: 'Not found',
          threshold: '₹5 Cr',
          result: 'NEEDS REVIEW',
          confidence: 0.62,
          source_doc: 'annexure_b.pdf',
          source_page: 17,
          raw_text: null,
          evaluation_logic: 'extraction_confidence below threshold (0.62 < 0.75)'
        },
        {
          rule_id: 'TECH-001',
          category: 'Technical',
          description: 'Minimum 3 similar completed projects',
          extracted_value: '3 projects',
          threshold: '3 projects',
          result: 'PASS',
          confidence: 0.86,
          source_doc: 'work_orders.pdf',
          source_page: 3,
          raw_text: 'Three project completion certificates enclosed',
          evaluation_logic: 'completed_projects (3) >= required (3)'
        },
        {
          rule_id: 'COMP-001',
          category: 'Compliance',
          description: 'Valid GST Registration',
          extracted_value: 'GSTIN: 29AABCS9012H1Z7',
          threshold: 'EXISTS',
          result: 'PASS',
          confidence: 0.95,
          source_doc: 'registration_docs.pdf',
          source_page: 1,
          raw_text: 'GST Registration: 29AABCS9012H1Z7',
          evaluation_logic: 'gst_registration EXISTS'
        },
        {
          rule_id: 'CERT-001',
          category: 'Certification',
          description: 'ISO 9001:2015 Certification',
          extracted_value: 'ISO 9001 (year unclear)',
          threshold: 'EXISTS',
          result: 'NEEDS REVIEW',
          confidence: 0.58,
          source_doc: 'certificates.pdf',
          source_page: 5,
          raw_text: 'ISO 9001 certificate — date partially obscured due to scan quality',
          evaluation_logic: 'confidence below threshold — expiry date unclear'
        },
        {
          rule_id: 'FIN-002',
          category: 'Financial',
          description: 'Net Worth ≥ ₹2 Crore',
          extracted_value: '₹2.3 Cr',
          threshold: '₹2 Cr',
          result: 'PASS',
          confidence: 0.81,
          source_doc: 'balance_sheet_2024.pdf',
          source_page: 8,
          raw_text: 'Net worth (audited): ₹2.3 Crore',
          evaluation_logic: 'net_worth (23,000,000) >= required (20,000,000)'
        },
      ]
    }
  ],
  review_queue: [
    {
      review_id: 'RV-001',
      bidder_id: 'B003',
      bidder_name: 'Sunrise Builders & Co.',
      rule_id: 'FIN-001',
      criterion: 'Average Annual Turnover ≥ ₹5 Crore (last 3 FY)',
      ai_verdict: 'FAIL',
      confidence: 0.62,
      evidence: 'No turnover figure extracted. Relevant section may be in Annexure B, page 17.',
      source_doc: 'annexure_b.pdf',
      source_page: 17,
      priority: 'HIGH',
      reason_flagged: 'extraction_confidence_low'
    },
    {
      review_id: 'RV-002',
      bidder_id: 'B003',
      bidder_name: 'Sunrise Builders & Co.',
      rule_id: 'CERT-001',
      criterion: 'ISO 9001:2015 Certification',
      ai_verdict: 'FAIL',
      confidence: 0.58,
      evidence: 'ISO certificate detected but validity date is unclear due to scan quality.',
      source_doc: 'certificates.pdf',
      source_page: 5,
      priority: 'MEDIUM',
      reason_flagged: 'ocr_quality_poor'
    }
  ],
  audit_log: [
    { timestamp: new Date(Date.now() - 120000).toISOString(), actor: 'SYSTEM', action: 'Tender document ingested', detail: 'Layout detection complete — 28 pages processed' },
    { timestamp: new Date(Date.now() - 115000).toISOString(), actor: 'SYSTEM', action: 'Rule extraction complete', detail: '12 rules extracted: 8 mandatory, 3 optional, 1 conditional' },
    { timestamp: new Date(Date.now() - 100000).toISOString(), actor: 'SYSTEM', action: 'Bidder B001 profile built', detail: 'All 5 fields extracted with confidence ≥ 0.88' },
    { timestamp: new Date(Date.now() - 90000).toISOString(), actor: 'SYSTEM', action: 'Bidder B002 profile built', detail: 'All 5 fields extracted with confidence ≥ 0.79' },
    { timestamp: new Date(Date.now() - 80000).toISOString(), actor: 'SYSTEM', action: 'Bidder B003 profile built', detail: '2 fields flagged for review (confidence < 0.75)' },
    { timestamp: new Date(Date.now() - 60000).toISOString(), actor: 'SYSTEM', action: 'Rule engine evaluation complete', detail: 'B001: ELIGIBLE | B002: NOT ELIGIBLE | B003: NEEDS REVIEW' },
    { timestamp: new Date(Date.now() - 50000).toISOString(), actor: 'SYSTEM', action: 'Review queue populated', detail: '2 items flagged for human review (RV-001, RV-002)' },
  ]
};
