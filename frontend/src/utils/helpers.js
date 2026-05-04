/**
 * Format file size from bytes to human readable format
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size (e.g., "2.5 MB")
 */
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * Format date to localized string
 * @param {string|Date} date - Date to format
 * @param {string} format - Format type ('full', 'date', 'time', 'datetime')
 * @returns {string} Formatted date string
 */
export const formatDate = (date, format = 'datetime') => {
  const d = new Date(date);
  if (isNaN(d.getTime())) return 'Invalid date';
  
  const options = {
    full: { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' },
    date: { year: 'numeric', month: 'short', day: 'numeric' },
    time: { hour: '2-digit', minute: '2-digit', second: '2-digit' },
    datetime: { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' },
  };
  
  return d.toLocaleDateString('en-US', options[format] || options.datetime);
};

/**
 * Truncate text to specified length
 * @param {string} text - Text to truncate
 * @param {number} length - Maximum length
 * @returns {string} Truncated text
 */
export const truncateText = (text, length = 100) => {
  if (!text) return '';
  if (text.length <= length) return text;
  return text.substring(0, length) + '...';
};

/**
 * Generate random ID
 * @param {string} prefix - Optional prefix for the ID
 * @returns {string} Generated ID
 */
export const generateId = (prefix = 'id') => {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Deep clone an object
 * @param {object} obj - Object to clone
 * @returns {object} Cloned object
 */
export const deepClone = (obj) => {
  return JSON.parse(JSON.stringify(obj));
};

/**
 * Download file as blob
 * @param {Blob} blob - File blob
 * @param {string} filename - Name for downloaded file
 */
export const downloadFile = (blob, filename) => {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

/**
 * Export data as CSV
 * @param {Array} data - Array of objects to export
 * @param {string} filename - Name for CSV file
 */
export const exportToCSV = (data, filename = 'export.csv') => {
  if (!data || data.length === 0) return;
  
  const headers = Object.keys(data[0]);
  const csvRows = [];
  
  // Add headers
  csvRows.push(headers.join(','));
  
  // Add data rows
  for (const row of data) {
    const values = headers.map(header => {
      const value = row[header] || '';
      return `"${String(value).replace(/"/g, '""')}"`;
    });
    csvRows.push(values.join(','));
  }
  
  const blob = new Blob([csvRows.join('\n')], { type: 'text/csv' });
  downloadFile(blob, filename);
};

/**
 * Export data as JSON
 * @param {object|Array} data - Data to export
 * @param {string} filename - Name for JSON file
 */
export const exportToJSON = (data, filename = 'export.json') => {
  const json = JSON.stringify(data, null, 2);
  const blob = new Blob([json], { type: 'application/json' });
  downloadFile(blob, filename);
};

/**
 * Get color based on verdict/status
 * @param {string} verdict - Verdict value (ELIGIBLE, PASS, FAIL, etc.)
 * @returns {object} Color object with main, light, dark properties
 */
export const getVerdictColors = (verdict) => {
  const colors = {
    ELIGIBLE: { main: '#10b981', light: '#d1fae5', dark: '#047857', text: '#065f46' },
    PASS: { main: '#10b981', light: '#d1fae5', dark: '#047857', text: '#065f46' },
    'NOT ELIGIBLE': { main: '#ef4444', light: '#fee2e2', dark: '#b91c1c', text: '#991b1b' },
    FAIL: { main: '#ef4444', light: '#fee2e2', dark: '#b91c1c', text: '#991b1b' },
    'NEEDS REVIEW': { main: '#f59e0b', light: '#fed7aa', dark: '#d97706', text: '#92400e' },
    REVIEW: { main: '#f59e0b', light: '#fed7aa', dark: '#d97706', text: '#92400e' },
    PENDING: { main: '#94a3b8', light: '#e2e8f0', dark: '#64748b', text: '#475569' },
    default: { main: '#6b7280', light: '#e5e7eb', dark: '#4b5563', text: '#374151' },
  };
  return colors[verdict] || colors.default;
};

/**
 * Calculate confidence level from score
 * @param {number} score - Confidence score (0-1)
 * @returns {object} Level object with label and color
 */
export const getConfidenceLevel = (score) => {
  if (score >= 0.9) return { label: 'High', color: '#10b981', icon: '✓' };
  if (score >= 0.7) return { label: 'Medium', color: '#f59e0b', icon: '●' };
  return { label: 'Low', color: '#ef4444', icon: '⚠' };
};

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {boolean} Is valid email
 */
export const isValidEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
};

/**
 * Validate file type against allowed types
 * @param {File} file - File to validate
 * @param {Array} allowedTypes - Array of allowed MIME types
 * @returns {boolean} Is valid file type
 */
export const isValidFileType = (file, allowedTypes = ['application/pdf', 'image/jpeg', 'image/png']) => {
  return allowedTypes.includes(file.type);
};

/**
 * Validate file size
 * @param {File} file - File to validate
 * @param {number} maxSizeMB - Maximum size in MB
 * @returns {boolean} Is valid file size
 */
export const isValidFileSize = (file, maxSizeMB = 20) => {
  return file.size <= maxSizeMB * 1024 * 1024;
};

/**
 * Debounce function for search inputs
 * @param {Function} func - Function to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Debounced function
 */
export const debounce = (func, delay = 300) => {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
};

/**
 * Group array by key
 * @param {Array} array - Array to group
 * @param {string} key - Key to group by
 * @returns {object} Grouped object
 */
export const groupBy = (array, key) => {
  return array.reduce((result, item) => {
    const groupKey = item[key];
    if (!result[groupKey]) {
      result[groupKey] = [];
    }
    result[groupKey].push(item);
    return result;
  }, {});
};

/**
 * Calculate average of numbers
 * @param {Array} numbers - Array of numbers
 * @returns {number} Average value
 */
export const average = (numbers) => {
  if (!numbers || numbers.length === 0) return 0;
  return numbers.reduce((sum, num) => sum + num, 0) / numbers.length;
};

/**
 * Format currency to INR
 * @param {number} amount - Amount to format
 * @param {boolean} showSymbol - Whether to show ₹ symbol
 * @returns {string} Formatted currency
 */
export const formatCurrency = (amount, showSymbol = true) => {
  if (amount === null || amount === undefined) return 'N/A';
  
  const formatter = new Intl.NumberFormat('en-IN', {
    style: showSymbol ? 'currency' : 'decimal',
    currency: 'INR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
  
  return formatter.format(amount);
};

/**
 * Parse number from string (handles crore, lakh, etc.)
 * @param {string} value - Value to parse (e.g., "5 Cr", "10 Lakh")
 * @returns {number} Parsed number
 */
export const parseIndianNumber = (value) => {
  if (typeof value === 'number') return value;
  if (!value) return 0;
  
  const str = String(value).toLowerCase();
  let num = parseFloat(str.replace(/[^0-9.-]/g, ''));
  
  if (str.includes('cr') || str.includes('crore')) {
    num *= 10000000;
  } else if (str.includes('lakh')) {
    num *= 100000;
  }
  
  return isNaN(num) ? 0 : num;
};

/**
 * Get status badge data
 * @param {string} status - Status value
 * @returns {object} Badge data with label and class
 */
export const getStatusBadge = (status) => {
  const badges = {
    SUCCESS: { label: 'Success', class: 'badge-pass' },
    ERROR: { label: 'Error', class: 'badge-fail' },
    PENDING: { label: 'Pending', class: 'badge-pending' },
    PROCESSING: { label: 'Processing', class: 'badge-review' },
    COMPLETED: { label: 'Completed', class: 'badge-pass' },
    FAILED: { label: 'Failed', class: 'badge-fail' },
  };
  return badges[status] || { label: status, class: 'badge-pending' };
};

/**
 * Sleep/delay function
 * @param {number} ms - Milliseconds to sleep
 * @returns {Promise} Promise that resolves after delay
 */
export const sleep = (ms) => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @returns {Promise<boolean>} Success status
 */
export const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    console.error('Failed to copy:', err);
    return false;
  }
};

/**
 * Extract query params from URL
 * @returns {object} Query parameters object
 */
export const getQueryParams = () => {
  const params = new URLSearchParams(window.location.search);
  const result = {};
  for (const [key, value] of params) {
    result[key] = value;
  }
  return result;
};

/**
 * Build URL with query parameters
 * @param {string} baseUrl - Base URL
 * @param {object} params - Query parameters
 * @returns {string} URL with query string
 */
export const buildUrl = (baseUrl, params = {}) => {
  const url = new URL(baseUrl, window.location.origin);
  Object.keys(params).forEach(key => {
    if (params[key] !== null && params[key] !== undefined) {
      url.searchParams.append(key, params[key]);
    }
  });
  return url.toString();
};

/**
 * Check if object is empty
 * @param {object} obj - Object to check
 * @returns {boolean} Is empty
 */
export const isEmptyObject = (obj) => {
  return obj && Object.keys(obj).length === 0 && obj.constructor === Object;
};

/**
 * Capitalize first letter of each word
 * @param {string} str - String to capitalize
 * @returns {string} Capitalized string
 */
export const capitalizeWords = (str) => {
  if (!str) return '';
  return str
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
};

/**
 * Format rule ID for display
 * @param {string} ruleId - Rule ID (e.g., "FIN-001")
 * @returns {string} Formatted rule ID
 */
export const formatRuleId = (ruleId) => {
  if (!ruleId) return '';
  const [category, number] = ruleId.split('-');
  const categoryNames = {
    FIN: 'Financial',
    TECH: 'Technical',
    COMP: 'Compliance',
    CERT: 'Certification',
  };
  return `${categoryNames[category] || category} Rule ${number}`;
};

/**
 * Calculate overall score from criteria results
 * @param {Array} criteria - Array of criteria objects with confidence scores
 * @returns {number} Overall score (0-1)
 */
export const calculateOverallScore = (criteria) => {
  if (!criteria || criteria.length === 0) return 0;
  const totalConfidence = criteria.reduce((sum, c) => sum + (c.confidence || 0), 0);
  return totalConfidence / criteria.length;
};

/**
 * Check if all required criteria are passed
 * @param {Array} criteria - Array of criteria objects
 * @param {Array} requiredRules - Array of required rule IDs
 * @returns {object} Pass status and missing rules
 */
export const checkRequiredCriteria = (criteria, requiredRules = []) => {
  const passedRules = criteria.filter(c => c.result === 'PASS').map(c => c.rule_id);
  const missingRules = requiredRules.filter(rule => !passedRules.includes(rule));
  return {
    allPassed: missingRules.length === 0,
    missingRules,
    passedCount: passedRules.length,
    requiredCount: requiredRules.length,
  };
};

/**
 * Generate random color for charts
 * @param {number} index - Index to generate deterministic color
 * @returns {string} Hex color code
 */
export const getChartColor = (index) => {
  const colors = [
    '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
    '#06b6d4', '#ec4899', '#84cc16', '#f97316', '#6366f1',
  ];
  return colors[index % colors.length];
};

/**
 * Log message with timestamp for debugging
 * @param {string} message - Message to log
 * @param {string} level - Log level (info, warn, error)
 */
export const debugLog = (message, level = 'info') => {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] [GePS] ${message}`;
  
  if (process.env.NODE_ENV === 'development') {
    switch (level) {
      case 'warn':
        console.warn(logMessage);
        break;
      case 'error':
        console.error(logMessage);
        break;
      default:
        console.log(logMessage);
    }
  }
};