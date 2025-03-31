import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  Chip,
  CircularProgress,
  Alert
} from '@mui/material';

const AppMonitor = () => {
  const [processName, setProcessName] = useState('');
  const [monitoredApps, setMonitoredApps] = useState([]);
  const [logs, setLogs] = useState([]);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      const response = await axios.get('/api/monitor/logs');
      setLogs(response.data);
    } catch (err) {
      setError('Failed to fetch monitoring logs');
    }
  };

  const handleStartMonitoring = async () => {
    if (!processName.trim()) {
      setError('Please enter a process name');
      return;
    }

    setLoading(true);
    try {
      await axios.post('/api/monitor/start', {
        process_names: [processName.trim()]
      });
      setMonitoredApps([...monitoredApps, processName.trim()]);
      setIsMonitoring(true);
      setError('');
    } catch (err) {
      setError('Failed to start monitoring');
    } finally {
      setLoading(false);
    }
  };

  const handleStopMonitoring = async () => {
    setLoading(true);
    try {
      await axios.post('/api/monitor/stop');
      setMonitoredApps([]);
      setIsMonitoring(false);
      setError('');
    } catch (err) {
      setError('Failed to stop monitoring');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Application Monitor
      </Typography>

      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2 }}>
          <TextField
            label="Process Name"
            value={processName}
            onChange={(e) => setProcessName(e.target.value)}
            placeholder="e.g., notepad.exe"
            disabled={isMonitoring}
          />
          <Button
            variant="contained"
            color="primary"
            onClick={handleStartMonitoring}
            disabled={isMonitoring || loading}
          >
            Start Monitoring
          </Button>
          <Button
            variant="contained"
            color="secondary"
            onClick={handleStopMonitoring}
            disabled={!isMonitoring || loading}
          >
            Stop Monitoring
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {monitoredApps.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle1" gutterBottom>
              Currently Monitored Applications:
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              {monitoredApps.map((app) => (
                <Chip key={app} label={app} color="primary" />
              ))}
            </Box>
          </Box>
        )}
      </Paper>

      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Monitoring Logs
        </Typography>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : (
          <List>
            {logs.map((log, index) => (
              <ListItem key={index} divider>
                <ListItemText
                  primary={log.window_info.window_title}
                  secondary={
                    <>
                      <Typography component="span" variant="body2">
                        Process: {log.window_info.process_name}
                      </Typography>
                      <br />
                      <Typography component="span" variant="body2">
                        Time: {new Date(log.timestamp).toLocaleString()}
                      </Typography>
                    </>
                  }
                />
              </ListItem>
            ))}
            {logs.length === 0 && (
              <ListItem>
                <ListItemText primary="No monitoring logs available" />
              </ListItem>
            )}
          </List>
        )}
      </Paper>
    </Box>
  );
};

export default AppMonitor; 