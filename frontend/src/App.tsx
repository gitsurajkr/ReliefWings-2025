import React from 'react';
import './App.css'; 
import TopBar from './components/TopBar/TopBar';
import AIResults from './components/AIResults/AIResults';
import MainFeed from './components/MainFeed/MainFeed';
import ControlBar from './components/ControlBar/ControlBar';

const App: React.FC = () => {
  const appStyle: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: '350px 1fr',
    gridTemplateRows: '60px 1fr 100px',
    height: '100vh',
    width: '100vw',
    gridTemplateAreas: `
      "topbar topbar"
      "sidebar main"
      "sidebar controls"
    `,
  };

  return (
    <div style={appStyle}>
      <TopBar />
      <AIResults />
      <MainFeed />
      <ControlBar />
    </div>
  );
}

export default App;