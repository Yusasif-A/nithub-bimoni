# Deploy ChopBeta Frontend to Firebase

## Prerequisites
✅ You already have a Firebase account

## Steps to Deploy

### 1. Install Firebase CLI (if not already installed)
```cmd
npm install -g firebase-tools
```

### 2. Login to Firebase
```cmd
firebase login
```
This will open your browser. Login with your Firebase account.

### 3. Initialize Firebase Project
```cmd
cd c:\Users\USER\Documents\Chop-beta\frontend-react
firebase init
```

When prompted:
- **Which Firebase features?** → Select **Hosting** (use spacebar to select)
- **Use an existing project** → Select your Firebase project
- **What do you want to use as your public directory?** → Type: `dist`
- **Configure as a single-page app?** → Type: `y` (yes)
- **Set up automatic builds with GitHub?** → Type: `n` (no)
- **Overwrite index.html?** → Type: `n` (no)

### 4. Build the React App
```cmd
npm run build
```
This creates the `dist` folder with your production-ready app.

### 5. Deploy to Firebase
```cmd
firebase deploy
```

✅ Your app will be live at: `https://YOUR_PROJECT_ID.web.app`

---

## Quick Redeploy (after making changes)

```cmd
cd c:\Users\USER\Documents\Chop-beta\frontend-react
npm run build
firebase deploy
```

---

## Update Firebase Project ID

Before deploying, update `.firebaserc` with your actual Firebase project ID:

```json
{
  "projects": {
    "default": "your-actual-project-id"
  }
}
```

Find your project ID at: https://console.firebase.google.com/

---

## Important Files

- `firebase.json` - Firebase hosting configuration (already created ✅)
- `.firebaserc` - Firebase project settings (update with your project ID)
- `dist/` - Production build folder (created by `npm run build`)

---

## Troubleshooting

**If you get "command not found: firebase"**
```cmd
npm install -g firebase-tools
```

**If login fails**
```cmd
firebase login --reauth
```

**To see your deployed site**
```cmd
firebase open hosting:site
```
