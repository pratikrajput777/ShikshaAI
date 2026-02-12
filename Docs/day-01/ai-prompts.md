# Day 01: AI Prompts for Code Generation (Firebase/Firestore)

This document contains AI prompts to help generate code for Day 01 tasks using Firebase and Firestore.

---

## Prompt 1: Firebase Service Setup

```
Create a Python Firebase service class that:
1. Initializes Firebase Admin SDK using service account credentials
2. Provides a singleton instance of Firestore client
3. Includes methods for Firebase Authentication (create user, get user)
4. Uses environment variables for configuration
5. Includes proper error handling

Requirements:
- Use firebase-admin SDK
- Load credentials from serviceAccountKey.json
- Support .env file configuration
- Include type hints
- Add docstrings for all methods

File: services/firebase_service.py
```

---

## Prompt 2: Firestore CRUD Service

```
Create a comprehensive Firestore service class in Python that provides:
1. CRUD operations (Create, Read, Update, Delete) for documents
2. Query methods with filters, ordering, and pagination
3. Subcollection operations
4. Batch operations
5. Transaction support

Features needed:
- create_document(collection, data, doc_id=None)
- get_document(collection, doc_id)
- get_documents(collection, filters=None, order_by=None, limit=None)
- update_document(collection, doc_id, data)
- delete_document(collection, doc_id)
- create_subcollection_document(collection, doc_id, subcollection, data)
- get_subcollection_documents(collection, doc_id, subcollection)

Use google-cloud-firestore SDK
Include error handling and logging
Add type hints and docstrings

File: services/firestore_service.py
```

---

## Prompt 3: User Service with Firebase Auth

```
Create a User service class that integrates Firebase Authentication and Firestore:

1. User Management:
   - create_user(email, password, user_data) - Creates auth user + Firestore document
   - get_user(uid) - Retrieves user from Firestore
   - update_user(uid, data) - Updates user data
   - delete_user(uid) - Soft delete (set isActive=False)

2. User Skills Management:
   - add_user_skill(uid, skill_data) - Add to skills subcollection
   - get_user_skills(uid) - Get all user skills
   - remove_user_skill(uid, skill_id) - Remove skill

3. User Proficiency Management:
   - update_user_proficiency(uid, skill_id, proficiency_data)
   - get_user_proficiencies(uid)

Firestore Structure:
- Collection: users/{userId}
- Subcollections: skills, proficiencies

Include:
- Firebase Auth integration
- Firestore references
- SERVER_TIMESTAMP for timestamps
- Error handling
- Type hints

File: services/user_service.py
```

---

## Prompt 4: FastAPI User Endpoints

```
Create FastAPI router for user management with these endpoints:

1. POST /users/ - Create new user
   - Input: email, password, username, displayName, targetRole, experienceYears
   - Creates Firebase Auth user + Firestore document
   - Returns: user object with uid

2. GET /users/{uid} - Get user by UID
   - Returns: user document from Firestore

3. PUT /users/{uid} - Update user
   - Input: Partial user data
   - Updates Firestore document
   - Returns: success message

4. POST /users/{uid}/skills - Add skill to user
   - Input: skillId, skillName, selfAssessment
   - Adds to skills subcollection
   - Returns: skill document ID

5. GET /users/{uid}/skills - Get user skills
   - Returns: array of skill documents

Use Pydantic models for request/response validation
Include proper HTTP status codes
Add error handling with HTTPException
Include docstrings

File: api/routes/users.py
```

---

## Prompt 5: Skills Service

```
Create a Skills service class for managing skills and occupations in Firestore:

1. Skills Management:
   - create_skill(skill_data) - Create new skill
   - get_skill(skill_id) - Get skill by ID
   - search_skills(query, limit) - Search skills by name
   - get_skills_by_type(skill_type) - Filter by type (technical/soft/knowledge)
   - update_skill(skill_id, data) - Update skill

2. Occupations Management:
   - create_occupation(occupation_data) - Create occupation with required skills
   - get_occupation(occupation_id) - Get occupation
   - get_occupation_skills(occupation_id) - Get required skills with details
   - search_occupations(query) - Search occupations

Firestore Structure:
- Collection: skills/{skillId}
  - Fields: preferredLabel, alternativeLabels[], description, skillType
  - Subcollection: embeddings/{embeddingId}

- Collection: occupations/{occupationId}
  - Fields: onetCode, preferredLabel, alternativeLabels[], description
  - Field: requiredSkills[] (array of {skillRef, skillName, importance, requiredProficiencyTheta})

Include:
- Firestore references for relationships
- Denormalized data for performance
- Array queries
- Type hints and docstrings

File: services/skills_service.py
```

