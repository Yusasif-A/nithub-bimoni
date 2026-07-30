import styles from './Comparison.module.css';

const without = [
  'Generic finance apps that feel confusing on a small phone',
  'Advice built for another market and another language',
  'No clear way to track cash flow, spending, or savings goals',
  'Messages that make you guess what to do next',
  'No simple way to turn receipts into useful records',
];

const with_ = [
  'Uses WhatsApp, the app people already know',
  'Replies in Yoruba, Hausa, Igbo, Pidgin, or English',
  'Tracks spending, sales, and savings in one place',
  'Turns chats and receipts into simple action steps',
  'Keeps the flow easy for busy traders and market women',
];

function Clipboard({ label, items, variant }) {
  return (
    <div className={`${styles.board} ${styles[variant]}`}>
      <div className={styles.clip}>
        <div className={styles.clipScrew} />
        <div className={styles.clipBody} />
        <div className={styles.clipJaw} />
      </div>
      <div className={styles.paper}>
        <span className={styles.tag}>{label}</span>
        <ul className={styles.list}>
          {items.map((item, i) => (
            <li key={i} className={styles.item}>{item}</li>
          ))}
        </ul>
        <div className={styles.curl} />
      </div>
    </div>
  );
}

export default function Comparison() {
  return (
    <section className={styles.section}>
      <div className="container">
        <div className="section-label">Why SabiSave?</div>
        <h2>Other apps vs. SabiSave</h2>
        <p className="lead">Most finance tools were built for someone else. SabiSave was built for real everyday hustle.</p>
        <div className={styles.boards}>
          <Clipboard label="Other apps" items={without} variant="bad" />
          <Clipboard label="With SabiSave" items={with_} variant="good" />
        </div>
      </div>
    </section>
  );
}
