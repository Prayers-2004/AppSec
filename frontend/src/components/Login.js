import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  Link,
  Alert,
  Container
} from '@mui/material';
import './Login.css';

const Login = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [attempts, setAttempts] = useState(0);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const response = await axios.post('http://localhost:5000/api/login', formData);
      if (response.data.token) {
        localStorage.setItem('token', response.data.token);
        navigate('/dashboard');
      }
    } catch (err) {
      const errorData = err.response?.data || {};
      setError(errorData.error || 'Login failed');
      
      if (errorData.remaining_attempts !== undefined) {
        setAttempts(3 - errorData.remaining_attempts);
        
        if (errorData.is_last_attempt) {
          setError('This is your last attempt. After this, a security alert will be sent.');
        }
      }
      
      if (err.response?.status === 429) {
        setError('Account locked due to too many failed attempts. A security alert has been sent.');
      }
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8, mb: 4 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom align="center">
            Welcome Back
          </Typography>
          <Typography variant="subtitle1" gutterBottom align="center" color="text.secondary">
            Please login to your account
          </Typography>
          
          {error && (
            <Alert severity={attempts >= 2 ? "warning" : "error"} sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              margin="normal"
              required
              placeholder="Enter your username"
            />
            
            <TextField
              fullWidth
              label="Password"
              name="password"
              type="password"
              value={formData.password}
              onChange={handleChange}
              margin="normal"
              required
              placeholder="Enter your password"
            />
            
            <Button
              fullWidth
              type="submit"
              variant="contained"
              color="primary"
              size="large"
              sx={{ mt: 3, mb: 2 }}
            >
              Login
            </Button>

            <Box sx={{ textAlign: 'center', mt: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Don't have an account?{' '}
                <Link component={RouterLink} to="/register" color="primary">
                  Register here
                </Link>
              </Typography>
            </Box>
          </form>
          
          {attempts > 0 && (
            <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 2 }}>
              Attempts remaining: {3 - attempts}
            </Typography>
          )}
        </Paper>
      </Box>
    </Container>
  );
};

export default Login; 