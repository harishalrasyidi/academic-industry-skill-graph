import { useParams } from 'react-router-dom';
import './EntityExplorer.css';

function EntityExplorer() {
  const { id } = useParams();

  // Mock data for now, later fetched from backend API
  return (
    <div className="entity-container">
      <div className="entity-header">
        <h1>{decodeURIComponent(id)}</h1>
        <span className="entity-type">CSO Topic</span>
      </div>
      
      <div className="entity-content">
        <div className="property-group">
          <div className="property-name">URI</div>
          <div className="property-values">
            <a href={`https://cso.kmi.open.ac.uk/topics/${id}`} target="_blank" rel="noreferrer">
              https://cso.kmi.open.ac.uk/topics/{id}
            </a>
          </div>
        </div>

        <div className="property-group">
          <div className="property-name">superTopicOf</div>
          <div className="property-values">
            <div className="value-item"><a href="/entity/agile_software_development">agile software development</a></div>
            <div className="value-item"><a href="/entity/software_design">software design</a></div>
            <div className="value-item"><a href="/entity/software_testing">software testing</a></div>
          </div>
        </div>

        <div className="property-group">
          <div className="property-name">exactMatch (Wikidata)</div>
          <div className="property-values">
            <div className="value-item"><a href="https://www.wikidata.org/wiki/Q8087" target="_blank" rel="noreferrer">Q8087 (Software Engineering)</a></div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default EntityExplorer;
