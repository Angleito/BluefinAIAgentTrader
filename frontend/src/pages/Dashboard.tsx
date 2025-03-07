import React, { useState, useEffect } from 'react';
import { getAgentStatus, getOpenPositions, getRecentTrades, subscribeToEvent } from '../api';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface Trade {
  id: string;
  symbol: string;
  side: string;
  entry_price: number;
  exit_price: number;
  profit_loss: number;
  timestamp: string;
}

interface Position {
  id: string;
  symbol: string;
  side: string;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  timestamp: string;
}

const Dashboard: React.FC = () => {
  const [status, setStatus] = useState<any>({});
  const [positions, setPositions] = useState<Position[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch initial data
    const fetchData = async () => {
      try {
        setLoading(true);
        const statusData = await getAgentStatus();
        const positionsData = await getOpenPositions();
        const tradesData = await getRecentTrades(10);
        
        setStatus(statusData);
        setPositions(positionsData.positions || []);
        setTrades(tradesData.trades || []);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
    
    // Subscribe to real-time updates
    const unsubscribeStatus = subscribeToEvent('status_update', (data) => {
      setStatus(data);
    });
    
    const unsubscribePositions = subscribeToEvent('positions_update', (data) => {
      setPositions(data.positions || []);
    });
    
    const unsubscribeTrades = subscribeToEvent('trades_update', (data) => {
      setTrades(data.trades || []);
    });
    
    // Cleanup subscriptions on unmount
    return () => {
      if (unsubscribeStatus) unsubscribeStatus();
      if (unsubscribePositions) unsubscribePositions();
      if (unsubscribeTrades) unsubscribeTrades();
    };
  }, []);

  // Prepare chart data
  const chartData = {
    labels: trades.map(trade => new Date(trade.timestamp).toLocaleDateString()),
    datasets: [
      {
        label: 'Profit/Loss',
        data: trades.map(trade => trade.profit_loss),
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.5)',
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Recent Trading Performance',
      },
    },
  };

  if (loading) {
    return <div>Loading dashboard data...</div>;
  }

  return (
    <div className="dashboard">
      <h1>Trading Dashboard</h1>
      
      <div className="status-card">
        <h2>Agent Status</h2>
        <div className="status-details">
          <p>Status: <span className={`status-${status.status?.toLowerCase()}`}>{status.status}</span></p>
          <p>Balance: ${status.balance?.toFixed(2)}</p>
          <p>Active Since: {new Date(status.active_since).toLocaleString()}</p>
          <p>Open Positions: {positions.length}</p>
        </div>
      </div>
      
      <div className="chart-container">
        <Line options={chartOptions} data={chartData} />
      </div>
      
      <div className="positions-section">
        <h2>Open Positions</h2>
        {positions.length === 0 ? (
          <p>No open positions</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Side</th>
                <th>Entry Price</th>
                <th>Current Price</th>
                <th>Unrealized P/L</th>
                <th>Open Time</th>
              </tr>
            </thead>
            <tbody>
              {positions.map(position => (
                <tr key={position.id}>
                  <td>{position.symbol}</td>
                  <td className={position.side.toLowerCase() === 'buy' ? 'green' : 'red'}>
                    {position.side}
                  </td>
                  <td>${position.entry_price.toFixed(2)}</td>
                  <td>${position.current_price.toFixed(2)}</td>
                  <td className={position.unrealized_pnl >= 0 ? 'green' : 'red'}>
                    ${position.unrealized_pnl.toFixed(2)}
                  </td>
                  <td>{new Date(position.timestamp).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      
      <div className="trades-section">
        <h2>Recent Trades</h2>
        {trades.length === 0 ? (
          <p>No recent trades</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Side</th>
                <th>Entry Price</th>
                <th>Exit Price</th>
                <th>Profit/Loss</th>
                <th>Close Time</th>
              </tr>
            </thead>
            <tbody>
              {trades.map(trade => (
                <tr key={trade.id}>
                  <td>{trade.symbol}</td>
                  <td className={trade.side.toLowerCase() === 'buy' ? 'green' : 'red'}>
                    {trade.side}
                  </td>
                  <td>${trade.entry_price.toFixed(2)}</td>
                  <td>${trade.exit_price.toFixed(2)}</td>
                  <td className={trade.profit_loss >= 0 ? 'green' : 'red'}>
                    ${trade.profit_loss.toFixed(2)}
                  </td>
                  <td>{new Date(trade.timestamp).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
