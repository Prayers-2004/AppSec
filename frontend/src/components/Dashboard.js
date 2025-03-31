import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Dashboard.css';

const Dashboard = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <div className="dashboard-container">
      <nav className="dashboard-nav">
        <h1>Dashboard</h1>
        <button onClick={handleLogout} className="logout-button">
          Logout
        </button>
      </nav>
      
      <div className="dashboard-content">
        <h2>Welcome to your Dashboard</h2>
        <p>You have successfully logged in!</p>
        
        <div className="dashboard-cards">
          <div className="card">
            <h3>Profile</h3>
            <p>View and edit your profile information</p>
          </div>
          
          <div className="card">
            <h3>Settings</h3>
            <p>Configure your application settings</p>
          </div>
          
          <div className="card">
            <h3>Security</h3>
            <p>Manage your security preferences</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 