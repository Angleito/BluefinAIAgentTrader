import React, { useState } from 'react';
import { openTrade, closeTrade } from '../api';

const TradingActions: React.FC = () => {
  const [newTrade, setNewTrade] = useState({
    symbol: '',
    side: '',
    size: 0,
    price: 0
  });

  const [closeTradeId, setCloseTradeId] = useState('');

  const handleOpenTrade = async () => {
    const result = await openTrade(newTrade);
    console.log('Opened trade:', result);
    // TODO: Display success/error message
  };

  const handleCloseTrade = async () => {
    const result = await closeTrade(closeTradeId);  
    console.log('Closed trade:', result);
    // TODO: Display success/error message
  };

  return (
    <div>
      <h1>Manual Trading Actions</h1>

      <section>
        <h2>Open New Trade</h2>
        <div>
          <label>Symbol: <input type="text" value={newTrade.symbol} onChange={e => setNewTrade({...newTrade, symbol: e.target.value})} /></label>
        </div>
        <div>
          <label>Side: <input type="text" value={newTrade.side} onChange={e => setNewTrade({...newTrade, side: e.target.value})} /></label>  
        </div>
        <div>
          <label>Size: <input type="number" value={newTrade.size} onChange={e => setNewTrade({...newTrade, size: parseFloat(e.target.value)})} /></label>
        </div>
        <div>
          <label>Price: <input type="number" value={newTrade.price} onChange={e => setNewTrade({...newTrade, price: parseFloat(e.target.value)})} /></label>
        </div>
        <button onClick={handleOpenTrade}>Open Trade</button>
      </section>

      <section>
        <h2>Close Open Trade</h2>
        <div>
          <label>Trade ID: <input type="text" value={closeTradeId} onChange={e => setCloseTradeId(e.target.value)} /></label>
        </div>
        <button onClick={handleCloseTrade}>Close Trade</button>  
      </section>
    </div>
  );
};

export default TradingActions;
