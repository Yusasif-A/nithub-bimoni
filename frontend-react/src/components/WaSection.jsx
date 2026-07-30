import WaIcon from './WaIcon';
import styles from './WaSection.module.css';

const WA = 'https://wa.me/2348020812523';

const steps = [
  { num: '1', color: 'green', title: 'Snap your receipt', desc: 'Take a photo of your sales slip, tally sheet, or payment note and send it on WhatsApp.' },
  { num: '2', color: 'amber', title: 'SabiSave reads it', desc: 'The assistant extracts the numbers and helps turn them into usable records.' },
  { num: '3', color: 'green', title: 'Get a clear summary', desc: 'Receive simple feedback that helps you understand what came in, what went out, and what remains.' },
];

function PhoneMockup() {
  return (
    <div className={styles.phoneWrap}>
      <div className={styles.phone}>
        <div className={styles.notch} />
        <div className={styles.screen}>
          <video
            className={styles.video}
            src="/assets/demo.mp4"
            autoPlay
            muted
            loop
            playsInline
            aria-label="SabiSave WhatsApp demo recording"
          />
        </div>
      </div>
    </div>
  );
}

export default function WaSection() {
  return (
    <section className={styles.section} id="how-it-works">
      <div className="container">
        <div className={styles.header}>
          <h2>The WhatsApp Experience</h2>
          <p>Simple, fast, and familiar. No new apps to download — just chat.</p>
        </div>
        <div className={styles.inner}>
          <PhoneMockup />
          <div className={styles.steps}>
            {steps.map(s => (
              <div key={s.num} className={styles.step}>
                <div className={`${styles.num} ${styles[s.color]}`}>{s.num}</div>
                <div>
                  <h4>{s.title}</h4>
                  <p>{s.desc}</p>
                </div>
              </div>
            ))}
            <a href={WA} className="btn-wa" target="_blank" rel="noopener noreferrer" style={{ marginTop: '8px' }}>
              <WaIcon size={20} />
              Start on WhatsApp
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
