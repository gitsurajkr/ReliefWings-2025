import React from 'react';
import styles from './TopBar.module.css';
import { FaSatelliteDish, FaBatteryFull, FaTachometerAlt, FaArrowsAltV } from 'react-icons/fa';

const TopBar: React.FC = () => {
  return (
    <header className={styles.topBar}>
      <div className={styles.logo}>RELIEF WINGS</div>
      <div className={styles.telemetry}>
        <div className={styles.telemetryItem}>
          <FaArrowsAltV />
          <span>ALTITUDE: <strong>2,589 m</strong></span>
        </div>
        <div className={styles.telemetryItem}>
          <FaTachometerAlt />
          <span>SPEED: <strong>102.9 km/h</strong></span>
        </div>
        <div className={styles.telemetryItem}>
          <FaBatteryFull />
          <span>BATTERY: <strong>82%</strong></span>
        </div>
        <div className={styles.telemetryItem}>
          <FaSatelliteDish />
          <span>SIGNAL: <strong>STRONG</strong></span>
        </div>
      </div>
    </header>
  );
};

export default TopBar;