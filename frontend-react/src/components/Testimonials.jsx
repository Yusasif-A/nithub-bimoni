import styles from './Testimonials.module.css';

const reviews = [
  {
    initials: 'FO',
    text: '"I was worried about my breast milk supply. ChopBeta suggested a specific balance of Akamu and healthy fats that actually worked."',
    name: 'Funmi O.',
    loc: 'New Mom in Ibadan',
  },
  {
    initials: 'CN',
    text: '"The growth tracker on WhatsApp is so easy. No complex charts to read — just clear messages telling me my baby is doing fine."',
    name: 'Chiamaka N.',
    loc: 'Mom of 2 in Enugu',
  },
  {
    initials: 'AA',
    text: '"Finally, an app that knows what Efo Riro is! I love the personalised recipes based on what\'s seasonal in Lagos."',
    name: 'Amina A.',
    loc: 'Expectant Mom in Lagos',
  },
];

export default function Testimonials() {
  return (
    <section className={styles.section} id="testimonials">
      <div className="container">
        <h2 className={styles.heading}>Real stories from real mothers</h2>
        <div className={styles.grid}>
          {reviews.map(r => (
            <div key={r.name} className={styles.card}>
              <div className={styles.stars}>★★★★★</div>
              <p className={styles.text}>{r.text}</p>
              <div className={styles.author}>
                <div className={styles.avatar}>{r.initials}</div>
                <div>
                  <div className={styles.name}>{r.name}</div>
                  <div className={styles.loc}>{r.loc}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
