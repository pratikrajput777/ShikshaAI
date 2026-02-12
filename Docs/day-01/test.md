# Day 01: Testing Guide (Firebase/Firestore)

This document provides comprehensive testing procedures for Day 01 Firebase/Firestore implementation.

---

## Pre-Test Checklist

Before running tests, ensure:

- [ ] Python 3.10+ is installed
- [ ] Virtual environment is activated
- [ ] All dependencies are installed (`pip install -r requirements.txt`)
- [ ] Firebase project is created
- [ ] Service account key is downloaded and placed correctly
- [ ] `.env` file is configured
- [ ] Firebase Admin SDK is initialized

---

## Test 1: Environment Setup Verification

### Test 1.1: Python Environment

**Command:**
```bash
python --version
```

**Expected Output:**
```
Python 3.10.x or higher
```

**Pass Criteria:** Python 3.10+ installed

---

### Test 1.2: Dependencies Installation

**Command:**
```bash
pip list | grep -E "(firebase-admin|google-cloud-firestore|fastapi|uvicorn)"
```

**Expected Output:**
```
fastapi                   0.109.0
firebase-admin            6.3.0
google-cloud-firestore    2.14.0
uvicorn                   0.27.0
```

**Pass Criteria:** All required packages installed

---

### Test 1.3: Environment Variables

**Command:**
```python
# test_env.py
from dotenv import load_dotenv
import os

load_dotenv()

print('DEBUG:', os.getenv('DEBUG'))
print('FIREBASE_PROJECT_ID:', os.getenv('FIREBASE_PROJECT_ID'))
print('FIREBASE_PRIVATE_KEY_PATH:', os.getenv('FIREBASE_PRIVATE_KEY_PATH'))
print('Service account key exists:', os.path.exists(os.getenv('FIREBASE_PRIVATE_KEY_PATH', '')))
```

**Expected Output:**
```
DEBUG: True
FIREBASE_PROJECT_ID: your-project-id
FIREBASE_PRIVATE_KEY_PATH: ./serviceAccountKey.json
Service account key exists: True
```

**Pass Criteria:** All environment variables loaded, service account key file exists

---

## Test 2: Firebase Connection

### Test 2.1: Firebase Admin SDK Initialization

**Command:**
```python
# test_firebase_init.py
from services.firebase_service import firebase_service, db

print("Firebase initialized:", firebase_service is not None)
print("Firestore client:", db is not None)
print("Firestore client type:", type(db).__name__)
```

**Expected Output:**
```
Firebase initialized: True
Firestore client: True
Firestore client type: Client
```

**Pass Criteria:** Firebase Admin SDK initialized successfully

---

### Test 2.2: Firestore Read/Write Test

**Command:**
```python
# test_firestore_connection.py
from services.firebase_service import db
from google.cloud import firestore

# Write test
doc_ref = db.collection('test').document('connection_test')
doc_ref.set({
    'message': 'Hello Firebase!',
    'timestamp': firestore.SERVER_TIMESTAMP
})

# Read test
doc = doc_ref.get()
if doc.exists:
    print("✓ Write successful")
    print("✓ Read successful")
    print("Data:", doc.to_dict())
else:
    print("✗ Failed to read document")

# Cleanup
doc_ref.delete()
print("✓ Delete successful")
```

**Expected Output:**
```
✓ Write successful
✓ Read successful
Data: {'message': 'Hello Firebase!', 'timestamp': Timestamp(...)}
✓ Delete successful
```

**Pass Criteria:** Can write, read, and delete from Firestore

---

## Test 3: Firestore Service

### Test 3.1: Create Document

**Command:**
```python
# test_firestore_service.py
from services.firestore_service import firestore_service

# Create document
data = {
    'name': 'Test User',
    'email': 'test@example.com',
    'role': 'developer'
}

doc_id = firestore_service.create_document('test_users', data)
print(f"✓ Document created with ID: {doc_id}")
```

**Expected Output:**
```
✓ Document created with ID: abc123xyz
```

