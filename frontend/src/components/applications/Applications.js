import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  Paper,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  IconButton,
  Alert
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Security as SecurityIcon
} from '@mui/icons-material';
import axios from 'axios';

function Applications() {
  const [applications, setApplications] = useState([]);
  const [open, setOpen] = useState(false);
  const [editingApp, setEditingApp] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    path: '',
    is_protected: true
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchApplications();
  }, []);

  const fetchApplications = async () => {
    try {
      const response = await axios.get('/api/applications');
      setApplications(response.data);
    } catch (error) {
      setError('Failed to fetch applications');
    }
  };

  const handleOpen = (app = null) => {
    if (app) {
      setEditingApp(app);
      setFormData({
        name: app.name,
        path: app.path,
        is_protected: app.is_protected
      });
    } else {
      setEditingApp(null);
      setFormData({
        name: '',
        path: '',
        is_protected: true
      });
    }
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setEditingApp(null);
    setFormData({
      name: '',
      path: '',
      is_protected: true
    });
  };

  const handleChange = (e) => {
    const { name, value, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'is_protected' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingApp) {
        await axios.put(`/api/applications/${editingApp.id}`, formData);
        setSuccess('Application updated successfully');
      } else {
        await axios.post('/api/applications', formData);
        setSuccess('Application added successfully');
      }
      handleClose();
      fetchApplications();
    } catch (error) {
      setError(error.response?.data?.error || 'Operation failed');
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this application?')) {
      try {
        await axios.delete(`/api/applications/${id}`);
        setSuccess('Application deleted successfully');
        fetchApplications();
      } catch (error) {
        setError('Failed to delete application');
      }
    }
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" component="h1">
          Protected Applications
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpen()}
        >
          Add Application
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Path</TableCell>
              <TableCell>Protected</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {applications.map((app) => (
              <TableRow key={app.id}>
                <TableCell>{app.name}</TableCell>
                <TableCell>{app.path}</TableCell>
                <TableCell>
                  <Switch
                    checked={app.is_protected}
                    onChange={() => handleOpen(app)}
                    color="primary"
                  />
                </TableCell>
                <TableCell>
                  <IconButton onClick={() => handleOpen(app)}>
                    <EditIcon />
                  </IconButton>
                  <IconButton onClick={() => handleDelete(app.id)}>
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={open} onClose={handleClose}>
        <DialogTitle>
          {editingApp ? 'Edit Application' : 'Add New Application'}
        </DialogTitle>
        <form onSubmit={handleSubmit}>
          <DialogContent>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Application Name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Application Path"
                  name="path"
                  value={formData.path}
                  onChange={handleChange}
                  required
                />
              </Grid>
              <Grid item xs={12}>
                <Box display="flex" alignItems="center">
                  <Switch
                    checked={formData.is_protected}
                    onChange={handleChange}
                    name="is_protected"
                    color="primary"
                  />
                  <Typography>Protect this application</Typography>
                </Box>
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleClose}>Cancel</Button>
            <Button type="submit" variant="contained" color="primary">
              {editingApp ? 'Update' : 'Add'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  );
}

export default Applications; 