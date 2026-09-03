import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search } from 'lucide-react';
import './Home.css';

function Home() {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/entity/${encodeURIComponent(query)}`);
    }
  };

  return (
    <div className="home-container">
      <div className="hero">
        <h1>Welcome to LOD Explorer</h1>
        <p>Explore the Computer Science Ontology and ESCO Skills Mapping</p>
        
        <form className="search-box" onSubmit={handleSearch}>
          <Search className="search-icon" />
          <input 
            type="text" 
            placeholder="Search for an entity, topic, or skill (e.g. software_engineering)..." 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
          />
          <button type="submit">Search</button>
        </form>
      </div>
    </div>
  );
}

export default Home;
