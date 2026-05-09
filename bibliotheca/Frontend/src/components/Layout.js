import { Link, NavLink } from 'react-router-dom';

function NavItem({ to, children }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
      end
    >
      {children}
    </NavLink>
  );
}

export default function Layout({ children }) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="container header-row">
          <Link to="/" className="brand">Bibliotheca</Link>
          <nav className="nav">
            <NavItem to="/books">Livres</NavItem>
            <NavItem to="/loans">Emprunts</NavItem>
            <NavItem to="/reservations">Réservations</NavItem>
            <NavItem to="/penalties">Pénalités</NavItem>
          </nav>
        </div>
      </header>
      <main className="container app-main">{children}</main>
    </div>
  );
}
