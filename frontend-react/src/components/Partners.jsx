import WaIcon from './WaIcon';
import styles from './Partners.module.css';

const WA = 'https://wa.me/2348020812523';

export default function Partners() {
  return (
    <section className={styles.section} id="partners">
      <div className="container">
        <div className={styles.inner}>
          <img
            src="/assets/mother-and-child.png"
            alt="Nigerian business owner using WhatsApp for money management"
            loading="lazy"
          />
          <div>
            <div className="section-label">For teams and partners</div>
            <h2>Bring SabiSave to more people</h2>
            <p>Community groups, NGOs, and financial partners can use SabiSave to reach more users through a simple WhatsApp flow.</p>
            <p>It gives people a familiar interface for money tracking, saving goals, and everyday support.</p>
            <ul className={styles.features}>
              <li><span className={styles.icon}>🔔</span><span>Simple alerts and reminders on WhatsApp</span></li>
              <li><span className={styles.icon}>📍</span><span>Easy-to-follow support for local users</span></li>
              <li><span className={styles.icon}>📈</span><span>Clear reporting for engagement and usage</span></li>
            </ul>
            <a href={WA} className="btn-wa-lg" target="_blank" rel="noopener noreferrer">
              <WaIcon size={20} />
              Partner with us
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