**Pass Criteria:** Document created successfully, ID returned

---

### Test 3.2: Get Document

**Command:**
```python
# Continue from Test 3.1
doc = firestore_service.get_document('test_users', doc_id)
print("✓ Document retrieved:", doc)
print("Name:", doc.get('name'))
print("Email:", doc.get('email'))
```

**Expected Output:**
```
✓ Document retrieved: {'id': 'abc123xyz', 'name': 'Test User', 'email': 'test@example.com', 'role': 'developer'}
Name: Test User
Email: test@example.com
```

**Pass Criteria:** Document retrieved with all fields

---

### Test 3.3: Update Document

**Command:**
```python
# Continue from Test 3.2
success = firestore_service.update_document('test_users', doc_id, {'role': 'senior developer'})
print("✓ Update successful:", success)

# Verify update
doc = firestore_service.get_document('test_users', doc_id)
print("Updated role:", doc.get('role'))
```

**Expected Output:**
```
✓ Update successful: True
Updated role: senior developer
```

**Pass Criteria:** Document updated successfully

---

### Test 3.4: Query Documents with Filters

**Command:**
```python
# Create multiple documents
for i in range(3):
    firestore_service.create_document('test_users', {
        'name': f'User {i}',
        'role': 'developer' if i % 2 == 0 else 'designer',
        'experience': i + 1
    })

# Query with filter
filters = [('role', '==', 'developer')]
docs = firestore_service.get_documents('test_users', filters=filters)
print(f"✓ Found {len(docs)} developers")
for doc in docs:
    print(f"  - {doc.get('name')}: {doc.get('role')}")
```

**Expected Output:**
```
✓ Found 2 developers
  - User 0: developer
  - User 2: developer
```

**Pass Criteria:** Query returns filtered results

---

### Test 3.5: Subcollection Operations

**Command:**
```python
# Create parent document
user_id = firestore_service.create_document('test_users', {'name': 'John Doe'})

# Create subcollection document
skill_id = firestore_service.create_subcollection_document(
    'test_users', user_id, 'skills',
    {'skillName': 'Python', 'level': 5}
)
print(f"✓ Skill added with ID: {skill_id}")

# Get subcollection documents
skills = firestore_service.get_subcollection_documents('test_users', user_id, 'skills')
print(f"✓ Retrieved {len(skills)} skills")
print("Skills:", skills)
```

**Expected Output:**
```
✓ Skill added with ID: skill123
✓ Retrieved 1 skills
Skills: [{'id': 'skill123', 'skillName': 'Python', 'level': 5}]
```

**Pass Criteria:** Subcollection operations work correctly

---

### Test 3.6: Delete Document

**Command:**
```python
# Cleanup all test documents
from services.firebase_service import db

# Delete all test_users
docs = db.collection('test_users').stream()
count = 0
for doc in docs:
    doc.reference.delete()
    count += 1

print(f"✓ Deleted {count} test documents")
```

**Expected Output:**
```
✓ Deleted 5 test documents
```

**Pass Criteria:** All test documents deleted

---

## Test 4: User Service

### Test 4.1: Create User

**Command:**
```python
# test_user_service.py
from services.user_service import user_service

user_data = {
    'username': 'testuser',
    'displayName': 'Test User',
    'targetRole': 'Software Developer',
    'experienceYears': 3
}

user = user_service.create_user('test@example.com', 'Test123456!', user_data)

if user:
    print("✓ User created successfully")
    print("UID:", user.get('uid'))
    print("Email:", user.get('email'))
    print("Username:", user.get('username'))
else:
    print("✗ Failed to create user")
```

**Expected Output:**
```
✓ User created successfully
UID: abc123xyz
Email: test@example.com
Username: testuser
```

**Pass Criteria:** User created in both Firebase Auth and Firestore

---

### Test 4.2: Get User

**Command:**
```python
# Continue from Test 4.1
uid = user.get('uid')
retrieved_user = user_service.get_user(uid)

print("✓ User retrieved:", retrieved_user.get('username'))
print("Target Role:", retrieved_user.get('targetRole'))
print("Experience Years:", retrieved_user.get('experienceYears'))
```

