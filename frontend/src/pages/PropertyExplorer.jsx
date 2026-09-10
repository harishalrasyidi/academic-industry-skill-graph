import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

function PropertyExplorer() {
  const { id } = useParams();
  const uri = decodeURIComponent(id);
  const [property, setProperty] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL || ''}/api/properties?uri=${encodeURIComponent(uri)}`)
      .then(async (response) => { const payload = await response.json(); if (!response.ok) throw new Error(payload.detail); return payload; })
      .then(setProperty)
      .catch((requestError) => setError(requestError.message || 'Property tidak dapat dimuat.'));
  }, [uri]);

  const localName = uri.split(/[/#]/).pop();
  return <div className="entity-container"><div className="entity-header"><h1>{localName}</h1><span className="entity-type">RDF Property</span></div>{error && <p className="entity-error">{error}</p>}<div className="entity-content"><div className="property-group"><div className="property-name">URI</div><div className="property-values"><a href={uri} target="_blank" rel="noreferrer">{uri}</a></div></div><div className="property-group"><div className="property-name">Metadata</div><div className="property-values">{(property?.metadata || []).map((item, index) => <div className="value-item" key={index}>{item.type?.value?.split(/[/#]/).pop()}{item.domain?.value && ` | domain: ${item.domain.value.split(/[/#]/).pop()}`}{item.range?.value && ` | range: ${item.range.value.split(/[/#]/).pop()}`}</div>)}</div></div><div className="property-group"><div className="property-name">Usage examples</div><div className="property-values">{(property?.examples || []).map((item, index) => <div className="value-item" key={index}><Link to={`/entity/${encodeURIComponent(item.subject.value)}`}>{item.subject.value}</Link>{' -> '}{item.value.value}</div>)}</div></div></div></div>;
}

export default PropertyExplorer;