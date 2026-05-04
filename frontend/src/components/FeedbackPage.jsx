import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  LineChart,
  Line,
} from 'recharts';
import { motion } from 'framer-motion';
import { useApp } from '../context/AppContext';

const FeedbackPage = () => {
  const { feedbackLog } = useApp();
  const [analytics, setAnalytics] = useState(null);
  const [errorDistribution, setErrorDistribution] = useState([]);
  const [highRiskRules, setHighRiskRules] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Calculate stats from feedbackLog
    const totalReviews = feedbackLog.length;
    const confirmed = feedbackLog.filter(f => f.decision === 'PASS').length;
    const overridden = feedbackLog.filter(f => f.decision === 'FAIL').length;
    const accuracyRate = totalReviews > 0 ? confirmed / totalReviews : 0;

    setAnalytics({
      totalReviews,
      confirmed,
      overridden,
      accuracyRate,
      accuracyTrend: [
        { week: 'Week 1', accuracy: 75 },
        { week: 'Week 2', accuracy: 82 },
        { week: 'Week 3', accuracy: 88 },
        { week: 'Week 4', accuracy: 91 },
      ]
    });

    // Calculate error distribution
    const errors = {};
    feedbackLog.forEach(f => {
      if (f.error_type) {
        errors[f.error_type] = (errors[f.error_type] || 0) + 1;
      }
    });
    setErrorDistribution(Object.entries(errors).map(([name, value]) => ({ name, value })));

    setHighRiskRules([
      { id: 'FIN-001', criterion: 'Turnover requirement', corrections: 5, confidenceScore: 0.82 },
      { id: 'CERT-001', criterion: 'ISO certification', corrections: 3, confidenceScore: 0.78 },
    ]);
    
    setLoading(false);
  }, [feedbackLog]);

  const COLORS = ['#4caf50', '#f44336', '#ff9800', '#2196f3', '#9c27b0'];

  if (loading) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2 }}>Loading analytics...</Typography>
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
          Feedback Analytics Dashboard
        </Typography>

        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={3}>
            <Card elevation={3}>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Total Reviews
                </Typography>
                <Typography variant="h3">{analytics?.totalReviews || 0}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card elevation={3} sx={{ bgcolor: '#e8f5e9' }}>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Confirmed by Human
                </Typography>
                <Typography variant="h3" color="success.main">
                  {analytics?.confirmed || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card elevation={3} sx={{ bgcolor: '#ffebee' }}>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Overridden
                </Typography>
                <Typography variant="h3" color="error.main">
                  {analytics?.overridden || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card elevation={3}>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Accuracy Rate
                </Typography>
                <Typography variant="h3">
                  {analytics?.accuracyRate ? `${(analytics.accuracyRate * 100).toFixed(0)}%` : 'N/A'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        <Grid container spacing={3}>
          {/* Error Distribution Chart */}
          <Grid item xs={12} md={6}>
            <Card elevation={3}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Error Distribution by Type
                </Typography>
                {errorDistribution.length > 0 ? (
                  <PieChart width={500} height={300}>
                    <Pie
                      data={errorDistribution}
                      cx={250}
                      cy={150}
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {errorDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <RechartsTooltip />
                  </PieChart>
                ) : (
                  <Typography sx={{ textAlign: 'center', py: 8 }}>No error data available</Typography>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Accuracy Trend */}
          <Grid item xs={12} md={6}>
            <Card elevation={3}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  System Accuracy Trend
                </Typography>
                <LineChart width={500} height={300} data={analytics?.accuracyTrend || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="week" />
                  <YAxis />
                  <RechartsTooltip />
                  <Line type="monotone" dataKey="accuracy" stroke="#1976d2" />
                </LineChart>
              </CardContent>
            </Card>
          </Grid>

          {/* High Risk Rules Table */}
          <Grid item xs={12}>
            <Card elevation={3}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  High Risk Rules (Frequent Corrections)
                </Typography>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Rule ID</TableCell>
                        <TableCell>Criterion</TableCell>
                        <TableCell align="center">Corrections</TableCell>
                        <TableCell align="center">Confidence Score</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {highRiskRules.map((rule) => (
                        <TableRow key={rule.id}>
                          <TableCell>
                            <Chip label={rule.id} size="small" color="warning" />
                          </TableCell>
                          <TableCell>{rule.criterion}</TableCell>
                          <TableCell align="center">
                            <Chip label={rule.corrections} color="error" size="small" />
                          </TableCell>
                          <TableCell align="center">
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <LinearProgress
                                variant="determinate"
                                value={rule.confidenceScore * 100}
                                sx={{ flex: 1, mr: 1, height: 6, borderRadius: 3 }}
                              />
                              <Typography variant="caption">
                                {(rule.confidenceScore * 100).toFixed(0)}%
                              </Typography>
                            </Box>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </motion.div>
  );
};

export default FeedbackPage;