**Expected Output:**
```
✓ User retrieved: testuser
Target Role: Software Developer
Experience Years: 3
```

**Pass Criteria:** User data retrieved correctly

---

### Test 4.3: Update User

**Command:**
```python
# Continue from Test 4.2
success = user_service.update_user(uid, {
    'experienceYears': 5,
    'targetRole': 'Senior Software Developer'
})

print("✓ Update successful:", success)

# Verify
updated_user = user_service.get_user(uid)
print("Updated experience:", updated_user.get('experienceYears'))
print("Updated role:", updated_user.get('targetRole'))
```

**Expected Output:**
```
✓ Update successful: True
Updated experience: 5
Updated role: Senior Software Developer
```

**Pass Criteria:** User data updated successfully

---

### Test 4.4: Add User Skill

**Command:**
```python
# Continue from Test 4.3
skill_data = {
    'skillId': 'python_123',
    'skillName': 'Python Programming',
    'selfAssessment': 4
}

skill_id = user_service.add_user_skill(uid, skill_data)
print(f"✓ Skill added with ID: {skill_id}")

# Get user skills
skills = user_service.get_user_skills(uid)
print(f"✓ User has {len(skills)} skills")
print("Skills:", [s.get('skillName') for s in skills])
```

**Expected Output:**
```
✓ Skill added with ID: skill_abc123
✓ User has 1 skills
Skills: ['Python Programming']
```

**Pass Criteria:** Skill added to user's subcollection

---

## Test 5: Skills Service

### Test 5.1: Create Skill

**Command:**
```python
# test_skills_service.py
from services.skills_service import skills_service

skill_data = {
    'preferredLabel': 'Python Programming',
    'alternativeLabels': ['Python', 'Python3', 'Python Development'],
    'description': 'Programming language for general-purpose programming',
    'skillType': 'technical'
}

skill_id = skills_service.create_skill(skill_data)
print(f"✓ Skill created with ID: {skill_id}")
```

**Expected Output:**
```
✓ Skill created with ID: skill_xyz789
```

**Pass Criteria:** Skill created successfully

---

### Test 5.2: Get Skill

**Command:**
```python
# Continue from Test 5.1
skill = skills_service.get_skill(skill_id)
print("✓ Skill retrieved:", skill.get('preferredLabel'))
print("Type:", skill.get('skillType'))
print("Alternative labels:", skill.get('alternativeLabels'))
```

**Expected Output:**
```
✓ Skill retrieved: Python Programming
Type: technical
Alternative labels: ['Python', 'Python3', 'Python Development']
```

**Pass Criteria:** Skill retrieved with all fields

---

### Test 5.3: Search Skills

**Command:**
```python
# Create more skills for search
skills_service.create_skill({
    'preferredLabel': 'JavaScript',
    'alternativeLabels': ['JS', 'ECMAScript'],
    'description': 'Programming language for web development',
    'skillType': 'technical'
})

skills_service.create_skill({
    'preferredLabel': 'Communication',
    'alternativeLabels': ['Verbal Communication'],
    'description': 'Ability to convey information effectively',
    'skillType': 'soft'
})

# Search
results = skills_service.search_skills('python', limit=10)
print(f"✓ Found {len(results)} skills matching 'python'")
for skill in results:
    print(f"  - {skill.get('preferredLabel')}")
```

**Expected Output:**
```
✓ Found 1 skills matching 'python'
  - Python Programming
```

**Pass Criteria:** Search returns relevant results

---

### Test 5.4: Get Skills by Type

**Command:**
```python
# Get technical skills
technical_skills = skills_service.get_skills_by_type('technical')
print(f"✓ Found {len(technical_skills)} technical skills")

# Get soft skills
soft_skills = skills_service.get_skills_by_type('soft')
print(f"✓ Found {len(soft_skills)} soft skills")
```

