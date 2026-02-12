# Day 01: Troubleshooting Guide (Firebase/Firestore)

This document provides solutions to common issues encountered during Day 01 Firebase/Firestore setup.

---

## 🔥 Firebase Setup Issues

### ❌ Problem: "Firebase project not found"

**Error Message:**
```
google.api_core.exceptions.PermissionDenied: 403 Project 'your-project-id' not found or permission denied.
```

**Cause:** Incorrect project ID or service account doesn't have access

**Solution:**
```bash
# 1. Verify project ID in Firebase Console
# Go to Project Settings → General → Project ID

# 2. Check .env file
cat .env | grep FIREBASE_PROJECT_ID

# 3. Verify service account key
python -c "import json; print(json.load(open('serviceAccountKey.json'))['project_id'])"

# 4. Ensure service account has proper roles:
# - Firebase Admin SDK Administrator Service Agent
# - Cloud Datastore User
```

**Prevention:** Double-check project ID when creating Firebase project

---

### ❌ Problem: "Service account key not found"

**Error Message:**
```
FileNotFoundError: [Errno 2] No such file or directory: './serviceAccountKey.json'
```

**Cause:** Service account key file missing or incorrect path

**Solution:**
```bash
# 1. Check if file exists
ls -la serviceAccountKey.json

# 2. Verify path in .env
cat .env | grep FIREBASE_PRIVATE_KEY_PATH

# 3. Download new key if needed:
# Firebase Console → Project Settings → Service Accounts → Generate New Private Key

# 4. Move to correct location
mv ~/Downloads/your-project-firebase-adminsdk-*.json ./serviceAccountKey.json

# 5. Update .env
echo "FIREBASE_PRIVATE_KEY_PATH=./serviceAccountKey.json" >> .env
```

**Prevention:** Add serviceAccountKey.json to .gitignore immediately

---

### ❌ Problem: "Firebase app already initialized"

**Error Message:**
```
ValueError: The default Firebase app already exists.
```

**Cause:** Attempting to initialize Firebase Admin SDK multiple times

**Solution:**
```python
# services/firebase_service.py
import firebase_admin
from firebase_admin import credentials

# Check if already initialized
if not firebase_admin._apps:
    cred = credentials.Certificate('serviceAccountKey.json')
    firebase_admin.initialize_app(cred)
else:
    print("Firebase already initialized")
```

**Prevention:** Use singleton pattern for Firebase service

---

### ❌ Problem: "Invalid service account credentials"

**Error Message:**
```
google.auth.exceptions.DefaultCredentialsError: Could not automatically determine credentials.
```

**Cause:** Malformed or invalid service account key JSON

**Solution:**
```bash
# 1. Validate JSON format
python -c "import json; json.load(open('serviceAccountKey.json'))"

# 2. Check required fields
python -c "
import json
key = json.load(open('serviceAccountKey.json'))
required = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
missing = [f for f in required if f not in key]
print('Missing fields:', missing if missing else 'None')
"

# 3. Re-download service account key if corrupted
```

**Prevention:** Don't manually edit service account key file

---

## 🗄️ Firestore Issues

### ❌ Problem: "Firestore not enabled"

**Error Message:**
```
google.api_core.exceptions.FailedPrecondition: 400 Cloud Firestore API has not been used in project...
```

**Cause:** Firestore Database not enabled in Firebase project

**Solution:**
```bash
# 1. Go to Firebase Console
# 2. Navigate to Build → Firestore Database
# 3. Click "Create database"
# 4. Choose production mode
# 5. Select location (cannot be changed later!)
# 6. Click "Enable"

# Wait 1-2 minutes for Firestore to be provisioned
```

**Prevention:** Enable Firestore during initial Firebase project setup

---

### ❌ Problem: "Permission denied" when writing to Firestore

**Error Message:**
```
google.api_core.exceptions.PermissionDenied: 403 Missing or insufficient permissions.
```

**Cause:** Firestore security rules blocking access

**Solution:**
```javascript
// Temporary fix for development (firestore.rules)
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if true;  // ⚠️ DEVELOPMENT ONLY!
    }
  }
}

// Deploy rules
firebase deploy --only firestore:rules
```

**Proper Solution:**
```javascript
// Production-ready rules
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    match /skills/{skillId} {
      allow read: if request.auth != null;
      allow write: if false;  // Only Cloud Functions
    }
  }
}
```

