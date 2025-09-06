import React from 'react';
import styles from './MainFeed.module.css';
import disasterFeedImage from '../../assets/disaster-feed.jpg';

// En una aplicación real, estos datos vendrían de una API de IA
const boundingBoxes = [
  { id: 1, top: '30%', left: '40%', width: '15%', height: '25%', label: 'Person' },
  { id: 2, top: '60%', left: '15%', width: '20%', height: '20%', label: 'Debris' },
  { id: 3, top: '55%', left: '65%', width: '25%', height: '30%', label: 'Structure Damage' },
];

const MainFeed: React.FC = () => {
  return (
    <main className={styles.mainFeed}>
      <img src={disasterFeedImage} alt="Live drone feed of a disaster area" className={styles.feedImage} />
      
      {/* Superposición para los cuadros delimitadores de la IA */}
      <div className={styles.overlay}>
        {boundingBoxes.map(box => (
          <div 
            key={box.id} 
            className={styles.boundingBox} 
            style={{ top: box.top, left: box.left, width: box.width, height: box.height }}
          >
            <span className={styles.boxLabel}>{box.label}</span>
          </div>
        ))}
      </div>

      {/* Superposición para la vista térmica */}
      <div className={styles.thermalView}>
        <div className={styles.thermalLabel}>THERMAL VIEW</div>
        {/* En una aplicación real, aquí iría una imagen o transmisión térmica */}
      </div>
    </main>
  );
};

export default MainFeed;