import styles from './Foods.module.css';

const foods = [
  { name: 'Egusi Soup', img: 'https://upload.wikimedia.org/wikipedia/commons/8/81/Pounded_Yam_and_Egusi_Soup.jpg' },
  { name: 'Egusi & Assorted', img: 'https://images.unsplash.com/photo-1763048443535-1243379234e2?fm=jpg&q=60&w=300&auto=format&fit=crop' },
  { name: 'Pounded Yam', img: 'https://images.pexels.com/photos/33853773/pexels-photo-33853773.jpeg?auto=compress&cs=tinysrgb&w=300' },
  { name: 'Amala & Ewedu', img: 'https://images.pexels.com/photos/35094454/pexels-photo-35094454.jpeg?auto=compress&cs=tinysrgb&w=300' },
  { name: 'Jollof Rice', img: 'https://images.pexels.com/photos/34603258/pexels-photo-34603258.jpeg?auto=compress&cs=tinysrgb&w=300' },
  { name: 'Moi Moi', img: 'https://images.unsplash.com/photo-1680878903102-92692799ef36?fm=jpg&q=60&w=300&auto=format&fit=crop' },
];

export default function Foods() {
  return (
    <section className={styles.foods} id="foods">
      <div className="container">
        <div className="section-label">Nigerian Foods, Nigerian Solutions</div>
        <h2>Built for your kitchen</h2>
        <p className="lead">ChopBeta recognises the foods on your table — not just &ldquo;African cuisine&rdquo; in general. Real foods. Real Nigerian homes.</p>
        <div className={styles.grid}>
          {foods.map((f) => (
            <div key={f.name} className={styles.chip}>
              <img src={f.img} alt={f.name} loading="lazy" />
              <span>{f.name}</span>
            </div>
          ))}
        </div>
        <p className={styles.more}>
          Don&apos;t see your food?{' '}
          <a href="https://wa.me/2349053458146" target="_blank" rel="noopener noreferrer">
            Ask us on WhatsApp →
          </a>
        </p>
      </div>
    </section>
  );
}
