import styles from './Features.module.css';

const points = [
  'WHO & UNICEF aligned growth monitoring',
  'Expert-led postnatal and infant nutrition tracking',
  'Pediatrician-approved meal plans for every milestone',
];

export default function Features() {
  return (
    <section className={styles.section}>
      <div className="container">
        <div className={styles.grid}>
          <div className={styles.imgWrap}>
            <img src="/assets/mother-and-child.png" alt="Mother with baby — clinical care" loading="lazy" />
          </div>
          <div className={styles.copy}>
            <span className="label-tag green">Clinical Excellence</span>
            <h2>Clinical Excellence for the First 1,000 Days</h2>
            <p>
              We bridge the gap between medical expertise and the realities of Nigerian
              motherhood. Our platform provides culturally-relevant support that grows
              with your child, ensuring they thrive from conception to their second birthday.
            </p>
            <ul className={styles.list}>
              {points.map(pt => (
                <li key={pt}>
                  <span className={styles.check}>✓</span>
                  <span>{pt}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