**Expected Output:**
```
✓ Found 2 technical skills
✓ Found 1 soft skills
```

**Pass Criteria:** Skills filtered by type correctly

---

### Test 5.5: Create Occupation with Skills

**Command:**
```python
from services.firebase_service import db

# Get skill references
python_skill = skills_service.search_skills('python')[0]
js_skill = skills_service.search_skills('javascript')[0]

occupation_data = {
    'onetCode': '15-1252.00',
    'preferredLabel': 'Software Developer',
    'alternativeLabels': ['Software Engineer', 'Developer'],
    'description': 'Develop computer applications software',
    'requiredSkills': [
        {
            'skillRef': db.collection('skills').document(python_skill['id']),
            'skillName': 'Python Programming',
            'importance': 0.9,
            'requiredProficiencyTheta': 1.5
        },
        {
            'skillRef': db.collection('skills').document(js_skill['id']),
            'skillName': 'JavaScript',
            'importance': 0.8,
            'requiredProficiencyTheta': 1.2
        }
    ]
}

occ_id = skills_service.create_occupation(occupation_data)
print(f"✓ Occupation created with ID: {occ_id}")
```

**Expected Output:**
```
✓ Occupation created with ID: occ_abc123
```

**Pass Criteria:** Occupation created with skill references

---

### Test 5.6: Get Occupation Skills

**Command:**
```python
# Continue from Test 5.5
skills = skills_service.get_occupation_skills(occ_id)
print(f"✓ Occupation requires {len(skills)} skills")
for skill in skills:
    print(f"  - {skill.get('preferredLabel')}: importance={skill.get('importance')}, theta={skill.get('requiredProficiencyTheta')}")
```

**Expected Output:**
```
✓ Occupation requires 2 skills
  - Python Programming: importance=0.9, theta=1.5
  - JavaScript: importance=0.8, theta=1.2
```

**Pass Criteria:** Occupation skills retrieved with metadata

---

## Test 6: API Endpoints

### Test 6.1: Start API Server

**Command:**
```bash
# For FastAPI
uvicorn main:app --reload --port 8000

# For Django
python manage.py runserver
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Pass Criteria:** Server starts without errors

---

### Test 6.2: Root Endpoint

**Command:**
```bash
curl http://localhost:8000/
```

**Expected Output:**
```json
{
  "message": "ShikshaAI API - Firebase Edition",
  "version": "1.0.0",
  "endpoints": ["/api/users", "/api/skills"]
}
```

**Pass Criteria:** Root endpoint returns API info

---

### Test 6.3: Create User via API

**Command:**
```bash
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "apitest@example.com",
    "password": "Test123456!",
    "username": "apitest",
    "displayName": "API Test User",
    "targetRole": "Data Scientist",
    "experienceYears": 2
  }'
