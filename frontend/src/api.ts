import { io, Socket } from 'socket.io-client';

// Use relative URLs to work with nginx proxy in production
const API_BASE_URL = '/api';
const SOCKET_URL = window.location.origin; // This will work with the socket.io path configured in nginx
let socket: Socket | null = null;

// Bluefin API base URL
const BLUEFIN_API_URL = 'https://api.bluefin.exchange/v1';

// WebSocket functions
export function connectSocket(onConnect?: () => void, onDisconnect?: () => void) {
  if (socket) {
    // Already connected
    return socket;
  }

  // Connect to socket.io through the /socket.io path configured in nginx
  socket = io(SOCKET_URL, {
    path: '/socket.io'
  });
  
  socket.on('connect', () => {
    console.log('Connected to WebSocket server');
    if (onConnect) onConnect();
  });
  
  socket.on('disconnect', () => {
    console.log('Disconnected from WebSocket server');
    if (onDisconnect) onDisconnect();
  });
  
  return socket;
}

export function disconnectSocket() {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
}

export function subscribeToEvent(event: string, callback: (data: any) => void) {
  if (!socket) {
    console.error('Socket not connected. Call connectSocket() first.');
    return;
  }
  
  socket.on(event, callback);
  return () => socket?.off(event, callback); // Return unsubscribe function
}

// Authentication functions
export async function login(username: string, password: string) {
  const response = await fetch(`${API_BASE_URL}/login`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ username, password })
  });
  const data = await response.json();
  
  if (data.status === 'success') {
    // Store token in localStorage
    localStorage.setItem('token', data.token);
    localStorage.setItem('user', JSON.stringify(data.user));
    
    // Connect to WebSocket after successful login
    connectSocket();
  }
  
  return data;
}

export function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  
  // Disconnect WebSocket on logout
  disconnectSocket();
}

export function getToken() {
  return localStorage.getItem('token');
}

export function getUser() {
  const userStr = localStorage.getItem('user');
  return userStr ? JSON.parse(userStr) : null;
}

export function isAuthenticated() {
  return !!getToken();
}

// Helper function to add auth header to requests
const authHeader = (): Record<string, string> => {
  const token = getToken();
  return token ? { 'Authorization': `Bearer ${token}` } : {};
};

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
    headers: {
      'Content-Type': 'application/json',
      ...authHeader()
    },
    body: JSON.stringify(trade)
  });
  return await response.json();
}

export async function closeTrade(tradeId: string) {
  const response = await fetch(`${API_BASE_URL}/close_trade`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeader()
    },
    body: JSON.stringify({trade_id: tradeId})
  });
  return await response.json();
}

export async function getConfiguration() {
  const response = await fetch(`${API_BASE_URL}/configuration`);
  return await response.json();
}

export async function updateConfiguration(config: any) {
  const response = await fetch(`${API_BASE_URL}/configure`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeader()
    },
    body: JSON.stringify(config)
  });
  return await response.json();
}

// Agent API endpoints
const AGENT_API_URL = '/agent';

export async function getAgentHealth() {
  const response = await fetch(`${AGENT_API_URL}/health`);
  return await response.json();
}

export async function getAgentMetrics() {
  const response = await fetch(`${AGENT_API_URL}/metrics`);
  return await response.json();
}

export async function controlAgent(command: string) {
  const response = await fetch(`${AGENT_API_URL}/control`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeader()
    },
    body: JSON.stringify({ command })
  });
  return await response.json();
}

// Bluefin API endpoints
export async function getBluefinExchangeInfo() {
  const response = await fetch(`${BLUEFIN_API_URL}/exchangeInfo`);
  return await response.json();
}

export async function getBluefinMarketData(symbol: string) {  
  const response = await fetch(`${BLUEFIN_API_URL}/marketData?symbol=${symbol}`);
  return await response.json();
}

export async function postBluefinOrder(order: any) {
  const response = await fetch(`${BLUEFIN_API_URL}/orders`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json', 
      ...authHeader()
    },
    body: JSON.stringify(order)
  });
  return await response.json();  
}

// Add more Bluefin API functions as needed 