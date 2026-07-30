import WaIcon from './WaIcon';
import styles from './FinalCTA.module.css';

const WA = 'https://wa.me/2349053458146';

export default function FinalCTA() {
  return (
    <section className={styles.section}>
      <div className="container">
        <div className={styles.box}>
          <div className={styles.glow1} />
          <div className={styles.glow2} />
          <div className={styles.inner}>
            <h2 className={styles.h2}>Ready to Nourish Your Family?</h2>
            <p className={styles.p}>
              Join thousands of Nigerian mothers getting expert advice daily.
              No subscriptions, no hidden fees — just pure care via WhatsApp.
            </p>
            <a href={WA} className={styles.btn} target="_blank" rel="noopener noreferrer">
              <WaIcon size={22} />
              Start on WhatsApp Now
            </a>
            <p className={styles.sub}>+234 905 345 8146 · Free to message · Works on any phone</p>
          </div>
        </div>
      </div>
    </section>
  );
}
