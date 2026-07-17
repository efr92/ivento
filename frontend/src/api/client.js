const API_BASE = '/api/v1';

let accessToken = localStorage.getItem('access_token');
let refreshToken = localStorage.getItem('refresh_token');

export function getAccessToken() {
  return accessToken;
}

export function setTokens(access, refresh) {
  accessToken = access;
  refreshToken = refresh;
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
}

export function clearTokens() {
  accessToken = null;
  refreshToken = null;
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const headers = { 'Content-Type': 'application/json', ...options.headers };

  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  let res = await fetch(url, { ...options, headers });

  // Token expired — try refresh
  if (res.status === 401 && refreshToken) {
    const refreshRes = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (refreshRes.ok) {
      const data = await refreshRes.json();
      setTokens(data.access_token, data.refresh_token);
      headers['Authorization'] = `Bearer ${data.access_token}`;
      res = await fetch(url, { ...options, headers });
    } else {
      clearTokens();
      window.location.reload();
      throw new Error('Сессия истекла');
    }
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const err = new Error(body.detail || `Ошибка ${res.status}`);
    err.status = res.status;
    throw err;
  }

  return res.json();
}

// Auth
export async function login(email, password) {
  const data = await request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  setTokens(data.access_token, data.refresh_token);
  return data;
}

export async function register(email, username, password) {
  const data = await request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, username, password }),
  });
  setTokens(data.access_token, data.refresh_token);
  return data;
}

export async function getMe() {
  return request('/auth/verify');
}

// Events
export async function createEvent(data) {
  return request('/events', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getNearbyEvents(lat, lon, radius = 50) {
  return request(
    `/events/nearby?latitude=${lat}&longitude=${lon}&radius=${radius}&limit=100`
  );
}

export async function getEvent(id) {
  return request(`/events/${id}`);
}

export async function joinEvent(eventId) {
  return request(`/events/${eventId}/join`, { method: 'POST' });
}

// Config
export async function getConfig() {
  return request('/config');
}
