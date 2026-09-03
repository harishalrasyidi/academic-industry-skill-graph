import { Link, useLocation } from 'react-router-dom';
import { Database, Search, Code2 } from 'lucide-react';
import './Navbar.css';

function Navbar() {
  const location = useLocation();
  
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Database className="icon" />
        <Link to="/">
          <span className="brand-text">LOD Explorer</span>
        </Link>
      </div>
      <ul className="navbar-links">
        <li className={location.pathname === '/' ? 'active' : ''}>
          <Link to="/">
            <Search className="icon-small" />
            <span>Search</span>
          </Link>
        </li>
        <li className={location.pathname.startsWith('/query') ? 'active' : ''}>
          <Link to="/query">
            <Code2 className="icon-small" />
            <span>Query Service</span>
          </Link>
        </li>
      </ul>
    </nav>
  );
}

export default Navbar;
