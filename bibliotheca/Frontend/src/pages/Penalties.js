import { useEffect, useState } from 'react';
import { api } from '../api';

export default function Penalties() {
  const [penalties, setPenalties] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.listPenalties({});
      setPenalties(res);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const pay = async (id) => {
    setError(null);
    try {
      await api.payPenalty(id);
      await load();
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <div>
      <div className="row">
        <h1>Pénalités</h1>
        <button className="btn" onClick={load} disabled={loading}>Actualiser</button>
      </div>

      <div className="card">
        <div className="card-title">Liste</div>
        {error ? <div className="error">{error}</div> : null}
        {loading && !penalties ? <div>Chargement...</div> : null}

        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Utilisateur</th>
                <th>Livre</th>
                <th>Montant</th>
                <th>Statut</th>
                <th>Payé le</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {(penalties?.data || []).map((p) => (
                <tr key={p.id}>
                  <td>{p.id}</td>
                  <td>{p.user ? `${p.user.name} (#${p.user.id})` : p.user_id}</td>
                  <td>{p.loan?.book ? `${p.loan.book.title} (#${p.loan.book.id})` : (p.loan_id ?? '-')}
                  </td>
                  <td>{p.amount}</td>
                  <td><span className={`pill ${p.status}`}>{p.status}</span></td>
                  <td>{p.paid_at ? new Date(p.paid_at).toLocaleString() : '-'}</td>
                  <td className="cell-actions">
                    <button className="btn small" onClick={() => pay(p.id)} disabled={loading || p.status !== 'unpaid'}>
                      Payer
                    </button>
                  </td>
                </tr>
              ))}
              {penalties && (penalties.data || []).length === 0 ? (
                <tr>
                  <td colSpan="7" className="muted">Aucune pénalité</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
