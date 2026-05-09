import './App.css';
import { Navigate, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import Books from './pages/Books';
import Home from './pages/Home';
import Loans from './pages/Loans';
import Penalties from './pages/Penalties';
import Reservations from './pages/Reservations';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/books" element={<Books />} />
        <Route path="/loans" element={<Loans />} />
        <Route path="/reservations" element={<Reservations />} />
        <Route path="/penalties" element={<Penalties />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

export default App;
