import React, { useEffect, useState } from 'react';
import { getAgentStatus, getOpenPositions, getRecentTrades } from '../api';

const Dashboard: React.FC = () => {
  const [status, setStatus] = useState<any>(null);
  const [positions, setPositions] = useState<any[]>([]);
  const [trades, setTrades] = useState<any[]>([]);

  useEffect(() => {
    getAgentStatus().then(setStatus);
    getOpenPositions().then(setPositions);
    getRecentTrades().then(setTrades);
  }, []);

  return (
    <div>
      <h1>Trading Agent Dashboard</h1>
      <section>
        <h2>Agent Status</h2>
        {status ? (
          <div>
            <p>Status: {status.status}</p>
            <p>Last Analysis: {status.last_analysis}</p>
            <p>Open Positions: {status.open_positions}</p>
            <p>Recent Trades: {status.recent_trades}</p>
          </div>
        ) : <p>Loading...</p>}
      </section>
      
      <section>
        <h2>Open Positions</h2>
        {positions.length > 0 ? (
          <ul>
            {positions.map(position => (
              <li key={position.id}>
                {position.symbol}: {position.size} @ {position.entry_price} (Current: {position.current_price}, PnL: {position.pnl})
              </li>
            ))}
          </ul>
        ) : <p>No open positions</p>}
      </section>

      <section>
        <h2>Recent Trades</h2>
        {trades.length > 0 ? (
          <ul>
            {trades.map(trade => (
              <li key={trade.id}>
                {trade.side} {trade.symbol}: {trade.size} @ {trade.price}
              </li>
            ))}
          </ul>
        ) : <p>No recent trades</p>}
      </section>
    </div>
  );
};

export default Dashboard;
