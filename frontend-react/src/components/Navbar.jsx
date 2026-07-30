import { useState } from 'react';
import WaIcon from './WaIcon';
import styles from './Navbar.module.css';

const WA = 'https://wa.me/2348020812523';

export default function Navbar() {
  const [open, setOpen] = useState(false);
  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <a href="/" className={styles.logo}>
          <span className={styles.wordmark}>SabiSpend</span>
        </a>

        <nav className={`${styles.links} ${open ? styles.open : ''}`}>
          <a href="#how-it-works" onClick={() => setOpen(false)}>How it Works</a>
          <a href="#features" onClick={() => setOpen(false)}>Features</a>
          <a href="#faq" onClick={() => setOpen(false)}>FAQ</a>
        </nav>

        <a href={WA} className="btn-wa-nav" target="_blank" rel="noopener noreferrer">
          <WaIcon size={15} />
          Start on WhatsApp
        </a>

        <button className={styles.burger} onClick={() => setOpen(o => !o)} aria-label="Menu">
          <span /><span /><span />
        </button>
      </div>
    </header>
  );
}
