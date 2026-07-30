import { useEffect } from 'react';
import styles from './LegalPage.module.css';

export default function TermsOfUse() {
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  return (
    <div className={styles.container}>
      <a href="/" className={styles.backLink}>← Back to Home</a>

      <h1>SabiSave Terms of Use</h1>
      <p className={styles.lastUpdated}>Last updated: 30 July 2026</p>

      <p>These Terms of Use ("Terms") govern your access to and use of SabiSave, a WhatsApp-based AI money assistant provided to traders, market women, and small business owners in Nigeria ("SabiSave," "we," "us," or "our"). By messaging or otherwise using SabiSave, you agree to these Terms. If you do not agree, please do not use SabiSave.</p>

      <h2>1. What SabiSave Is</h2>
      <p>SabiSave provides money-management guidance through WhatsApp, including help with tracking sales, spending, and savings goals based on information you provide.</p>

      <h2>2. Not Financial Advice</h2>
      <p>SabiSave provides general money-management information only. It is not a substitute for professional financial, accounting, legal, or tax advice. You are responsible for your own business and financial decisions.</p>

      <h2>3. Who Can Use SabiSave</h2>
      <p>SabiSave is intended for use by adults, including traders, market women, and small business owners. Any information you provide about your business, spending, or savings must be accurate to the best of your knowledge.</p>

      <h2>4. Your Responsibilities</h2>
      <p>When using SabiSave, you agree to:</p>
      <ul>
        <li>Provide accurate information, to the best of your knowledge</li>
        <li>Use SabiSave only for its intended purpose of receiving money-management guidance</li>
        <li>Not use SabiSave for any unlawful, harmful, or abusive purpose</li>
      </ul>

      <h2>5. Availability of the Service</h2>
      <p>We aim to keep SabiSave available and useful, but we do not guarantee that it will always be available, accurate, or error-free. We may update, suspend, or discontinue SabiSave, in whole or in part, at any time.</p>

      <h2>6. Limitation of Liability</h2>
      <p>SabiSave is provided on an "as is" basis. To the fullest extent permitted by law, we are not liable for any loss, harm, or damage arising from your use of SabiSave, including reliance on any money-management information provided. Nothing in these Terms limits any liability that cannot be limited under Nigerian law.</p>

      <h2>7. Your Data</h2>
      <p>Our collection and use of your personal information is described in our <a href="/privacy-policy">Privacy Policy</a>, which forms part of these Terms.</p>

      <h2>8. Ending Your Use of SabiSave</h2>
      <p>You may stop using SabiSave at any time, simply by no longer messaging it. We may also suspend or end your access to SabiSave if we reasonably believe you have misused the service or violated these Terms.</p>

      <h2>9. Changes to These Terms</h2>
      <p>We may update these Terms from time to time as SabiSave grows or as required by law. We will notify you of significant changes through WhatsApp. Continuing to use SabiSave after such changes means you accept the updated Terms.</p>

      <h2>10. Governing Law</h2>
      <p>These Terms are governed by the laws of the Federal Republic of Nigeria.</p>

      <h2>11. Contact Us</h2>
      <div className={styles.contact}>
        <p>If you have any questions about these Terms, please contact us:</p>
        <p><strong>Email:</strong> support@sabisave.com</p>
      </div>
    </div>
  );
}
