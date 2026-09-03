import { Link, useParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import './EntityExplorer.css';

function EntityExplorer() {
  const { id } = useParams();
  const uri = decodeURIComponent(id);
  const [resource, setResource] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/resources?uri=${encodeURIComponent(uri)}`)
      .then(async (response) => { const payload = await response.json(); if (!response.ok) throw new Error(payload.detail); return payload; })
      .then(setResource)
      .catch((requestError) => setError(requestError.message || 'Resource tidak dapat dimuat.'));
  }, [uri]);

  const localName = uri.split(/[/#]/).pop();
  const wikidataLinks = resource?.properties.filter((item) => item.object?.value?.includes('wikidata.org/entity/')) || [];

  return (
    <div className="entity-container">
      <div className="entity-header">
        <h1>{localName}</h1>
        <span className="entity-type">RDF Resource</span>
      </div>
      {error && <p className="entity-error">{error}</p>}
      <div className="entity-content">
        <div className="property-group">
          <div className="property-name">URI</div>
          <div className="property-values">
            <a href={uri} target="_blank" rel="noreferrer">{uri}</a>
          </div>
        </div>
        {wikidataLinks.length > 0 && <div className="property-group"><div className="property-name">Wikidata</div><div className="property-values">{wikidataLinks.map((item) => <a key={item.object.value} href={item.object.value.replace('http://www.wikidata.org/entity/', 'https://www.wikidata.org/wiki/')} target="_blank" rel="noreferrer">{item.object.value.split('/').pop()}</a>)}</div></div>}
        {(resource?.properties || []).map((item) => <div className="property-group" key={`${item.predicate.value}-${item.object.value}`}><div className="property-name"><Link to={`/property/${encodeURIComponent(item.predicate.value)}`}>{item.predicate.value.split(/[/#]/).pop()}</Link></div><div className="property-values"><div className="value-item">{item.objectType?.value === 'iri' ? <Link to={`/entity/${encodeURIComponent(item.object.value)}`}>{item.object.value}</Link> : item.object.value}</div></div></div>)}
      </div>
    </div>
  );
}

export default EntityExplorer;
