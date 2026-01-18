import React, { useState, useEffect } from 'react';
import { importFromGoogleDrive, getImportStatus } from '../services/api';
import './ImportForm.css';

const ImportForm = ({ onImportComplete }) => {
  const [folderUrl, setFolderUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);
  const [jobId, setJobId] = useState(null);

  
  useEffect(() => {
    if (!jobId) return;

    const pollInterval = setInterval(async () => {
      try {
        const status = await getImportStatus(jobId);

        
        setMessage({
          text: `Processing: ${status.processed + status.failed} of ${status.total} images`,
          total: status.total,
          processed: status.processed,
          failed: status.failed,
          status: status.status
        });

        
        if (status.status === 'completed') {
          setLoading(false);
          setJobId(null);
          setMessage({
            text: 'Import completed!',
            total: status.total,
            processed: status.processed,
            failed: status.failed,
            status: 'completed'
          });
          if (onImportComplete) {
            onImportComplete();
          }
        }
      } catch (err) {
        console.error('Error polling job status:', err);
      }
    }, 2000); 

    return () => clearInterval(pollInterval);
  }, [jobId, onImportComplete]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);
    setError(null);

    try {
      const result = await importFromGoogleDrive(folderUrl);
      
      
      if (result.job_id) {
        setJobId(result.job_id);
        setMessage({
          text: result.message || `Import started for ${result.total_images} images`,
          total: result.total_images,
          processed: 0,
          failed: 0,
          status: 'processing'
        });
        setFolderUrl('');
      } else {
        
        setMessage({
          text: result.message,
          total: result.total_found || result.total_images,
          processed: result.imported?.length || 0,
          failed: result.failed?.length || 0,
          status: 'completed'
        });
        setFolderUrl('');
        setLoading(false);
        if (onImportComplete) {
          onImportComplete();
        }
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to import images');
      setLoading(false);
    }
  };

  return (
    <div className="import-form-container">
      <h2>Import Images from Google Drive</h2>
      <form onSubmit={handleSubmit} className="import-form">
        <div className="form-group">
          <label htmlFor="folderUrl">Google Drive Folder URL:</label>
          <input
            type="text"
            id="folderUrl"
            value={folderUrl}
            onChange={(e) => setFolderUrl(e.target.value)}
            placeholder="https://drive.google.com/drive/folders/..."
            required
            disabled={loading}
          />
        </div>
        <button type="submit" disabled={loading} className="btn-primary">
          {loading ? 'Importing...' : 'Import Images'}
        </button>
      </form>

      {loading && (
        <div className="loading-indicator">
          <div className="spinner"></div>
          <p>Importing images... This may take a while.</p>
          {message && message.status === 'processing' && (
            <p>Progress: {message.processed + message.failed} / {message.total} images</p>
          )}
        </div>
      )}

      {message && (
        <div className={`message ${message.status === 'completed' ? 'success' : 'info'}`}>
          <h3>✓ {message.text}</h3>
          <ul>
            <li>Total images found: {message.total}</li>
            <li>Successfully processed: {message.processed}</li>
            {message.failed > 0 && <li>Failed: {message.failed}</li>}
            {message.status === 'processing' && (
              <li>
                <strong>Status: Processing...</strong>
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{width: `${((message.processed + message.failed) / message.total * 100)}%`}}
                  />
                </div>
              </li>
            )}
          </ul>
        </div>
      )}

      {error && (
        <div className="message error">
          <h3>✗ Error</h3>
          <p>{error}</p>
        </div>
      )}
    </div>
  );
};

export default ImportForm;
