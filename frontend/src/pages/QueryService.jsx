import { useEffect, useRef, useState } from 'react';
import Editor from '@monaco-editor/react';
import { AlertCircle, CheckCircle2, Copy, Play, RotateCcw } from 'lucide-react';
import './QueryService.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const EXAMPLE_QUERY = `PREFIX schema: <https://schema.org/>
PREFIX ex: <http://example.org/lod/>

SELECT ?person ?name ?role
WHERE {
  ?person a schema:Person ;
          schema:name ?name ;
          schema:jobTitle ?role .
}
ORDER BY ?name`;

function QueryService() {
  const [query, setQuery] = useState(EXAMPLE_QUERY);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleExecute = async () => {
    if (!query.trim()) return;
    setIsLoading(true);
    setError('');
    setResult(null);
    try {
      const response = await fetch(`${API_URL}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || 'Query gagal dijalankan.');
      setResult(payload);
    } catch (requestError) {
      setError(requestError.message || 'Tidak dapat terhubung ke API.');
    } finally {
      setIsLoading(false);
    }
  };

  const rows = result?.results?.bindings || [];
  const variables = result?.head?.vars || [];
  const executeRef = useRef(handleExecute);
  executeRef.current = handleExecute;

  useEffect(() => {
    const handleShortcut = (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        event.preventDefault();
        executeRef.current();
      }
    };
    window.addEventListener('keydown', handleShortcut);
    return () => window.removeEventListener('keydown', handleShortcut);
  }, []);

  return (
    <div className="query-container">
      <div className="query-header">
        <div>
          <p className="eyebrow">LOCAL DATASET / SPARQL</p>
          <h1>Query service</h1>
          <p className="query-intro">Write a query, send it through FastAPI, and inspect the graph response.</p>
        </div>
        <button className="secondary-button" onClick={() => setQuery(EXAMPLE_QUERY)} title="Restore example query">
          <RotateCcw size={16} /> Reset example
        </button>
      </div>

      <div className="editor-section">
        <div className="editor-wrapper">
          <Editor height="310px" language="sql" theme="vs-dark" value={query} onChange={(value) => setQuery(value || '')} options={{ minimap: { enabled: false }, fontSize: 14, padding: { top: 18 } }} />
        </div>
        <div className="action-bar">
          <button className="btn-execute" onClick={handleExecute} disabled={isLoading || !query.trim()}>
            <Play className="icon-small" /> {isLoading ? 'Running...' : 'Run query'}
          </button>
        </div>
      </div>

      <div className="results-section">
        <div className="results-heading"><div><p className="eyebrow">RESPONSE</p><h2>Results</h2></div>{result && <span className="row-count"><CheckCircle2 size={15} /> {rows.length} rows</span>}</div>
        {error && <div className="error-message"><AlertCircle size={18} /><span>{error}</span></div>}
        {!result && !error && <div className="results-placeholder"><p>Run a query to see bindings returned by Fuseki.</p></div>}
        {result && rows.length === 0 && <div className="results-placeholder"><p>The query returned no results.</p></div>}
        {result && rows.length > 0 && <div className="table-wrap"><table><thead><tr>{variables.map((variable) => <th key={variable}>?{variable}</th>)}<th>Actions</th></tr></thead><tbody>{rows.map((row, rowIndex) => <tr key={rowIndex}>{variables.map((variable) => { const value = row[variable]?.value || ''; return <td key={variable} title={value}>{value}</td>; })}<td><button className="copy-button" title="Copy row" onClick={() => navigator.clipboard?.writeText(JSON.stringify(row))}><Copy size={15} /></button></td></tr>)}</tbody></table></div>}
      </div>
    </div>
  );
}

export default QueryService;
