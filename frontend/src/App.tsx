import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import './App.css';
import Dashboard from './pages/Dashboard';
import Configuration from './pages/Configuration';
import TradingActions from './pages/TradingActions';
import Login from './pages/Login';
import AIChat from './pages/AIChat';
import { isAuthenticated } from './api';

// Protected route component
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

const App: React.FC = () => {
  return (
    <Router>
      <div className="App">
        <header className="App-header">
          <h1>PerplexityTrader</h1>
          {isAuthenticated() && (
            <nav>
              <ul className="nav-menu">
                <li><Link to="/dashboard">Dashboard</Link></li>
                <li><Link to="/configuration">Configuration</Link></li>
                <li><Link to="/trading">Trading Actions</Link></li>
                <li><Link to="/ai-chat">AI Chat</Link></li>
                <li><button onClick={() => {
                  localStorage.removeItem('token');
                  localStorage.removeItem('user');
                  window.location.href = '/login';
                }}>Logout</button></li>
              </ul>
            </nav>
          )}
        </header>
        
        <main>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="/configuration" element={
              <ProtectedRoute>
                <Configuration />
              </ProtectedRoute>
            } />
            <Route path="/trading" element={
              <ProtectedRoute>
                <TradingActions />
              </ProtectedRoute>
            } />
            <Route path="/ai-chat" element={
              <ProtectedRoute>
                <AIChat />
              </ProtectedRoute>  
            } />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
};

export default App;
