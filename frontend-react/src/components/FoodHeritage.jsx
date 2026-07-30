import styles from './FoodHeritage.module.css';

const WA = 'https://wa.me/2349053458146';

export default function FoodHeritage() {
  return (
    <section className={styles.section} id="heritage">
      <div className="container">
        <div className={styles.grid}>
          <div className={styles.copy}>
            <h2>Honouring our food heritage</h2>
            <p>
              Our database contains over 2,000 authentic Nigerian dishes — from Eba and
              Egusi to Jollof. We understand exactly what goes into your pot, from the
              right spices to the local prep methods.
            </p>
            <div className={styles.stats}>
              <div className={styles.stat}>
                <span className={styles.statNum}>2,000+</span>
                <span className={styles.statLabel}>Dishes Analysed</span>
              </div>
              <div className={styles.stat}>
                <span className={styles.statNum}>36</span>
                <span className={styles.statLabel}>States Supported</span>
              </div>
            </div>
          </div>

          <div className={styles.imgWrap}>
            <img
              src="/assets/food-plait.png"
              alt="Authentic Nigerian food — Eba and Egusi soup"
              loading="lazy"
            />
          </div>
        </div>
      </div>
    </section>
  );
}
