import styles from './Pain.module.css';

const langs = ['English', 'Yoruba', 'Igbo', 'Hausa', 'Pidgin'];

export default function Pain() {
  return (
    <section className={styles.section}>
      <div className="container">
        <div className={styles.grid}>

          {/* Left — challenge stat */}
          <div className={styles.left}>
            <span className="label-tag red">The Challenge</span>
            <h2>1 in 5 children in<br />Nigeria face malnutrition.</h2>
            <p>
              We exist to change this statistic. By empowering mothers with the right knowledge at
              the right time, we&apos;re building a healthier future for the next generation of Nigerians.
            </p>
            <div className={styles.card}>
              <div className={styles.cardTop}>
                <span className={styles.badge}>Critical Window</span>
                <h3>The First 1,000 Days</h3>
              </div>
              <p>
                From pregnancy to age two, we monitor your child&apos;s health throughout this critical
                window, following WHO and UNICEF recommendations.
              </p>
              <div className={styles.cardFoot}>
                <span className={styles.footIcon}>🌍</span>
                <p>Our Mission: Expert nutrition for every Nigerian mother, growing with your child.</p>
              </div>
            </div>
          </div>

          {/* Right — language grid */}
          <div className={styles.right}>
            <h2>Breaking language barriers</h2>
            <p>
              Nutrition advice shouldn&apos;t be complicated. That&apos;s why ChopBeta speaks your language.
              Get expert guidance the way you&apos;re most comfortable.
            </p>
            <div className={styles.langGrid}>
              {langs.map(l => (
                <div key={l} className={styles.langChip}>{l}</div>
              ))}
            </div>
            <div className={styles.more}>
              <span>🌐</span>
              <span>More languages coming soon</span>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
