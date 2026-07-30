import styles from './TrustStrip.module.css';

const items = [
  { icon: '⭐', text: '200+ Nigerian foods recognized' },
  { icon: '📋', text: 'NFCMS 2021 Database' },
  { icon: '✅', text: 'Yoruba · Hausa · Igbo · Pidgin' },
  { icon: '📱', text: 'Works on WhatsApp — no download' },
];

export default function TrustStrip() {
  return (
    <div className={styles.strip}>
      {items.map((item) => (
        <div key={item.text} className={styles.item}>
          <span>{item.icon}</span>
          {item.text}
        </div>
      ))}
    </div>
  );
}
