import React from 'react';
import styles from './AIResults.module.css';
import { FaUser, FaCar, FaBuilding, FaExclamationTriangle } from 'react-icons/fa';

const detectedItems = [
  { icon: <FaUser />, name: 'Person', confidence: '98%', count: 5 },
  { icon: <FaCar />, name: 'Vehicle', confidence: '95%', count: 2 },
  { icon: <FaExclamationTriangle />, name: 'Debris', confidence: '89%', count: 12 },
  { icon: <FaBuilding />, name: 'Structure Damage', confidence: '85%', count: 3 },
];

const AIResults: React.FC = () => {
  return (
    <aside className={styles.aiResults}>
      <h2 className={styles.title}>AI Object Detection</h2>
      <div className={styles.summary}>
        <span>STATUS:</span>
        <span className={styles.statusActive}>ACTIVE</span>
      </div>
      <ul className={styles.resultsList}>
        {detectedItems.map((item, index) => (
          <li key={index} className={styles.resultItem}>
            <div className={styles.itemIcon}>{item.icon}</div>
            <div className={styles.itemName}>{item.name}</div>
            <div className={styles.itemConfidence}>{item.confidence}</div>
            <div className={styles.itemCount}>x{item.count}</div>
          </li>
        ))}
      </ul>
       <button className={styles.toggleButton}>Hide Bounding Boxes</button>
    </aside>
  );
};

export default AIResults;