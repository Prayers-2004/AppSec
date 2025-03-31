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
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Chip,
  CircularProgress,
  Snackbar,
  Autocomplete,
  InputAdornment
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import SearchIcon from '@mui/icons-material/Search';
import RefreshIcon from '@mui/icons-material/Refresh';

const WindowsAppMonitor = () => {
  const [monitoredApps, setMonitoredApps] = useState([]);
  const [runningApps, setRunningApps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const [loginDialog, setLoginDialog] = useState(false);
  const [loginCredentials, setLoginCredentials] = useState({ username: '', password: '' });
  const [currentApp, setCurrentApp] = useState(null);
  const [newApp, setNewApp] = useState({ app_name: '', process_name: '' });
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [notificationCheckInterval, setNotificationCheckInterval] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [lastNotificationId, setLastNotificationId] = useState(null);
  const [remainingAttempts, setRemainingAttempts] = useState(3);
  const [loginError, setLoginError] = useState('');

  // Create axios instance with base URL
  const api = axios.create({
    baseURL: 'http://localhost:5000'
  });

  // Add request interceptor to include auth token
  api.interceptors.request.use(config => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  const fetchMonitoredApps = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setSnackbar({
          open: true,
          message: 'Please login to view monitored applications',
          severity: 'warning'
        });
        return;
      }

      const response = await api.get('/api/monitor/windows-apps', {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (Array.isArray(response.data)) {
        setMonitoredApps(response.data);
      } else {
        console.error('Invalid response format:', response.data);
        setError('Invalid response format from server');
      }
    } catch (error) {
      console.error('Error fetching monitored apps:', error);
      setError(error.response?.data?.error || 'Failed to fetch monitored applications');
      setSnackbar({
        open: true,
        message: error.response?.data?.error || 'Failed to fetch monitored applications',
        severity: 'error'
      });
    }
  };

  const fetchRunningApps = async () => {
    try {
      setLoading(true);
      setError(null); // Clear any previous errors
      
      // Check if we have a token
      const token = localStorage.getItem('token');
      if (!token) {
        setSnackbar({
          open: true,
          message: 'Please login first to view running applications',
          severity: 'warning'
        });
        return;
      }

      // Make the API call with explicit headers
      const response = await axios.get('http://localhost:5000/api/monitor/running-apps', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      });

      // Check if we got a valid response
      if (response.status === 200 && Array.isArray(response.data)) {
        setRunningApps(response.data);
        if (response.data.length === 0) {
          setSnackbar({
            open: true,
            message: 'No running applications found',
            severity: 'info'
          });
        }
      } else {
        throw new Error('Invalid response format from server');
      }
    } catch (error) {
      console.error('Error fetching running apps:', error);
      const errorMessage = error.response?.data?.error || error.message || 'Failed to fetch running applications';
      setError(errorMessage);
      setSnackbar({
        open: true,
        message: errorMessage,
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const checkForLoginRequired = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;  // Don't check if not logged in
      
      const response = await api.get('/api/notifications', {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data && response.data.length > 0) {
        const notification = response.data[0];
        if (notification.type === 'login_required' && 
            notification.id !== lastNotificationId && 
            !loginDialog) {
          setCurrentApp(notification.data);
          setLastNotificationId(notification.id);
          setLoginDialog(true);
        }
      }
    } catch (error) {
      // Just log the error, don't try to auto-login
      console.error('Error checking for notifications:', error);
    }
  };

  const handleAddApp = async () => {
    if (!newApp.app_name || !newApp.process_name) {
      setSnackbar({
        open: true,
        message: 'Please select an application',
        severity: 'error'
      });
      return;
    }

    try {
      const response = await api.post('/api/monitor/windows-apps', newApp);
      if (response.data.message) {
        setSnackbar({
          open: true,
          message: response.data.message,
          severity: 'success'
        });
        setNewApp({ app_name: '', process_name: '' });
        fetchMonitoredApps();
      }
    } catch (error) {
      console.error('Error adding app:', error);
      setSnackbar({
        open: true,
        message: error.response?.data?.error || 'Failed to add application',
        severity: 'error'
      });
    }
  };

  const handleRemoveApp = async (appName) => {
    try {
      const response = await api.delete(`/api/monitor/windows-apps/${appName}`);
      if (response.data.message) {
        setSnackbar({
          open: true,
          message: response.data.message,
          severity: 'success'
        });
        fetchMonitoredApps();
      }
    } catch (error) {
      console.error('Error removing app:', error);
      setSnackbar({
        open: true,
        message: error.response?.data?.error || 'Failed to remove application',
        severity: 'error'
      });
    }
  };

  const handleStartMonitoring = async () => {
    try {
      const response = await api.post('/api/monitor/windows-apps/start');
      if (response.data.message) {
        setIsMonitoring(true);
        setSnackbar({
          open: true,
          message: response.data.message,
          severity: 'success'
        });
      }
    } catch (error) {
      console.error('Error starting monitoring:', error);
      setSnackbar({
        open: true,
        message: error.response?.data?.error || 'Failed to start monitoring',
        severity: 'error'
      });
    }
  };

  const handleStopMonitoring = async () => {
    try {
      const response = await api.post('/api/monitor/windows-apps/stop');
      if (response.data.message) {
        setIsMonitoring(false);
        setSnackbar({
          open: true,
          message: response.data.message,
          severity: 'success'
        });
      }
    } catch (error) {
      console.error('Error stopping monitoring:', error);
      setSnackbar({
        open: true,
        message: error.response?.data?.error || 'Failed to stop monitoring',
        severity: 'error'
      });
    }
  };

  const handleLogin = async () => {
    try {
      const response = await api.post('/api/auth/login', loginCredentials);
      if (response.data.token) {
        localStorage.setItem('token', response.data.token);
        setLoginDialog(false);
        setLoginCredentials({ username: '', password: '' });
        setRemainingAttempts(3); // Reset attempts on successful login
        setLoginError('');
        setSnackbar({
          open: true,
          message: 'Login successful',
          severity: 'success'
        });
        
        // Notify backend about successful login
        if (currentApp) {
          await api.post('/api/monitor/windows-apps/login-success', {
            app_name: currentApp.app_name
          });
        }
      }
    } catch (error) {
      console.error('Login error:', error);
      
      // Update remaining attempts
      setRemainingAttempts(prev => {
        const newAttempts = prev - 1;
        if (newAttempts === 0) {
          // Handle max attempts reached
          handleMaxAttemptsReached();
        } else if (newAttempts === 1) {
          setLoginError('This is your last attempt. After this, a security alert will be sent.');
          // Notify backend about failed login
          if (currentApp) {
            api.post('/api/monitor/windows-apps/login-failed', {
              app_name: currentApp.app_name,
              username: loginCredentials.username
            });
          }
        } else {
          setLoginError(`Invalid credentials. ${newAttempts} attempts remaining.`);
          // Notify backend about failed login
          if (currentApp) {
            api.post('/api/monitor/windows-apps/login-failed', {
              app_name: currentApp.app_name,
              username: loginCredentials.username
            });
          }
        }
        return newAttempts;
      });
    }
  };

  // Function to handle max attempts reached
  const handleMaxAttemptsReached = async () => {
    try {
      // First capture both screenshot and camera image
      const [screenshot, cameraImage] = await Promise.all([
        captureScreenshot(),
        captureCameraImage()
      ]);

      console.log('Screenshot captured:', !!screenshot);
      console.log('Camera image captured:', !!cameraImage);
      
      // Send failed login with security data
      await api.post('/api/monitor/windows-apps/login-failed', {
        app_name: currentApp?.app_name,
        username: loginCredentials.username,
        screenshot: screenshot,
        camera_image: cameraImage,
        max_attempts_reached: true
      });
      
      setLoginError('Account locked due to too many failed attempts. A security alert has been sent.');
    } catch (error) {
      console.error('Error handling max attempts:', error);
      setLoginError('Account locked. Error sending security alert.');
    }
  };

  // Function to capture screenshot using html2canvas
  const captureScreenshot = async () => {
    try {
      const html2canvas = (await import('html2canvas')).default;
      const canvas = await html2canvas(document.body);
      const dataUrl = canvas.toDataURL('image/png');
      console.log('Screenshot captured successfully');
      return dataUrl;
    } catch (error) {
      console.error('Error capturing screenshot:', error);
      return null;
    }
  };

  // Function to capture camera image
  const captureCameraImage = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          width: 1280,
          height: 720,
          facingMode: 'user'
        } 
      });
      
      const video = document.createElement('video');
      video.srcObject = stream;
      
      // Wait for video to be ready
      await new Promise((resolve) => {
        video.onloadedmetadata = () => {
          video.play();
          resolve();
        };
      });

      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      // Draw the video frame to canvas
      canvas.getContext('2d').drawImage(video, 0, 0);

      // Stop camera stream
      stream.getTracks().forEach(track => track.stop());
      
      const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
      console.log('Camera image captured successfully');
      return dataUrl;
    } catch (error) {
      console.error('Error capturing camera image:', error);
      return null;
    }
  };

  const handleCloseLoginDialog = () => {
    setLoginDialog(false);
    setLoginCredentials({ username: '', password: '' });
    setCurrentApp(null);
  };

  const handleAppSelect = (event, value) => {
    if (value) {
      setNewApp({
        app_name: value.name,
        process_name: value.process_name
      });
    } else {
      setNewApp({ app_name: '', process_name: '' });
    }
  };

  const handleQuickAdd = (appName, processName) => {
    setNewApp({
      app_name: appName,
      process_name: processName
    });
    setOpenDialog(true);
  };

  useEffect(() => {
    const initializeData = async () => {
      await fetchMonitoredApps();
      await fetchRunningApps();
    };
    
    initializeData();
    
    // Set up notification checking with a longer interval (10 seconds)
    const interval = setInterval(checkForLoginRequired, 10000);
    setNotificationCheckInterval(interval);
    
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, []);

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Windows Application Monitor
      </Typography>

      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2 }}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleStartMonitoring}
            disabled={isMonitoring || loading || monitoredApps.length === 0}
            startIcon={<AddIcon />}
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
          <Button
            variant="outlined"
            onClick={() => setOpenDialog(true)}
            startIcon={<AddIcon />}
          >
            Add Application
          </Button>
        </Box>

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
            <CircularProgress />
          </Box>
        )}

        <List>
          {monitoredApps.map((app, index) => (
            <ListItem key={index} divider>
              <ListItemText
                primary={app.app_name}
                secondary={`Process: ${app.process_name}`}
              />
              <ListItemSecondaryAction>
                <IconButton 
                  edge="end" 
                  aria-label="delete"
                  onClick={() => handleRemoveApp(app.app_name)}
                >
                  <DeleteIcon />
                </IconButton>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
          {monitoredApps.length === 0 && (
            <ListItem>
              <ListItemText primary="No applications being monitored" />
            </ListItem>
          )}
        </List>
      </Paper>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Application to Monitor</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Typography variant="subtitle1" sx={{ flexGrow: 1 }}>
              Select a running application
            </Typography>
            <IconButton onClick={fetchRunningApps} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Box>
          <Autocomplete
            options={runningApps}
            getOptionLabel={(option) => option.name}
            onChange={handleAppSelect}
            loading={loading}
            renderInput={(params) => (
              <TextField
                {...params}
                autoFocus
                margin="dense"
                label="Search Applications"
                fullWidth
                InputProps={{
                  ...params.InputProps,
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
                helperText="Type to search for running applications"
              />
            )}
            renderOption={(props, option) => (
              <li {...props}>
                {option.name} ({option.process_name})
              </li>
            )}
            sx={{ mt: 2 }}
          />
          {newApp.app_name && (
            <TextField
              margin="dense"
              label="Application Name"
              fullWidth
              value={newApp.app_name}
              onChange={(e) => setNewApp({ ...newApp, app_name: e.target.value })}
              helperText="You can modify the application name if needed"
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleAddApp} 
            variant="contained"
            disabled={!newApp.app_name || !newApp.process_name}
          >
            Add
          </Button>
        </DialogActions>
      </Dialog>

      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Common Applications
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Chip 
            label="WhatsApp" 
            onClick={() => handleQuickAdd('WhatsApp', 'WhatsApp.exe')} 
          />
          <Chip 
            label="VS Code" 
            onClick={() => handleQuickAdd('VS Code', 'code.exe')} 
          />
          <Chip 
            label="Facebook" 
            onClick={() => handleQuickAdd('Facebook', 'chrome.exe')} 
          />
          <Chip 
            label="File Explorer" 
            onClick={() => handleQuickAdd('File Explorer', 'explorer.exe')} 
          />
        </Box>
      </Paper>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setSnackbar({ ...snackbar, open: false })} severity={snackbar.severity}>
          {snackbar.message}
        </Alert>
      </Snackbar>

      <Dialog 
        open={loginDialog} 
        onClose={handleCloseLoginDialog}
        maxWidth="sm" 
        fullWidth
        disableEscapeKeyDown
        disableBackdropClick
      >
        <DialogTitle>Login Required</DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Please login to continue using {currentApp?.app_name}
          </Typography>
          {loginError && (
            <Alert severity={remainingAttempts <= 1 ? "warning" : "error"} sx={{ mb: 2 }}>
              {loginError}
            </Alert>
          )}
          <TextField
            autoFocus
            margin="dense"
            label="Username"
            fullWidth
            value={loginCredentials.username}
            onChange={(e) => setLoginCredentials({ ...loginCredentials, username: e.target.value })}
          />
          <TextField
            margin="dense"
            label="Password"
            type="password"
            fullWidth
            value={loginCredentials.password}
            onChange={(e) => setLoginCredentials({ ...loginCredentials, password: e.target.value })}
          />
          {remainingAttempts < 3 && (
            <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 2 }}>
              Attempts remaining: {remainingAttempts}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseLoginDialog}>Cancel</Button>
          <Button 
            onClick={handleLogin} 
            variant="contained"
            disabled={!loginCredentials.username || !loginCredentials.password || remainingAttempts <= 0}
          >
            Login
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default WindowsAppMonitor; 