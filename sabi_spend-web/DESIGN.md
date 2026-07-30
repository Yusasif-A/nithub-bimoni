---
name: Accessible Growth
colors:
  surface: '#f8f9ff'
  surface-dim: '#d1dbec'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eef4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dfe9fa'
  surface-container-highest: '#d9e3f4'
  on-surface: '#121c28'
  on-surface-variant: '#3f4941'
  inverse-surface: '#27313e'
  inverse-on-surface: '#eaf1ff'
  outline: '#6f7a70'
  outline-variant: '#bfc9bf'
  surface-tint: '#156c41'
  primary: '#005832'
  on-primary: '#ffffff'
  primary-container: '#1e7246'
  on-primary-container: '#a1f4bc'
  inverse-primary: '#87d8a2'
  secondary: '#006d2f'
  on-secondary: '#ffffff'
  secondary-container: '#5dfd8a'
  on-secondary-container: '#007232'
  tertiary: '#454c5d'
  on-tertiary: '#ffffff'
  tertiary-container: '#5d6476'
  on-tertiary-container: '#dbe1f7'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#a2f4bd'
  primary-fixed-dim: '#87d8a2'
  on-primary-fixed: '#00210f'
  on-primary-fixed-variant: '#00522e'
  secondary-fixed: '#66ff8e'
  secondary-fixed-dim: '#3de273'
  on-secondary-fixed: '#002109'
  on-secondary-fixed-variant: '#005322'
  tertiary-fixed: '#dce2f7'
  tertiary-fixed-dim: '#c0c6db'
  on-tertiary-fixed: '#141b2b'
  on-tertiary-fixed-variant: '#404758'
  background: '#f8f9ff'
  on-background: '#121c28'
  surface-variant: '#d9e3f4'
  background-surface: '#FDFCF6'
  voice-indicator: '#25D366'
  expense-red: '#DC2626'
  savings-gold: '#F59E0B'
typography:
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
  headline-lg-mobile:
    fontFamily: Hanken Grotesk
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Be Vietnam Pro
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
  body-md:
    fontFamily: Be Vietnam Pro
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 26px
  label-lg:
    fontFamily: Be Vietnam Pro
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.5px
  label-md:
    fontFamily: Be Vietnam Pro
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 18px
    letterSpacing: 1px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  gutter: 16px
  margin-mobile: 20px
  margin-desktop: 40px
  container-max: 600px
---

## Brand & Style

The design system is engineered for SabiSpend, an AI money assistant designed to bridge the gap between complex fintech and low-literacy users. The brand personality is **Empathetic, Capable, and Uplifting**. It moves away from the intimidating, data-dense interfaces of traditional banking and toward a familiar, chat-centric environment.

The design style is **Modern Tactile Minimalism**. It leverages high-contrast elements, generous whitespace, and "WhatsApp-first" familiarity to reduce cognitive load. The UI prioritizes visual cues (icons and color) over text, ensuring that users can navigate through shape recognition and intuitive spatial relationships. The emotional goal is to make the user feel like they are talking to a knowledgeable friend who helps them grow their money.

## Colors

