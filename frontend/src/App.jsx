import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import EntityExplorer from './pages/EntityExplorer';
import QueryService from './pages/QueryService';
import './index.css';

function App() {
  return (
    <Router>
      <div className="app-container">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/entity/:id" element={<EntityExplorer />} />
            <Route path="/query" element={<QueryService />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