**Prevention:** Set up proper security rules from the start

---

### ❌ Problem: "Document not found" after creation

**Error Message:**
```
None returned when getting document
```

**Cause:** Asynchronous write not completed or incorrect document ID

**Solution:**
```python
from google.cloud import firestore
import time

# Option 1: Add small delay
doc_ref = db.collection('users').add(data)
time.sleep(0.1)  # Wait for write to complete
doc = doc_ref[1].get()

# Option 2: Use set() with known ID
doc_id = 'user_123'
db.collection('users').document(doc_id).set(data)
doc = db.collection('users').document(doc_id).get()

# Option 3: Check if document exists
doc = db.collection('users').document(doc_id).get()
if doc.exists:
    print(doc.to_dict())
else:
    print("Document not found")
```

**Prevention:** Always check `doc.exists` before accessing data

---

### ❌ Problem: "Firestore query returns empty results"

**Error Message:**
```
No documents found matching query
```

**Cause:** Incorrect query syntax or missing index

**Solution:**
```python
# Check 1: Verify collection has documents
docs = db.collection('users').limit(1).stream()
print("Collection has documents:", len(list(docs)) > 0)

# Check 2: Simplify query
# Instead of:
docs = db.collection('users').where('role', '==', 'developer').where('active', '==', True).stream()

# Try:
docs = db.collection('users').where('role', '==', 'developer').stream()

# Check 3: Check for index requirement
# If error mentions "requires an index", create composite index:
# Firebase Console → Firestore → Indexes → Create Index
```

**Prevention:** Create indexes for complex queries

---

## 🔐 Authentication Issues

### ❌ Problem: "Firebase Auth not enabled"

**Error Message:**
```
firebase_admin._auth_utils.UserNotFoundError: No user record found for the provided identifier.
```

**Cause:** Firebase Authentication not enabled

**Solution:**
```bash
# 1. Go to Firebase Console
# 2. Navigate to Build → Authentication
# 3. Click "Get started"
# 4. Enable "Email/Password" sign-in method
# 5. Click "Save"
```

**Prevention:** Enable Authentication during initial setup

---

### ❌ Problem: "Weak password" when creating user

**Error Message:**
```
firebase_admin.auth.InvalidArgumentError: Password must be at least 6 characters long.
```

**Cause:** Password doesn't meet Firebase requirements

**Solution:**
```python
# Validate password before creating user
def validate_password(password):
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters")
    return True

# Create user with validated password
if validate_password(password):
    user = auth.create_user(email=email, password=password)
```

**Prevention:** Implement password validation in API

---

### ❌ Problem: "Email already exists"

**Error Message:**
```
firebase_admin.auth.EmailAlreadyExistsError: The email address is already in use by another account.
```

**Cause:** Attempting to create user with existing email

**Solution:**
```python
from firebase_admin import auth
from firebase_admin._auth_utils import EmailAlreadyExistsError

try:
    user = auth.create_user(email=email, password=password)
except EmailAlreadyExistsError:
    # Option 1: Return error to user
    return {"error": "Email already registered"}
    
    # Option 2: Get existing user
    user = auth.get_user_by_email(email)
    return {"message": "User already exists", "uid": user.uid}
```

**Prevention:** Check if email exists before creating user

---

## 🐍 Python/Dependencies Issues

### ❌ Problem: "Module not found: firebase_admin"

**Error Message:**
```
ModuleNotFoundError: No module named 'firebase_admin'
```

**Cause:** Firebase Admin SDK not installed

**Solution:**
```bash
# 1. Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 2. Install firebase-admin
pip install firebase-admin==6.3.0

# 3. Verify installation
pip list | grep firebase

# 4. Update requirements.txt
pip freeze > requirements.txt
```

**Prevention:** Always activate virtual environment before installing packages

---

### ❌ Problem: "ImportError: cannot import name 'firestore'"

**Error Message:**
```
ImportError: cannot import name 'firestore' from 'firebase_admin'
```

**Cause:** Incorrect import statement

**Solution:**
```python
# ❌ Wrong
from firebase_admin import firestore
db = firestore.client()

# ✓ Correct
from firebase_admin import firestore
db = firestore.client()

# OR

from google.cloud import firestore
db = firestore.Client()
```

