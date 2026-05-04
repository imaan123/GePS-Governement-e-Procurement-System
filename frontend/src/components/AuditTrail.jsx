import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  TextField,
  InputAdornment,
  Button,
  LinearProgress,
  Tooltip,
} from '@mui/material';
import {
  Search as SearchIcon,
  Download as DownloadIcon,
  Visibility as VisibilityIcon,
  FilterList as FilterListIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { getAuditLogs, exportAuditReport } from '../services/api';
import toast from 'react-hot-toast';

const AuditTrail = ({ tenderId }) => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadAuditLogs();
  }, [tenderId]);

  const loadAuditLogs = async () => {
    try {
      const data = await getAuditLogs(tenderId);
      setLogs(data);
    } catch (error) {
      console.error('Error loading audit logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    try {
      const report = await exportAuditReport(tenderId, format);
      toast.success(`Report exported as ${format.toUpperCase()}`);
    } catch (error) {
      toast.error('Failed to export report');
    }
  };

  const getActionIcon = (action) => {
    switch(action) {
      case 'EVALUATION': return <CheckCircleIcon fontSize="small" color="success" />;
      case 'HUMAN_REVIEW': return <VisibilityIcon fontSize="small" color="primary" />;
      case 'OVERRIDE': return <WarningIcon fontSize="small" color="warning" />;
      default: return <ErrorIcon fontSize="small" />;
    }
  };

  const filteredLogs = logs.filter(log => {
    const matchesSearch = 
      log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.userId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.details.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filter === 'all' || log.action === filter;
    return matchesSearch && matchesFilter;
  });

  if (loading) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2 }}>Loading audit trail...</Typography>
      </Box>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <Box sx={{ maxWidth: 1400, mx: 'auto' }}>
        <Typography variant="h4" gutterBottom align="center" sx={{ mb: 4, color: '#fff' }}>
          Audit Trail
        </Typography>

        <Paper elevation={3} sx={{ p: 3 }}>
          {/* Filters */}
          <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
            <TextField
              size="small"
              placeholder="Search logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
              sx={{ flex: 1, minWidth: 200 }}
            />
            
            <Button
              variant={filter === 'all' ? 'contained' : 'outlined'}
              onClick={() => setFilter('all')}
              size="small"
            >
              All
            </Button>
            <Button
              variant={filter === 'EVALUATION' ? 'contained' : 'outlined'}
              onClick={() => setFilter('EVALUATION')}
              size="small"
              color="success"
            >
              Evaluations
            </Button>
            <Button
              variant={filter === 'HUMAN_REVIEW' ? 'contained' : 'outlined'}
              onClick={() => setFilter('HUMAN_REVIEW')}
              size="small"
              color="primary"
            >
              Human Reviews
            </Button>
            <Button
              variant={filter === 'OVERRIDE' ? 'contained' : 'outlined'}
              onClick={() => setFilter('OVERRIDE')}
              size="small"
              color="warning"
            >
              Overrides
            </Button>
            
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={() => handleExport('json')}
              sx={{ ml: 'auto' }}
            >
              Export JSON
            </Button>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={() => handleExport('csv')}
            >
              Export CSV
            </Button>
          </Box>

          {/* Audit Logs Table */}
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                  <TableCell>Timestamp</TableCell>
                  <TableCell>Actor</TableCell>
                  <TableCell>Action Type</TableCell>
                  <TableCell>Details</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredLogs.map((log, idx) => (
                  <TableRow key={idx} hover>
                    <TableCell>
                      <Typography variant="caption">
                        {new Date(log.timestamp).toLocaleString()}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        icon={getActionIcon(log.action)}
                        label={log.userId}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={log.action.replace('_', ' ')}
                        size="small"
                        color={log.action === 'EVALUATION' ? 'success' : log.action === 'HUMAN_REVIEW' ? 'primary' : 'warning'}
                      />
                    </TableCell>
                    <TableCell>
                      <Tooltip title={log.details}>
                        <Typography variant="body2" sx={{ maxWidth: 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {log.details}
                        </Typography>
                      </Tooltip>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={log.status}
                        size="small"
                        color={log.status === 'SUCCESS' ? 'success' : 'error'}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {filteredLogs.length === 0 && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography color="textSecondary">No audit logs found</Typography>
            </Box>
          )}

          {/* Summary Stats */}
          <Box sx={{ mt: 3, pt: 2, borderTop: 1, borderColor: 'divider' }}>
            <Typography variant="caption" color="textSecondary">
              Total Entries: {filteredLogs.length} | 
              Last Updated: {logs.length > 0 ? new Date(logs[0].timestamp).toLocaleString() : 'N/A'}
            </Typography>
          </Box>
        </Paper>
      </Box>
    </motion.div>
  );
};

export default AuditTrail;