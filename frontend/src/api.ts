const API_BASE_URL = 'http://localhost:5000';

export async function getAgentStatus() {
  const response = await fetch(`${API_BASE_URL}/status`);
  return await response.json();
}

export async function getOpenPositions() {
  const response = await fetch(`${API_BASE_URL}/positions`);
  return await response.json();
}

export async function getRecentTrades(limit: number = 10) {
  const response = await fetch(`${API_BASE_URL}/trades?limit=${limit}`);
  return await response.json();
}

export async function openTrade(trade: any) {
  const response = await fetch(`${API_BASE_URL}/open_trade`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(trade)
  });
  return await response.json();
}

export async function closeTrade(tradeId: string) {
  const response = await fetch(`${API_BASE_URL}/close_trade`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({trade_id: tradeId})
  });
  return await response.json();
} 