**Prevention:** Use correct import syntax from documentation

---

### ❌ Problem: "Virtual environment not activated"

**Symptoms:**
- Packages installed globally
- Different Python version
- Module not found errors

**Solution:**
```bash
# Check if venv is activated
which python  # Should show path to venv/bin/python

# If not activated:
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Verify
python --version
which pip
```

**Prevention:** Always activate venv before working

---

## 🌐 API Issues

### ❌ Problem: "FastAPI server won't start"

**Error Message:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Cause:** FastAPI not installed

**Solution:**
```bash
# Install FastAPI and uvicorn
pip install fastapi==0.109.0 uvicorn==0.27.0

# Start server
uvicorn main:app --reload --port 8000
```

**Prevention:** Install all dependencies from requirements.txt

---

### ❌ Problem: "Port 8000 already in use"

**Error Message:**
```
OSError: [Errno 48] Address already in use
```

**Cause:** Another process using port 8000

**Solution:**
```bash
# Option 1: Kill process on port 8000
# Linux/Mac
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Option 2: Use different port
uvicorn main:app --reload --port 8001
```

**Prevention:** Stop server before starting new instance

---

### ❌ Problem: "CORS error in browser"

**Error Message:**
```
Access to fetch at 'http://localhost:8000/api/users' from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Cause:** CORS not configured in FastAPI

**Solution:**
```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ For development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# For production, specify exact origins:
# allow_origins=["https://yourdomain.com"]
```

**Prevention:** Configure CORS during initial API setup

---

### ❌ Problem: "422 Validation Error"

**Error Message:**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Cause:** Missing required field in request body

**Solution:**
```bash
# Check request body includes all required fields
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123456!",
    "username": "testuser"
  }'

# Verify Pydantic model
class UserCreate(BaseModel):
    email: str  # Required
    password: str  # Required
    username: str  # Required
    displayName: Optional[str] = None  # Optional
```

**Prevention:** Use Pydantic models for validation

---

## 🔧 Environment Issues

### ❌ Problem: "Environment variables not loading"

**Error Message:**
```
KeyError: 'FIREBASE_PROJECT_ID'
```

**Cause:** .env file not loaded or incorrect path

**Solution:**
```python
# Ensure python-dotenv is installed
pip install python-dotenv

# Load .env at the start of your script
from dotenv import load_dotenv
import os

load_dotenv()  # Load .env from current directory

# Or specify path
load_dotenv('.env')

# Verify
print("Project ID:", os.getenv('FIREBASE_PROJECT_ID'))
```

**Prevention:** Load .env before importing services

---

### ❌ Problem: ".env file not found"

**Error Message:**
```
Warning: .env file not found
```

**Cause:** .env file doesn't exist

**Solution:**
```bash
# Create .env from example
cp .env.example .env

# Edit with your values
nano .env

# Or create manually
cat > .env << EOF
DEBUG=True
SECRET_KEY=your-secret-key
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_PATH=./serviceAccountKey.json
EOF
```

**Prevention:** Create .env during initial setup

---

## 🧪 Testing Issues

### ❌ Problem: "Test data not cleaning up"

**Symptoms:**
- Test users accumulate in Firebase Auth
- Test documents remain in Firestore

**Solution:**
```python
# Create cleanup script
# cleanup_tests.py
from firebase_admin import auth
from services.firebase_service import db

def cleanup_test_data():
    # Delete test users from Auth
    users = auth.list_users()
    for user in users.iterate_all():
        if 'test' in user.email.lower():
            auth.delete_user(user.uid)
            print(f"Deleted: {user.email}")
    
    # Delete test collections
    collections = ['test_users', 'test']
    for coll in collections:
        docs = db.collection(coll).stream()
        for doc in docs:
            doc.reference.delete()
    
    print("Cleanup complete")

if __name__ == '__main__':
    cleanup_test_data()
```

**Prevention:** Run cleanup after each test session

---

### ❌ Problem: "Firebase quota exceeded"

**Error Message:**
```
google.api_core.exceptions.ResourceExhausted: 429 Quota exceeded
```

**Cause:** Too many operations in free tier

**Solution:**
```bash
# Check quota usage
# Firebase Console → Usage and billing

# Solutions:
# 1. Reduce test frequency
# 2. Use batch operations
# 3. Upgrade to Blaze plan (pay-as-you-go)