---

## Prompt 6: Skills API Endpoints

```
Create FastAPI router for skills and occupations with these endpoints:

Skills:
1. POST /skills/ - Create skill
2. GET /skills/{skill_id} - Get skill
3. GET /skills/search/{query} - Search skills
4. GET /skills/type/{skill_type} - Get skills by type

Occupations:
5. POST /skills/occupations/ - Create occupation
6. GET /skills/occupations/{occupation_id} - Get occupation
7. GET /skills/occupations/{occupation_id}/skills - Get required skills

Use Pydantic models:
- SkillCreate: preferredLabel, alternativeLabels, description, skillType
- OccupationCreate: onetCode, preferredLabel, alternativeLabels, description

Include:
- Proper validation
- Error handling
- HTTP status codes
- Docstrings

File: api/routes/skills.py
```

---

## Prompt 7: Cloud Function - User Created Trigger

```
Create a Cloud Function in Python that triggers when a new user is created in Firestore:

Trigger: firestore_fn.on_document_created(document="users/{userId}")

Actions:
1. Extract user data from event
2. Initialize userPoints document:
   - userId: reference to user
   - totalPoints: 0
   - level: 1
   - currentStreak: 0
   - longestStreak: 0
   - lastLoginDate: SERVER_TIMESTAMP

3. Send welcome email (placeholder for now)
4. Log the event

Use:
- firebase_functions SDK
- firebase_admin for Firestore
- Proper error handling
- Logging

File: functions/main.py
```

---

## Prompt 8: Firestore Security Rules

```
Create comprehensive Firestore security rules for:

1. Users Collection:
   - Users can only read/write their own documents
   - Anyone authenticated can create a user
   - Prevent deletion
   - Subcollections (skills, proficiencies, studyPlans) - owner only

2. Skills Collection:
   - Read: All authenticated users
   - Write: Only via Cloud Functions (deny direct writes)
   - Subcollection embeddings: Same rules

3. Occupations Collection:
   - Read: All authenticated users
   - Write: Only via Cloud Functions

4. UserPoints Collection:
   - Read: Owner only
   - Write: Only via Cloud Functions

5. Leaderboard Collection:
   - Read: All authenticated users
   - Write: Only via Cloud Functions

Include:
- Helper functions (isAuthenticated, isOwner)
- Clear comments
- Proper security

File: firestore.rules
```

---

## Prompt 9: Data Seeding Script

```
Create a Python script to seed initial data into Firestore:

1. Create sample skills:
   - Python Programming (technical)
   - JavaScript (technical)
   - Communication (soft)
   - Problem Solving (soft)
   - Data Structures (knowledge)
   - Algorithms (knowledge)

2. Create sample occupations:
   - Software Developer (with required skills: Python, JavaScript, Data Structures)
   - Data Scientist (with required skills: Python, Statistics, Machine Learning)

For each skill/occupation:
- Include all required fields
- Use proper Firestore references
- Set importance and requiredProficiencyTheta for occupation skills

Include:
- Progress logging
- Error handling
- Ability to run multiple times (check if exists)

File: scripts/seed_skills.py
```

---

## Prompt 10: FastAPI Main Application

```
Create the main FastAPI application file that:

1. Initializes FastAPI app with metadata:
   - Title: "ShikshaAI API - Firebase Edition"
   - Description: "AI-powered career development platform"
   - Version: "1.0.0"

2. Includes routers:
   - users router (prefix: /api/users)
   - skills router (prefix: /api/skills)

3. Adds middleware:
   - CORS (allow all origins for development)
   - Request logging

4. Root endpoint:
   - GET / - Returns API info and available endpoints

5. Health check endpoint:
   - GET /health - Returns status and Firebase connection

Include:
- Proper imports
- Error handling
- Startup event to initialize Firebase
- Documentation

File: main.py
```

---

## Prompt 11: Environment Configuration

