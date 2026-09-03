import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
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
  const [showFullUris, setShowFullUris] = useState(false);
  const [termKinds, setTermKinds] = useState({});
  const [columnWidths, setColumnWidths] = useState({});
  const resizeRef = useRef(null);

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

  useEffect(() => {
    const resultRows = result?.results?.bindings || [];
    const resultVariables = result?.head?.vars || [];
    const uriValues = [...new Set(resultRows.flatMap((row) => resultVariables.map((variable) => row[variable]).filter((binding) => binding?.type === 'uri').map((binding) => binding.value)))];
    if (!uriValues.length) return undefined;
    let cancelled = false;
    Promise.all(uriValues.map(async (uri) => {
      try {
        const response = await fetch(`${API_URL}/api/term-info?uri=${encodeURIComponent(uri)}`);
        if (!response.ok) return [uri, null];
        const info = await response.json();
        return [uri, info.kind];
      } catch {
        return [uri, null];
      }
    })).then((entries) => {
      if (!cancelled) setTermKinds((current) => ({ ...current, ...Object.fromEntries(entries.filter(([, kind]) => kind)) }));
    });
    return () => { cancelled = true; };
  }, [result]);

  const renderBinding = (variable, binding) => {
    if (!binding?.value) return '';
    const { type, value } = binding;
    if (type !== 'uri') return value;
    if (value.includes('wikidata.org/entity/')) {
      const wikidataId = value.split('/').pop();
      return <a href={`https://www.wikidata.org/wiki/${wikidataId}`} target="_blank" rel="noreferrer">{showFullUris ? value : wikidataId}</a>;
    }
    const target = termKinds[value] || (/predicate|property/i.test(variable) ? 'property' : 'entity');
    const shortValue = value.split(/[/#]/).pop() || value;
    return <Link to={`/${target}/${encodeURIComponent(value)}`}>{showFullUris ? value : shortValue}</Link>;
  };

  const startResize = (event, columnKey) => {
    event.preventDefault();
    const header = event.currentTarget.parentElement;
    resizeRef.current = {
      columnKey,
      startX: event.clientX,
      startWidth: columnWidths[columnKey] || header.getBoundingClientRect().width,
    };
  };

  useEffect(() => {
    executeRef.current = handleExecute;
  });

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

  useEffect(() => {
    const handlePointerMove = (event) => {
      if (!resizeRef.current) return;
      const { columnKey, startX, startWidth } = resizeRef.current;
      const nextWidth = Math.max(100, startWidth + event.clientX - startX);
      setColumnWidths((currentWidths) => ({ ...currentWidths, [columnKey]: nextWidth }));
    };
    const stopResize = () => {
      resizeRef.current = null;
    };
    document.addEventListener('pointermove', handlePointerMove);
    document.addEventListener('pointerup', stopResize);
    return () => {
      document.removeEventListener('pointermove', handlePointerMove);
      document.removeEventListener('pointerup', stopResize);
    };
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
        <div className="results-heading"><div><p className="eyebrow">RESPONSE</p><h2>Results</h2></div><div className="results-controls">{result && <span className="row-count"><CheckCircle2 size={15} /> {rows.length} rows</span>}<label className="uri-toggle"><input type="checkbox" checked={showFullUris} onChange={(event) => setShowFullUris(event.target.checked)} /> Full URI</label></div></div>
        {error && <div className="error-message"><AlertCircle size={18} /><span>{error}</span></div>}
        {!result && !error && <div className="results-placeholder"><p>Run a query to see bindings returned by Fuseki.</p></div>}
        {result && rows.length === 0 && <div className="results-placeholder"><p>The query returned no results.</p></div>}
        {result && rows.length > 0 && <div className="table-wrap"><table><colgroup>{variables.map((variable) => <col key={variable} style={columnWidths[variable] ? { width: `${columnWidths[variable]}px` } : undefined} />)}<col style={columnWidths.actions ? { width: `${columnWidths.actions}px` } : undefined} /></colgroup><thead><tr>{variables.map((variable) => <th key={variable} style={columnWidths[variable] ? { width: `${columnWidths[variable]}px` } : undefined}>?{variable}<span className="column-resizer" onPointerDown={(event) => startResize(event, variable)} aria-hidden="true" /></th>)}<th style={columnWidths.actions ? { width: `${columnWidths.actions}px` } : undefined}>Actions<span className="column-resizer" onPointerDown={(event) => startResize(event, 'actions')} aria-hidden="true" /></th></tr></thead><tbody>{rows.map((row, rowIndex) => <tr key={rowIndex}>{variables.map((variable) => { const binding = row[variable]; return <td key={variable} title={binding?.value || ''}>{renderBinding(variable, binding)}</td>; })}<td><button className="copy-button" title="Copy row" onClick={() => navigator.clipboard?.writeText(JSON.stringify(row))}><Copy size={15} /></button></td></tr>)}</tbody></table></div>}
      </div>
    </div>
  );
}

export default QueryService;