# Optimize queries
# Instead of:
for doc in db.collection('users').stream():
    process(doc)

# Use batch:
docs = db.collection('users').limit(100).stream()
batch = db.batch()
for doc in docs:
    batch.update(doc.reference, {'processed': True})
batch.commit()
```

**Prevention:** Monitor quota usage, use batch operations

---

## 📦 Cloud Functions Issues

### ❌ Problem: "Firebase CLI not installed"

**Error Message:**
```
firebase: command not found
```

**Cause:** Firebase CLI not installed globally

**Solution:**
```bash
# Install Firebase CLI
npm install -g firebase-tools

# Verify installation
firebase --version

# Login
firebase login
```

**Prevention:** Install Firebase CLI during initial setup

---

### ❌ Problem: "Cloud Functions deployment fails"

**Error Message:**
```
Error: Failed to deploy functions
```

**Cause:** Various reasons (syntax error, missing dependencies, etc.)

**Solution:**
```bash
# Check function syntax
cd functions
python -m py_compile main.py

# Check requirements.txt
cat requirements.txt

# Deploy with verbose logging
firebase deploy --only functions --debug

# Check logs
firebase functions:log
```

**Prevention:** Test functions locally before deploying

---

## 🔍 Debugging Tips

### Enable Detailed Logging

```python
import logging

# Enable Firebase Admin SDK logging
logging.basicConfig(level=logging.DEBUG)

# Enable Firestore logging
import google.cloud.logging
client = google.cloud.logging.Client()
client.setup_logging()
```

### Check Firebase Console Logs

```bash
# View Firestore operations
# Firebase Console → Firestore → Usage tab

# View Auth operations
# Firebase Console → Authentication → Usage tab

# View Cloud Functions logs
# Firebase Console → Functions → Logs tab
```

### Use Firebase Emulator Suite (Advanced)

```bash
# Install emulators
firebase init emulators

# Start emulators
firebase emulators:start

# Connect to emulators in code
import os
os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
```

---

## 🆘 Getting Help

If you're still stuck:

1. **Check Firebase Status**: https://status.firebase.google.com/
2. **Firebase Documentation**: https://firebase.google.com/docs
3. **Stack Overflow**: Tag questions with `firebase` and `python`
4. **Firebase Support**: https://firebase.google.com/support
5. **GitHub Issues**: Check firebase-admin-python repository

---

## 📋 Quick Diagnostic Checklist

Run this diagnostic script to check your setup:

```python
# diagnostic.py
import sys
import os
from pathlib import Path

print("=== ShikshaAI Day 01 Diagnostic ===\n")

# Check Python version
print(f"✓ Python version: {sys.version}")

# Check virtual environment
in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
print(f"{'✓' if in_venv else '✗'} Virtual environment: {'Active' if in_venv else 'Not active'}")

# Check dependencies
try:
    import firebase_admin
    print(f"✓ firebase-admin: {firebase_admin.__version__}")
except ImportError:
    print("✗ firebase-admin: Not installed")

try:
    from google.cloud import firestore
    print("✓ google-cloud-firestore: Installed")
except ImportError:
    print("✗ google-cloud-firestore: Not installed")

try:
    import fastapi
    print(f"✓ fastapi: {fastapi.__version__}")
except ImportError:
    print("✗ fastapi: Not installed")

# Check .env file
env_exists = Path('.env').exists()
print(f"{'✓' if env_exists else '✗'} .env file: {'Exists' if env_exists else 'Missing'}")

# Check service account key
key_path = os.getenv('FIREBASE_PRIVATE_KEY_PATH', './serviceAccountKey.json')
key_exists = Path(key_path).exists()
print(f"{'✓' if key_exists else '✗'} Service account key: {'Exists' if key_exists else 'Missing'}")

# Test Firebase connection
if key_exists:
    try:
        from services.firebase_service import db
        db.collection('test').document('diagnostic').set({'test': True})
        db.collection('test').document('diagnostic').delete()
        print("✓ Firebase connection: Working")
    except Exception as e:
        print(f"✗ Firebase connection: Failed - {str(e)}")

print("\n=== Diagnostic Complete ===")
```

Run with:
```bash
python diagnostic.py
```

---

**Remember**: Most issues are due to configuration errors. Double-check your Firebase Console settings and environment variables!
