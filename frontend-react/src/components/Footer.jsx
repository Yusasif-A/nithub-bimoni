import styles from './Footer.module.css';

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <div className={styles.brand}>
          <div className={styles.logo}>SabiSpend</div>
          <p>AI money assistant for the real hustle. Built for Nigeria's traders and artisans.</p>
        </div>

        <div className={styles.cols}>
          <div className={styles.col}>
            <h5>Company</h5>
            <a href="#how-it-works">How it Works</a>
            <a href="#features">Features</a>
            <a href="#faq">FAQ</a>
          </div>
        </div>
      </div>
      <div className={styles.bottom}>
        <p>© 2026 SabiSpend. Powered by BMONI.</p>
      </div>
    </footer>
  );
}
