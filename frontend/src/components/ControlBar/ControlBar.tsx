import React from 'react';
import styles from './ControlBar.module.css';
import { FaPlay, FaMapMarkedAlt, FaCamera, FaFileAlt } from 'react-icons/fa';

const ControlBar: React.FC = () => {
  return (
    <footer className={styles.controlBar}>
      <button className={`${styles.button} ${styles.takeoff}`}>
        <FaPlay />
        <span>TAKEOFF / LAND</span>
      </button>
       <button className={styles.button}>
        <FaMapMarkedAlt />
        <span>AREA SCAN</span>
      </button>
      <button className={styles.button}>
        <FaCamera />
        <span>CAPTURE</span>
      </button>
      <button className={`${styles.button} ${styles.report}`}>
        <FaFileAlt />
        <span>GENERATE REPORT</span>
      </button>
    </footer>
  );
};

export default ControlBar;