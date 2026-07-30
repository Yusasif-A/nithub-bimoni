import { useState } from 'react';
import styles from './FAQ.module.css';

const items = [
  { q: 'Do I need to download an app?', a: 'No. SabiSave runs entirely on WhatsApp, so you can start without installing anything new.' },
  { q: 'Which languages does SabiSave support?', a: 'Yoruba, Hausa, Igbo, Nigerian Pidgin, and English. Just tell us your preferred language in your first message.' },
  { q: 'What does SabiSave help me track?', a: 'It helps you follow sales, spending, and savings goals with simple chats and receipt photos.' },
  { q: 'How does savings tracking work?', a: 'Share what you earned or spent and SabiSave helps you keep a clear record and spot patterns over time.' },
  { q: 'Is it free?', a: 'The core money tracking features are free to start. Extra premium features can be added later if needed.' },
  { q: 'Is my data private?', a: 'Your conversations stay between you and SabiSave. We do not sell your data.' },
  { q: 'What if SabiSave does not recognise my receipt?', a: 'Just describe the details in your message and SabiSave will still help organize the information.' },
];

function FaqItem({ q, a }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={styles.item}>
      <button className={styles.q} onClick={() => setOpen(!open)} aria-expanded={open}>
        {q}
        <span className={styles.toggle}>{open ? '−' : '+'}</span>
      </button>
      {open && <p className={styles.a}>{a}</p>}
    </div>
  );
}

export default function FAQ() {
  return (
    <section className={styles.section} id="faq">
      <div className="container">
        <div className="section-label">Common questions</div>
        <h2>Things people ask us</h2>
        <p className="lead" style={{ marginBottom: 40 }}>Can&apos;t find your answer? Message us on WhatsApp — we reply fast.</p>
        <div className={styles.list}>
          {items.map((item) => (
            <FaqItem key={item.q} {...item} />
          ))}
        </div>
      </div>
    </section>
  );
}
