import React from 'react';
import './App.css';
import Dashboard from './pages/Dashboard';
import Configuration from './pages/Configuration';
import TradingActions from './pages/TradingActions';

const App: React.FC = () => {
  return (
    <div className="App">
      <h1>PerplexityTrader Frontend</h1>
      <Dashboard />
      <Configuration />
      <TradingActions />
    </div>
  );
}

export default App;
