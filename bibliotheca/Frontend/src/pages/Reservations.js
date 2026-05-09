import { useEffect, useState } from 'react';
import { api } from '../api';

export default function Reservations() {
  const [reservations, setReservations] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [form, setForm] = useState({ user_id: '', book_id: '' });

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.listReservations({});
      setReservations(res);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
  };

  const reserve = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      await api.createReservation({
        user_id: Number(form.user_id),
        book_id: Number(form.book_id),
      });
      setForm({ user_id: '', book_id: '' });
      await load();
    } catch (e2) {
      setError(e2.message);
    }
  };

  const cancel = async (id) => {
    setError(null);
    try {
      await api.cancelReservation(id);
      await load();
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <div>
      <div className="row">
        <h1>Réservations</h1>
        <button className="btn" onClick={load} disabled={loading}>Actualiser</button>
      </div>

      <div className="card">
        <div className="card-title">Nouvelle réservation</div>
        {error ? <div className="error">{error}</div> : null}
        <form onSubmit={reserve} className="grid">
          <label>
            user_id
            <input name="user_id" value={form.user_id} onChange={onChange} required type="number" min="1" />
          </label>
          <label>
            book_id
            <input name="book_id" value={form.book_id} onChange={onChange} required type="number" min="1" />
          </label>
          <div className="actions">
            <button className="btn primary" type="submit" disabled={loading}>Réserver</button>
          </div>
        </form>
      </div>

      <div className="card">
        <div className="card-title">Liste</div>
        {loading && !reservations ? <div>Chargement...</div> : null}
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Livre</th>
                <th>Utilisateur</th>
                <th>Statut</th>
                <th>Réservé le</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {(reservations?.data || []).map((r) => (
                <tr key={r.id}>
                  <td>{r.id}</td>
                  <td>{r.book ? `${r.book.title} (#${r.book.id})` : r.book_id}</td>
                  <td>{r.user ? `${r.user.name} (#${r.user.id})` : r.user_id}</td>
                  <td><span className={`pill ${r.status}`}>{r.status}</span></td>
                  <td>{r.reserved_at ? new Date(r.reserved_at).toLocaleString() : '-'}</td>
                  <td className="cell-actions">
                    <button className="btn small" onClick={() => cancel(r.id)} disabled={loading || r.status !== 'active'}>
                      Annuler
                    </button>
                  </td>
                </tr>
              ))}
              {reservations && (reservations.data || []).length === 0 ? (
                <tr>
                  <td colSpan="6" className="muted">Aucune réservation</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
