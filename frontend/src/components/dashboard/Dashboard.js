import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Box,
  CircularProgress
} from '@mui/material';
import {
  Security as SecurityIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  AccessTime as AccessTimeIcon
} from '@mui/icons-material';
import axios from 'axios';

function Dashboard() {
  const [stats, setStats] = useState({
    totalApplications: 0,
    protectedApplications: 0,
    recentAttempts: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const response = await axios.get('/api/applications/stats');
        setStats(response.data);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Grid container spacing={3}>
      {/* Statistics Cards */}
      <Grid item xs={12} md={4}>
        <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 140 }}>
          <Typography component="h2" variant="h6" color="primary" gutterBottom>
            Total Applications
          </Typography>
          <Typography component="p" variant="h4">
            {stats.totalApplications}
          </Typography>
        </Paper>
      </Grid>
      <Grid item xs={12} md={4}>
        <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 140 }}>
          <Typography component="h2" variant="h6" color="primary" gutterBottom>
            Protected Applications
          </Typography>
          <Typography component="p" variant="h4">
            {stats.protectedApplications}
          </Typography>
        </Paper>
      </Grid>
      <Grid item xs={12} md={4}>
        <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 140 }}>
          <Typography component="h2" variant="h6" color="primary" gutterBottom>
            Security Status
          </Typography>
          <Typography component="p" variant="h4" color="success.main">
            Active
          </Typography>
        </Paper>
      </Grid>

      {/* Recent Activity */}
      <Grid item xs={12}>
        <Paper sx={{ p: 2 }}>
          <Typography component="h2" variant="h6" color="primary" gutterBottom>
            Recent Activity
          </Typography>
          <List>
            {stats.recentAttempts.map((attempt, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  {attempt.success ? (
                    <CheckCircleIcon color="success" />
                  ) : (
                    <WarningIcon color="error" />
                  )}
                </ListItemIcon>
                <ListItemText
                  primary={`${attempt.application_name} - ${attempt.success ? 'Successful' : 'Failed'} Access`}
                  secondary={`${attempt.timestamp} - ${attempt.location}`}
                />
              </ListItem>
            ))}
            {stats.recentAttempts.length === 0 && (
              <ListItem>
                <ListItemIcon>
                  <AccessTimeIcon />
                </ListItemIcon>
                <ListItemText primary="No recent activity" />
              </ListItem>
            )}
          </List>
        </Paper>
      </Grid>
    </Grid>
  );
}

export default Dashboard; 