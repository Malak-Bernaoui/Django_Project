import { useEffect, useState } from 'react';
import { api } from '../api';

export default function Home() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    api
      .health()
      .then((data) => {
        if (mounted) setHealth(data);
      })
      .catch((e) => {
        if (mounted) setError(e.message);
      });

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div>
      <h1>Tableau de bord</h1>
      <p>
        Cette interface consomme l’API Laravel.
      </p>
      <div className="card">
        <div className="card-title">État API</div>
        {error ? <div className="error">{error}</div> : null}
        {health ? <pre className="pre">{JSON.stringify(health, null, 2)}</pre> : <div>Chargement...</div>}
      </div>
      <div className="card">
        <div className="card-title">Remarque</div>
        <p>
          L’authentification / rôles (Admin, Bibliothécaire, Étudiant) sera ajoutée ensuite.
          Pour l’instant, les actions “emprunter / réserver” demandent un <code>user_id</code>.
        </p>
      </div>
    </div>
  );
}