```
Create a comprehensive .env.example file with all required environment variables:

1. Application Settings:
   - DEBUG
   - SECRET_KEY
   - ALLOWED_HOSTS

2. Firebase Configuration:
   - FIREBASE_PROJECT_ID
   - FIREBASE_PRIVATE_KEY_PATH
   - FIREBASE_API_KEY
   - FIREBASE_AUTH_DOMAIN
   - FIREBASE_STORAGE_BUCKET

3. Google Cloud:
   - GOOGLE_API_KEY (for Gemini AI)
   - GOOGLE_APPLICATION_CREDENTIALS

4. Stripe:
   - STRIPE_SECRET_KEY
   - STRIPE_PUBLISHABLE_KEY
   - STRIPE_WEBHOOK_SECRET

5. Other:
   - FRONTEND_URL
   - API_BASE_URL

Include:
- Comments explaining each variable
- Example values (not real credentials)
- Security notes

File: .env.example
```

---

## Prompt 12: Firestore Indexes Configuration

```
Create a Firestore indexes configuration file for:

1. Skills Collection:
   - Composite index: skillType (ASC) + preferredLabel (ASC)
   - For filtering by type and sorting by name

2. Leaderboard Collection:
   - Composite index: period (ASC) + points (DESC)
   - For filtering by period and ranking by points

3. Diagnostic Sessions:
   - Composite index: userId (ASC) + status (ASC) + startedAt (DESC)
   - For user's sessions filtered by status

4. Study Plans:
   - Composite index: userId (ASC) + status (ASC) + createdAt (DESC)
   - For user's plans filtered by status

Use proper JSON format for firestore.indexes.json

File: firestore.indexes.json
```

---

## Prompt 13: Testing Script

```
Create a comprehensive testing script that:

1. Tests Firebase connection
2. Tests user creation and retrieval
3. Tests skills CRUD operations
4. Tests occupations with skill references
5. Tests subcollections (user skills)
6. Tests queries with filters

For each test:
- Print test name
- Execute operation
- Verify result
- Print success/failure
- Clean up test data

Include:
- Colored output (green for success, red for failure)
- Summary at the end
- Error handling

File: tests/test_firebase.py
```

---

## Prompt 14: README Documentation

```
Create a comprehensive README.md for the project:

1. Project Overview:
   - What is ShikshaAI
   - Key features
   - Technology stack

2. Prerequisites:
   - Python 3.10+
   - Firebase account
   - Node.js (for Cloud Functions)

3. Setup Instructions:
   - Clone repository
   - Create virtual environment
   - Install dependencies
   - Firebase project setup
   - Environment configuration
   - Run application

4. Project Structure:
   - Explain directory layout
   - Key files and their purposes

5. API Documentation:
   - List all endpoints
   - Request/response examples
   - Authentication

6. Firestore Collections:
   - Document structure
   - Relationships
   - Security rules

7. Development:
   - Running locally
   - Testing
   - Deployment

8. Contributing:
   - Code style
   - Pull request process

File: README.md
```

---

## Prompt 15: Docker Configuration (Optional)

```
Create Docker configuration for the FastAPI application:

1. Dockerfile:
   - Base image: python:3.10-slim
   - Install dependencies
   - Copy application code
   - Expose port 8000
   - Run with uvicorn

2. docker-compose.yml:
   - Service: api
   - Environment variables from .env
   - Volume mounts for development
   - Port mapping

3. .dockerignore:
   - Exclude venv, __pycache__, .env, etc.

Include:
- Multi-stage build for production
- Health check
- Proper user permissions

Files: Dockerfile, docker-compose.yml, .dockerignore
```

---

## Usage Instructions

To use these prompts with AI assistants (ChatGPT, Claude, Gemini):

1. **Copy the prompt** for the component you want to generate
2. **Paste into AI chat** with any specific requirements
3. **Review the generated code** for correctness
4. **Test the code** in your environment
5. **Iterate** if needed with follow-up prompts

### Example Follow-up Prompts:

- "Add error handling for network failures"
- "Include type hints for all function parameters"
- "Add logging statements for debugging"
- "Create unit tests for this service"
- "Add pagination support to this endpoint"
- "Optimize this query for better performance"

---

## Best Practices

When using AI-generated code:

1. **Always review** the code before using
2. **Test thoroughly** in development environment
3. **Check security** implications
4. **Verify** Firestore queries are optimized
5. **Ensure** proper error handling
6. **Add** appropriate logging
7. **Document** any modifications

---

## Additional Resources

- [Firebase Admin SDK Documentation](https://firebase.google.com/docs/admin/setup)
- [Firestore Data Modeling](https://firebase.google.com/docs/firestore/manage-data/structure-data)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Cloud Functions for Firebase](https://firebase.google.com/docs/functions)
