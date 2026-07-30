import styles from './Stats.module.css';

const stats = [
  { number: 'Fast', label: 'Simple WhatsApp-first money tracking' },
  { number: 'Local', label: 'Built for Nigerian traders and market women', note: 'SabiSave' },
  { number: 'Clear', label: 'Receipt photos turned into usable records' },
  { number: 'Private', label: 'Your chats stay between you and the assistant' },
];

export default function Stats() {
  return (
    <section className={styles.stats}>
      <div className="container">
        <div className={styles.label}>Why people use SabiSave</div>
        <h2 className={styles.h2}>Simple money help for everyday hustle</h2>
        <p className={styles.lead}>SabiSave exists to make tracking income, spending, and savings feel easy instead of stressful.</p>
        <div className={styles.grid}>
          {stats.map((s) => (
            <div key={s.number} className={styles.item}>
              <span className={styles.number}>{s.number}</span>
              <div className={styles.itemLabel}>{s.label}</div>
              {s.note && <div className={styles.note}>{s.note}</div>}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
