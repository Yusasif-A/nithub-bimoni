import styles from './HowItWorks.module.css';

const steps = [
  {
    num: '01',
    title: 'Send a WhatsApp message',
    desc: 'Tell us what you need or send a photo of your meal. We reply in Yoruba, Hausa, Igbo, Pidgin, or English — your choice.',
    img: 'https://images.unsplash.com/photo-1680878903102-92692799ef36?fm=jpg&q=70&w=500&auto=format&fit=crop',
    alt: 'Woman using WhatsApp on phone Nigeria',
  },
  {
    num: '02',
    title: 'Instant food analysis',
    desc: 'ChopBeta identifies your Nigerian food — Egusi, Oha, Okra, Moi Moi — and breaks down exactly what nutrients you and your baby get.',
    img: 'https://upload.wikimedia.org/wikipedia/commons/8/81/Pounded_Yam_and_Egusi_Soup.jpg',
    alt: 'Pounded yam and egusi soup Nigerian food',
  },
  {
    num: '03',
    title: 'Personalised meal plan',
    desc: 'Get a 3–7 day meal plan using ingredients already in your kitchen. Tailored to your region, budget, and your baby\'s age.',
    img: 'https://images.pexels.com/photos/34370433/pexels-photo-34370433.jpeg?auto=compress&cs=tinysrgb&w=500',
    alt: 'Nigerian woman cooking outdoors with traditional pot — meal planning',
  },
  {
    num: '04',
    title: 'Baby growth tracking',
    desc: 'Track your baby\'s weight against WHO growth curves. Early warning alerts catch malnutrition before it becomes critical.',
    img: 'https://images.unsplash.com/flagged/photo-1551049215-23fd6d2ac3f1?fm=jpg&q=70&w=500&auto=format&fit=crop',
    alt: 'Nurse putting baby on weighing scale — growth tracking',
  },
];

export default function HowItWorks() {
  return (
    <section className={styles.how} id="how">
      <div className="container">
        <div className="section-label">How it works</div>
        <h2>Your AI Nutrition Companion — in 4 simple steps</h2>
        <p className="lead">No app to download. No complicated setup. Just WhatsApp — the one you already use every day.</p>
        <div className={styles.grid}>
          {steps.map((s) => (
            <div key={s.num} className={styles.step}>
              <div className={styles.num}>{s.num}</div>
              <h3>{s.title}</h3>
              <p>{s.desc}</p>
              {s.img && <img src={s.img} alt={s.alt} loading="lazy" />}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
