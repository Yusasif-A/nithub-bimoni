import { useEffect } from 'react';
import styles from './LegalPage.module.css';

export default function PrivacyPolicy() {
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  return (
    <div className={styles.container}>
      <a href="/" className={styles.backLink}>← Back to Home</a>

      <h1>SabiSave Privacy Policy</h1>
      <p className={styles.lastUpdated}>Last updated: 30 July 2026</p>

      <p>SabiSave ("SabiSave," "we," "us," or "our") is a WhatsApp-based AI money assistant that helps traders, market women, and small business owners in Nigeria track spending, understand sales, and save safely. This Privacy Policy explains what personal data we collect when you use SabiSave, why we collect it, who we share it with, and the choices and rights you have. By using SabiSave on WhatsApp, you agree to the practices described in this Policy.</p>

      <h2>1. Who We Are</h2>
      <p>SabiSave is a money assistant delivered through WhatsApp, built for everyday business owners in Nigeria. We process personal data in accordance with the Nigeria Data Protection Act, 2023 (NDPA).</p>

      <h2>2. Information We Collect</h2>
      <p>When you use SabiSave, we may collect:</p>
      <ul>
        <li>Your phone number and name</li>
        <li>Voice messages you send us</li>
        <li>Photos of receipts, sales records, or other documents you share for analysis</li>
        <li>Your chat messages and conversation history</li>
        <li>Transaction and savings details you provide</li>
        <li>Your preferred language</li>
        <li>Feedback you give us about the service</li>
      </ul>

      <h2>3. How We Use Your Information</h2>
      <p>We use the information we collect to:</p>
      <ul>
        <li>Identify you and send you messages on WhatsApp, using your phone number and name</li>
        <li>Understand and respond to your money questions, using your voice messages and receipt photos</li>
        <li>Help you track income, expenses, and savings goals based on the details you provide</li>
        <li>Respond to you in your preferred language</li>
        <li>Maintain context across your conversations with SabiSave, using your chat history</li>
      </ul>
      <p>We do not use your information for any purpose beyond providing and improving the SabiSave service.</p>

      <h2>4. Sensitive Information</h2>
      <p>Some of the information you share with SabiSave may reveal financial or personal details. We treat this information with care and only use it to provide you with money-management guidance and related service features.</p>

      <h2>5. The Platform We Operate On</h2>
      <p>SabiSave operates on the WhatsApp Business Platform. WhatsApp/Meta is the messaging channel through which you interact with SabiSave, not a party we choose to share your information with for their own purposes.</p>

      <h2>6. Who We Share Your Information With</h2>
      <p>We share your information with the following categories of technical service providers, who process it on our behalf under data protection obligations and are only permitted to use it to deliver these services:</p>
      <ul>
        <li>Cloud database providers to securely store your data</li>
        <li>AI processing partners to process speech, extract text from photos, and help answer your questions</li>
      </ul>
      <p>We never share your information with marketers or unrelated third parties, and we do not sell your personal information.</p>

      <h2>7. Cross-Border Processing</h2>
      <p>In some instances, your information may be processed outside Nigeria by our technical service providers. Where this happens, we take reasonable steps to ensure such transfers are protected in line with the requirements of the Nigeria Data Protection Act, 2023.</p>

      <h2>8. How Long We Keep Your Information</h2>
      <p>We keep your information for as long as your account remains active. You may request deletion of your information at any time, as described in Section 9 below.</p>

      <h2>9. Your Rights and Choices</h2>
      <p>You have the right to:</p>
      <ul>
        <li>View the personal information we hold about you</li>
        <li>Correct any information that is inaccurate or outdated</li>
        <li>Request deletion of your information at any time</li>
      </ul>
      <p>To exercise any of these rights, contact us using the details in Section 11 below, or message us directly on WhatsApp.</p>

      <h2>10. Children's Information</h2>
      <p>SabiSave is intended for use by adults, including traders, market women, and small business owners. Information about dependents or family members is provided by the user for the purpose of service support and is not collected directly from children.</p>

      <h2>11. Contact Us</h2>
      <div className={styles.contact}>
        <p>If you have any questions about this Privacy Policy or wish to exercise your rights, please contact us:</p>
        <p><strong>Email:</strong> support@sabisave.com</p>
      </div>

      <h2>12. Changes to This Policy</h2>
      <p>We may update this Privacy Policy from time to time as SabiSave grows or as required by law. We will notify you of significant changes through WhatsApp.</p>
    </div>
  );
}
