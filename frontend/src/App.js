import React, { useState } from 'react';
import ImportForm from './components/ImportForm';
import ImageGallery from './components/ImageGallery';
import './App.css';

function App() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleImportComplete = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Image Import System</h1>
        <p>Import, store, and instantly browse images from Google Drive.</p>

       
      </header>
      
      <main className="App-main">
        <div className="layout">
          <section className="layout-left" aria-label="Import">
            <ImportForm onImportComplete={handleImportComplete} />
          </section>
          <section className="layout-right" aria-label="Gallery">
            <ImageGallery refreshTrigger={refreshTrigger} />
          </section>
        </div>
      </main>
      
      <footer className="App-footer">
        <p>React UI • Flask microservices • Docker • AWS</p>
      </footer>
    </div>
  );
}

export default App;
