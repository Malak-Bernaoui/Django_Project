import { useEffect, useMemo, useState } from 'react';
import { api } from '../api';

const emptyForm = {
  title: '',
  author: '',
  isbn: '',
  category: '',
  published_year: '',
  copies_total: 1,
};

export default function Books() {
  const [page, setPage] = useState(1);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const isEditing = useMemo(() => editingId !== null, [editingId]);

  const load = async (p = page) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.listBooks(p);
      setData(res);
      setPage(res.current_page || p);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
  };

  const reset = () => {
    setForm(emptyForm);
    setEditingId(null);
  };

  const submit = async (e) => {
    e.preventDefault();
    setError(null);

    const payload = {
      title: form.title,
      author: form.author,
      isbn: form.isbn || null,
      category: form.category || null,
      published_year: form.published_year === '' ? null : Number(form.published_year),
      copies_total: Number(form.copies_total),
    };

    try {
      if (isEditing) {
        await api.updateBook(editingId, payload);
      } else {
        await api.createBook(payload);
      }
      reset();
      await load(page);
    } catch (e2) {
      setError(e2.message);
    }
  };

  const startEdit = (book) => {
    setEditingId(book.id);
    setForm({
      title: book.title || '',
      author: book.author || '',
      isbn: book.isbn || '',
      category: book.category || '',
      published_year: book.published_year ?? '',
      copies_total: book.copies_total ?? 1,
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const remove = async (id) => {
    if (!window.confirm('Supprimer ce livre ?')) return;
    setError(null);
    try {
      await api.deleteBook(id);
      await load(page);
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <div>
      <div className="row">
        <h1>Livres</h1>
        <button className="btn" onClick={() => load(page)} disabled={loading}>Actualiser</button>
      </div>

      <div className="card">
        <div className="card-title">{isEditing ? `Modifier livre #${editingId}` : 'Ajouter un livre'}</div>
        {error ? <div className="error">{error}</div> : null}
        <form onSubmit={submit} className="grid">
          <label>
            Titre
            <input name="title" value={form.title} onChange={onChange} required />
          </label>
          <label>
            Auteur
            <input name="author" value={form.author} onChange={onChange} required />
          </label>
          <label>
            ISBN
            <input name="isbn" value={form.isbn} onChange={onChange} />
          </label>
          <label>
            Catégorie
            <input name="category" value={form.category} onChange={onChange} />
          </label>
          <label>
            Année
            <input name="published_year" value={form.published_year} onChange={onChange} type="number" min="0" />
          </label>
          <label>
            Exemplaires (total)
            <input name="copies_total" value={form.copies_total} onChange={onChange} type="number" min="0" required />
          </label>

          <div className="actions">
            <button className="btn primary" type="submit" disabled={loading}>
              {isEditing ? 'Enregistrer' : 'Créer'}
            </button>
            <button className="btn" type="button" onClick={reset} disabled={loading}>
              Annuler
            </button>
          </div>
        </form>
      </div>

      <div className="card">
        <div className="card-title">Liste</div>
        {loading && !data ? <div>Chargement...</div> : null}

        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Titre</th>
                <th>Auteur</th>
                <th>Disponible</th>
                <th>Total</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {(data?.data || []).map((b) => (
                <tr key={b.id}>
                  <td>{b.id}</td>
                  <td>{b.title}</td>
                  <td>{b.author}</td>
                  <td>{b.copies_available}</td>
                  <td>{b.copies_total}</td>
                  <td className="cell-actions">
                    <button className="btn small" onClick={() => startEdit(b)}>Modifier</button>
                    <button className="btn small danger" onClick={() => remove(b.id)}>Supprimer</button>
                  </td>
                </tr>
              ))}
              {data && (data.data || []).length === 0 ? (
                <tr>
                  <td colSpan="6" className="muted">Aucun livre</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>

        <div className="pager">
          <button className="btn" disabled={!data || data.current_page <= 1 || loading} onClick={() => load((data.current_page || 1) - 1)}>
            Précédent
          </button>
          <div className="muted">
            Page {data?.current_page || 1} / {data?.last_page || 1}
          </div>
          <button className="btn" disabled={!data || data.current_page >= data.last_page || loading} onClick={() => load((data.current_page || 1) + 1)}>
            Suivant
          </button>
        </div>
      </div>
    </div>
  );
}
