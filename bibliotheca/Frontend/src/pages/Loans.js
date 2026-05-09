import { useEffect, useState } from 'react';
import { api } from '../api';

export default function Loans() {
  const [loans, setLoans] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [borrowForm, setBorrowForm] = useState({ user_id: '', book_id: '', days: 14 });

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.listLoans({});
      setLoans(res);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const onBorrowChange = (e) => {
    const { name, value } = e.target;
    setBorrowForm((f) => ({ ...f, [name]: value }));
  };

  const borrow = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      await api.borrow({
        user_id: Number(borrowForm.user_id),
        book_id: Number(borrowForm.book_id),
        days: Number(borrowForm.days || 14),
      });
      setBorrowForm({ user_id: '', book_id: '', days: 14 });
      await load();
    } catch (e2) {
      setError(e2.message);
    }
  };

  const doReturn = async (loanId) => {
    setError(null);
    try {
      await api.returnLoan(loanId);
      await load();
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <div>
      <div className="row">
        <h1>Emprunts</h1>
        <button className="btn" onClick={load} disabled={loading}>Actualiser</button>
      </div>

      <div className="card">
        <div className="card-title">Nouvel emprunt</div>
        {error ? <div className="error">{error}</div> : null}
        <form onSubmit={borrow} className="grid">
          <label>
            user_id
            <input name="user_id" value={borrowForm.user_id} onChange={onBorrowChange} required type="number" min="1" />
          </label>
          <label>
            book_id
            <input name="book_id" value={borrowForm.book_id} onChange={onBorrowChange} required type="number" min="1" />
          </label>
          <label>
            Durée (jours)
            <input name="days" value={borrowForm.days} onChange={onBorrowChange} type="number" min="1" max="60" />
          </label>

          <div className="actions">
            <button className="btn primary" type="submit" disabled={loading}>Emprunter</button>
          </div>
        </form>
      </div>

      <div className="card">
        <div className="card-title">Liste</div>
        {loading && !loans ? <div>Chargement...</div> : null}
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Livre</th>
                <th>Utilisateur</th>
                <th>Statut</th>
                <th>Échéance</th>
                <th>Retour</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {(loans?.data || []).map((l) => (
                <tr key={l.id}>
                  <td>{l.id}</td>
                  <td>{l.book ? `${l.book.title} (#${l.book.id})` : l.book_id}</td>
                  <td>{l.user ? `${l.user.name} (#${l.user.id})` : l.user_id}</td>
                  <td><span className={`pill ${l.status}`}>{l.status}</span></td>
                  <td>{l.due_at ? new Date(l.due_at).toLocaleString() : '-'}</td>
                  <td>{l.returned_at ? new Date(l.returned_at).toLocaleString() : '-'}</td>
                  <td className="cell-actions">
                    <button className="btn small" onClick={() => doReturn(l.id)} disabled={loading || l.status !== 'borrowed'}>
                      Retourner
                    </button>
                  </td>
                </tr>
              ))}
              {loans && (loans.data || []).length === 0 ? (
                <tr>
                  <td colSpan="7" className="muted">Aucun emprunt</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