The palette is anchored in **Trust and Growth**. The primary deep green (#1E7246) establishes authority and financial security, while the vibrant secondary green (#25D366) is used for action-oriented elements like "Save" or "Proceed," leveraging the familiarity of popular messaging apps.

The background uses a soft, warm off-white (#FDFCF6) to reduce eye strain and provide a "paper-like" tactile quality. High-contrast neutrals are reserved for text to ensure WCAG AA accessibility. 

- **Primary Green:** Used for headers, primary buttons, and successful financial states.
- **Vibrant Green:** Reserved for active voice recording states, incoming money, and "confirm" actions.
- **Deep Navy:** Used for primary text and critical navigation icons to ensure maximum legibility.
- **Functional Accents:** A distinct red and gold are used sparingly for "Money Out" and "Goals" to provide immediate visual categorization without requiring the user to read labels.

## Typography

Typography in this design system is treated as a functional tool first. **Hanken Grotesk** is chosen for headlines for its clarity and modern, open letterforms that remain legible even at high weights. **Be Vietnam Pro** is used for body and labels because of its friendly, approachable tone and excellent readability for non-native speakers or those with lower literacy levels.

**Key Principles:**
- **Size over Density:** Font sizes are larger than standard fintech apps (minimum 18px for body) to assist readability.
- **Weights:** Use Bold (700) and Semi-Bold (600) to create a clear visual hierarchy.
- **Line Height:** Generous leading (1.5x) ensures that users don't lose their place while reading short sentences.
- **Upper Case:** Avoid all-caps for long strings; use them only for short, 1-word labels to improve shape recognition.

## Layout & Spacing

This design system uses a **Conversation-Centric Fluid Grid**. The layout mimics the vertical flow of a chat application to provide a sense of continuity.

- **The Single Column Rule:** To prevent confusion, the main interaction area is a single-column stack on mobile. Elements never compete horizontally unless they are clearly defined icons or buttons in a 2-column grid.
- **The 8px Rhythm:** All spacing, padding, and margins are multiples of 8px. 
- **The "Safe Zone":** Primary actions (Voice/Photo upload) are always anchored to the bottom 25% of the screen, within easy reach of the thumb.
- **Max Width:** On larger screens, the content is capped at 600px and centered to maintain the intimacy of a mobile chat experience.

## Elevation & Depth

To maintain the "WhatsApp-first" feel, depth is created through **Tonal Layering and Soft Shadows** rather than complex gradients.

- **Surface Levels:** The main background is the base. Chat bubbles and cards sit on Level 1, using a subtle 2px blur shadow with 5% opacity to indicate they are tappable.
- **Active Elements:** The Voice Interaction button uses a "Pulse" elevation, where a secondary vibrant green ring expands from behind the button to indicate the AI is listening.
- **Modals:** Use a heavy backdrop blur (12px) to dim the background, focusing all attention on the current task (e.g., confirming a spend).
- **Physicality:** Input fields should feel "recessed" (slight inner shadow) when active, suggesting they are ready to be filled.

## Shapes

The shape language is **Soft and Friendly**. Sharp corners are avoided as they appear aggressive or technical.

- **Standard Elements:** Buttons and input fields use a 0.5rem (8px) radius.
- **Chat Bubbles:** Use a "Mixed Radius" approach—three corners at 16px and the corner pointing to the speaker at 4px—to clearly identify who is talking.
- **Data Visualization:** Profit and savings bars use fully rounded (pill-shaped) ends to feel more organic and less like "accounting software."
- **Icons:** All icons must be enclosed in circular or "squircle" containers to make them feel like distinct, touchable buttons.

## Components

### 1. Voice & Interaction Indicators
- **The "Listen" Button:** A large circular button with a microphone icon. When active, it triggers a "Sound Wave" animation using the secondary vibrant green.
- **AI Typing State:** A simple three-dot pulse within a chat bubble to show the AI is processing the user's voice or photo.

### 2. Photo-Upload "Receipt" States
- **The Camera Trigger:** A persistent icon in the input bar. 
- **Processing Card:** Once a photo is taken, a card appears with a thumbnail and a "Reading your receipt..." progress bar using the primary green.

### 3. Data Visualizations (Simplified)
- **Growth Bars:** Vertical bars with pill-shaped ends. Current savings are shown in Vibrant Green, while the "Goal" is shown as a dashed outline.
- **The "Money In/Out" Toggle:** A large, two-segment switch with high-contrast icons (Arrow Up/Down).

### 4. High-Contrast Buttons
- **Primary Action:** Solid Primary Green with White text.
- **Secondary Action:** Thick 2px border in Primary Green with Green text.
- **Destructive Action:** Solid Red background with White text, used only for "Delete" or "Cancel."

### 5. Chat-Style Input
- A fixed bottom bar containing a text field, camera icon, and the prominent Voice button. This provides a constant "home base" for the user to interact with the AI.