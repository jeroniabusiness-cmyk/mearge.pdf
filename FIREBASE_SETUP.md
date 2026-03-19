# Firebase Setup Guide

## Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add Project"
3. Enter project name: `telegram-pdf-bot`
4. Disable Google Analytics (optional)
5. Click "Create Project"

## Step 2: Enable Firestore

1. In Firebase Console, click "Firestore Database"
2. Click "Create Database"
3. Select "Start in production mode"
4. Choose your location (closest to your users)
5. Click "Enable"

## Step 3: Get Service Account Key

1. Go to Project Settings (gear icon)
2. Click "Service Accounts" tab
3. Click "Generate New Private Key"
4. Click "Generate Key"
5. Save downloaded JSON file as `config/firebase-credentials.json`

## Step 4: Security Rules (Optional)

In Firestore Rules tab, use:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if false; // Only server-side access
    }
  }
}
```

## Step 5: Indexes

Firestore will automatically create indexes when queries run for the first time.

## Verification

Test Firebase connection:
```bash
python -c "from database.firebase_config import FirebaseConfig; FirebaseConfig.initialize(); print('✅ Firebase connected!')"
```

## Troubleshooting

**Error: Default credentials not found**
- Verify `firebase-credentials.json` exists in `config/` folder
- Check path in `.env` file

**Error: Permission denied**
- Check Firestore rules
- Verify service account has correct permissions

**Error: Project not found**
- Verify project ID in Firebase console
- Check internet connection
