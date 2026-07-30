import WaIcon from './WaIcon';
import styles from './Hero.module.css';

const WA = 'https://wa.me/2348020812523';

export default function Hero() {
  return (
    <section className={styles.hero}>
      <div className="container">
        <div className={styles.grid}>
          <div className={styles.copy}>
            <span className="label-tag green">WhatsApp-first money help</span>
            <h1>Track money. Save smarter.</h1>
            <p>
              SabiSave helps you capture sales, spending, and savings in one easy WhatsApp flow.
              Send a photo, type a message, or just ask what to do next.
            </p>
            <div className={styles.btns}>
              <a href={WA} className="btn-wa" target="_blank" rel="noopener noreferrer">
                <WaIcon size={20} />
                Start on WhatsApp
              </a>
              <a href="#how-it-works" className="btn-outline">How it Works</a>
            </div>
          </div>
          <div className={styles.imgWrap}>
            <img src="/assets/first-page-image.png" alt="Person using SabiSave on WhatsApp" loading="eager" />
          </div>
        </div>
      </div>
    </section>
  );
}