```

**Expected Output:**
```json
{
  "uid": "abc123xyz",
  "email": "apitest@example.com",
  "username": "apitest",
  "displayName": "API Test User",
  "targetRole": "Data Scientist",
  "experienceYears": 2,
  "isActive": true
}
```

**Pass Criteria:** User created via API, returns user object

---

### Test 6.4: Get User via API

**Command:**
```bash
# Replace {uid} with actual UID from previous test
curl http://localhost:8000/api/users/{uid}
```

**Expected Output:**
```json
{
  "uid": "abc123xyz",
  "email": "apitest@example.com",
  "username": "apitest",
  "displayName": "API Test User",
  "targetRole": "Data Scientist"
}
```

**Pass Criteria:** User data retrieved via API

---

### Test 6.5: Search Skills via API

**Command:**
```bash
curl http://localhost:8000/api/skills/search/python
```

**Expected Output:**
```json
[
  {
    "id": "skill_123",
    "preferredLabel": "Python Programming",
    "alternativeLabels": ["Python", "Python3"],
    "skillType": "technical"
  }
]
```

**Pass Criteria:** Skills search returns results

---

### Test 6.6: Get Occupation via API

**Command:**
```bash
curl http://localhost:8000/api/skills/occupations/{occupation_id}
```

**Expected Output:**
```json
{
  "id": "occ_123",
  "onetCode": "15-1252.00",
  "preferredLabel": "Software Developer",
  "alternativeLabels": ["Software Engineer"],
  "requiredSkills": [...]
}
```

**Pass Criteria:** Occupation data retrieved

---

## Test 7: Firebase Console Verification

### Test 7.1: Verify Firestore Collections

**Steps:**
1. Go to Firebase Console: https://console.firebase.google.com/
2. Select your project
3. Navigate to Firestore Database
4. Verify collections exist:
   - users
   - skills
   - occupations
   - userPoints

**Pass Criteria:** All collections visible in console

---

### Test 7.2: Verify User Document Structure

**Steps:**
1. In Firestore Database, click on `users` collection
2. Click on any user document
3. Verify fields:
   - uid, email, username, displayName
   - targetRole, experienceYears
   - isActive, createdAt, updatedAt
4. Check subcollections:
   - skills
   - proficiencies

**Pass Criteria:** Document structure matches schema

---

### Test 7.3: Verify Firebase Authentication

**Steps:**
1. In Firebase Console, go to Authentication
2. Click on "Users" tab
3. Verify test users are listed
4. Check email and UID match Firestore documents

**Pass Criteria:** Auth users match Firestore users

---

## Test 8: Security Rules (Manual)

### Test 8.1: Unauthenticated Access

**Command:**
```python
# test_security.py
from google.cloud import firestore

# Create unauthenticated client (this will fail with proper rules)
db_unauth = firestore.Client()

try:
    doc = db_unauth.collection('users').document('test').get()
    print("✗ SECURITY ISSUE: Unauthenticated access allowed!")
except Exception as e:
    print("✓ Security working: Unauthenticated access denied")
    print(f"Error: {type(e).__name__}")
```

**Expected Output:**
```
✓ Security working: Unauthenticated access denied
Error: PermissionDenied
```

**Pass Criteria:** Unauthenticated access is denied

---

## Test 9: Cleanup

### Test 9.1: Delete Test Data

**Command:**
```python
# cleanup_test_data.py
from services.firebase_service import db, firebase_service
from firebase_admin import auth

# Delete test users from Auth
users = auth.list_users()
for user in users.iterate_all():
    if 'test' in user.email.lower():
        auth.delete_user(user.uid)
        print(f"✓ Deleted auth user: {user.email}")

# Delete test collections
collections = ['test_users', 'test']
for collection in collections:
    docs = db.collection(collection).stream()
    for doc in docs:
        doc.reference.delete()
    print(f"✓ Deleted collection: {collection}")

print("✓ Cleanup complete")
```

**Expected Output:**
```
✓ Deleted auth user: test@example.com
✓ Deleted auth user: apitest@example.com
✓ Deleted collection: test_users
✓ Deleted collection: test
✓ Cleanup complete
```

**Pass Criteria:** All test data removed

---

## Summary Checklist

### Environment
- [x] Python 3.10+ installed
- [x] Dependencies installed
- [x] Environment variables configured
- [x] Service account key in place

### Firebase
- [x] Firebase project created
- [x] Firestore enabled
- [x] Firebase Auth enabled
- [x] Admin SDK initialized

### Services
- [x] Firebase service working
- [x] Firestore service CRUD operations
- [x] User service (create, get, update)
- [x] Skills service (create, search, filter)

### API
- [x] Server starts successfully
- [x] User endpoints working
- [x] Skills endpoints working
- [x] Proper error handling

### Data
- [x] Users created in Auth and Firestore
- [x] Skills and occupations created
- [x] Subcollections working
- [x] References working correctly

### Security
- [x] Security rules deployed
- [x] Unauthenticated access denied
- [x] Owner-only access enforced

---

## Troubleshooting

If tests fail, refer to `troubleshoot.md` for common issues and solutions.

---

**All tests passed? Congratulations! Day 01 is complete. Proceed to Day 02.**
