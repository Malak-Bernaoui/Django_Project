const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:8000/api';

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });

  const contentType = res.headers.get('content-type') || '';
  const isJson = contentType.includes('application/json');
  const body = isJson ? await res.json().catch(() => null) : await res.text().catch(() => null);

  if (!res.ok) {
    const message = (body && body.message) ? body.message : `HTTP ${res.status}`;
    const err = new Error(message);
    err.status = res.status;
    err.body = body;
    throw err;
  }

  return body;
}

export const api = {
  health: () => request('/health'),

  listBooks: (page = 1) => request(`/books?page=${page}`),
  getBook: (id) => request(`/books/${id}`),
  createBook: (payload) => request('/books', { method: 'POST', body: JSON.stringify(payload) }),
  updateBook: (id, payload) => request(`/books/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteBook: (id) => request(`/books/${id}`, { method: 'DELETE' }),

  listLoans: (params = {}) => {
    const q = new URLSearchParams(params);
    return request(`/loans?${q.toString()}`);
  },
  borrow: (payload) => request('/loans/borrow', { method: 'POST', body: JSON.stringify(payload) }),
  returnLoan: (loanId) => request(`/loans/${loanId}/return`, { method: 'POST' }),
  loanHistory: (userId, page = 1) => request(`/loans/history?user_id=${userId}&page=${page}`),

  listReservations: (params = {}) => {
    const q = new URLSearchParams(params);
    return request(`/reservations?${q.toString()}`);
  },
  createReservation: (payload) => request('/reservations', { method: 'POST', body: JSON.stringify(payload) }),
  cancelReservation: (reservationId) => request(`/reservations/${reservationId}/cancel`, { method: 'POST' }),

  listPenalties: (params = {}) => {
    const q = new URLSearchParams(params);
    return request(`/penalties?${q.toString()}`);
  },
  payPenalty: (penaltyId) => request(`/penalties/${penaltyId}/pay`, { method: 'POST' }),
};
