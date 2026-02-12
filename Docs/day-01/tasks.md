# Day 01: Detailed Tasks Breakdown (Firebase/Firestore)

## Developer Assignment

- **Developer A (DA)**: Focus on Django/FastAPI project setup, Firebase Auth, and API endpoints
- **Developer B (DB)**: Focus on Firestore collections, Cloud Functions setup, and skills taxonomy

---

## Phase 1: Project Initialization (1.5 hours)

### Task 1.1: Environment Setup
**Assigned to**: Both developers
**Duration**: 30 minutes

#### Subtasks:
- [ ] 1.1.1 Install Python 3.10+ and create virtual environment
  ```bash
  python -m venv venv
  source venv/bin/activate  # On Windows: venv\\Scripts\\activate
  ```
- [ ] 1.1.2 Create Firebase project in Firebase Console
  - Go to https://console.firebase.google.com/
  - Click "Add project"
  - Name: "shikshaai" or your preferred name
  - Enable Google Analytics (optional)
  
- [ ] 1.1.3 Enable Firestore Database
  - In Firebase Console, go to Build → Firestore Database
  - Click "Create database"
  - Start in **production mode** (we'll add security rules later)
  - Choose location closest to your users
  
- [ ] 1.1.4 Enable Firebase Authentication
  - Go to Build → Authentication
  - Click "Get started"
  - Enable Email/Password sign-in method
  
- [ ] 1.1.5 Generate service account key
  - Go to Project Settings → Service Accounts
  - Click "Generate new private key"
  - Save as `serviceAccountKey.json` in project root
  - **IMPORTANT**: Add to `.gitignore`

- [ ] 1.1.6 Create project directory structure
  ```bash
  mkdir shikshaAI && cd shikshaAI
  mkdir services api functions
  ```

**Completion Criteria**: Firebase project created, service account key downloaded

---

### Task 1.2: Django/FastAPI Project Creation
**Assigned to**: DA
**Duration**: 30 minutes

#### Subtasks:
- [ ] 1.2.1 Install Django/FastAPI and core dependencies
  
  **Option A: Django**
  ```bash
  pip install Django==4.2.7 djangorestframework==3.14.0 firebase-admin==6.3.0
  ```
  
  **Option B: FastAPI (Recommended for new projects)**
  ```bash
  pip install fastapi==0.109.0 uvicorn==0.27.0 firebase-admin==6.3.0
  ```

- [ ] 1.2.2 Create project structure

  **For Django:**
  ```bash
  django-admin startproject jobreadiness .
  python manage.py startapp api
  python manage.py startapp services
  ```
  
  **For FastAPI:**
  ```bash
  touch main.py
  mkdir -p api/routes services models
  ```

- [ ] 1.2.3 Install additional Firebase dependencies
  ```bash
  pip install google-cloud-firestore==2.14.0 google-cloud-storage==2.14.0
  pip install python-dotenv==1.0.0
  ```

- [ ] 1.2.4 Create `requirements.txt`
  ```bash
  pip freeze > requirements.txt
  ```

**Completion Criteria**: Project structure created, dependencies installed

---

### Task 1.3: Firebase Configuration
**Assigned to**: DB
**Duration**: 30 minutes

#### Subtasks:
- [ ] 1.3.1 Create `.env` file in project root
  ```env
  DEBUG=True
  SECRET_KEY=your-secret-key-here-change-in-production
  
  # Firebase Configuration
  FIREBASE_PROJECT_ID=your-project-id
  FIREBASE_PRIVATE_KEY_PATH=./serviceAccountKey.json
  
  # Google Cloud (for Gemini AI)
  GOOGLE_API_KEY=your-gemini-api-key
  
  # Stripe (for later)
  STRIPE_SECRET_KEY=your-stripe-key
  STRIPE_WEBHOOK_SECRET=your-webhook-secret
  ```

- [ ] 1.3.2 Create Firebase initialization service `services/firebase_service.py`
  ```python
  import firebase_admin
  from firebase_admin import credentials, firestore, auth
  import os
  from dotenv import load_dotenv
  
  load_dotenv()
  
  class FirebaseService:
      _instance = None
      _db = None
      
      def __new__(cls):
          if cls._instance is None:
              cls._instance = super(FirebaseService, cls).__new__(cls)
              cls._instance._initialize()
          return cls._instance
      
      def _initialize(self):
          """Initialize Firebase Admin SDK"""
          if not firebase_admin._apps:
              cred_path = os.getenv('FIREBASE_PRIVATE_KEY_PATH')
              cred = credentials.Certificate(cred_path)
              firebase_admin.initialize_app(cred)
          
          self._db = firestore.client()
      
      @property
      def db(self):
          """Get Firestore client"""
          return self._db
      
      def get_user(self, uid):
          """Get user by Firebase Auth UID"""
          try:
              return auth.get_user(uid)
          except Exception as e:
              print(f"Error getting user: {e}")
              return None
      
      def create_user(self, email, password, display_name=None):
          """Create new Firebase Auth user"""
          try:
              user = auth.create_user(
                  email=email,
                  password=password,
                  display_name=display_name
              )
              return user
          except Exception as e:
              print(f"Error creating user: {e}")
              return None
  
  # Singleton instance
  firebase_service = FirebaseService()
  db = firebase_service.db
  ```

- [ ] 1.3.3 Create Firestore service `services/firestore_service.py`
  ```python
  from google.cloud import firestore
  from services.firebase_service import db
  from typing import Dict, List, Optional
  
  class FirestoreService:
      """Service for Firestore CRUD operations"""
      
      def __init__(self):
          self.db = db
      
      # CREATE
      def create_document(self, collection: str, data: Dict, doc_id: Optional[str] = None):
          """Create a new document"""
          try:
              if doc_id:
                  doc_ref = self.db.collection(collection).document(doc_id)
                  doc_ref.set(data)
                  return doc_id
              else:
                  doc_ref = self.db.collection(collection).add(data)
                  return doc_ref[1].id
          except Exception as e:
              print(f"Error creating document: {e}")
              return None
      
      # READ
      def get_document(self, collection: str, doc_id: str):
          """Get a single document"""
          try:
              doc = self.db.collection(collection).document(doc_id).get()
              if doc.exists:
                  return {**doc.to_dict(), 'id': doc.id}
              return None
          except Exception as e:
              print(f"Error getting document: {e}")
              return None
      
      def get_documents(self, collection: str, filters: Optional[List] = None, 
                       order_by: Optional[str] = None, limit: Optional[int] = None):
          """Get multiple documents with optional filters"""
          try:
              query = self.db.collection(collection)
              
              # Apply filters
              if filters:
                  for field, operator, value in filters:
                      query = query.where(field, operator, value)
              
              # Apply ordering
              if order_by:
                  query = query.order_by(order_by)
              
              # Apply limit
              if limit:
                  query = query.limit(limit)
              
              docs = query.stream()
              return [{**doc.to_dict(), 'id': doc.id} for doc in docs]
          except Exception as e:
              print(f"Error getting documents: {e}")
              return []
      
      # UPDATE
      def update_document(self, collection: str, doc_id: str, data: Dict):
          """Update a document"""
          try:
              self.db.collection(collection).document(doc_id).update(data)
              return True
          except Exception as e:
              print(f"Error updating document: {e}")
              return False
      
      # DELETE
      def delete_document(self, collection: str, doc_id: str):
          """Delete a document"""
          try:
              self.db.collection(collection).document(doc_id).delete()
              return True
          except Exception as e:
              print(f"Error deleting document: {e}")
              return False
      
      # SUBCOLLECTIONS
      def create_subcollection_document(self, collection: str, doc_id: str, 
                                       subcollection: str, data: Dict, 
                                       subdoc_id: Optional[str] = None):
          """Create document in subcollection"""
          try:
              if subdoc_id:
                  doc_ref = self.db.collection(collection).document(doc_id) \\
                                   .collection(subcollection).document(subdoc_id)
                  doc_ref.set(data)
                  return subdoc_id
              else:
                  doc_ref = self.db.collection(collection).document(doc_id) \\
                                   .collection(subcollection).add(data)
                  return doc_ref[1].id
          except Exception as e:
              print(f"Error creating subcollection document: {e}")
              return None
      
      def get_subcollection_documents(self, collection: str, doc_id: str, 
                                     subcollection: str):
          """Get all documents from subcollection"""
          try:
              docs = self.db.collection(collection).document(doc_id) \\
                            .collection(subcollection).stream()
              return [{**doc.to_dict(), 'id': doc.id} for doc in docs]
          except Exception as e:
              print(f"Error getting subcollection documents: {e}")
              return []
  
  # Service instance
  firestore_service = FirestoreService()
  ```

- [ ] 1.3.4 Test Firebase connection
  ```python
  # test_firebase.py
  from services.firebase_service import db
  
  # Test Firestore connection
  doc_ref = db.collection('test').document('test_doc')
  doc_ref.set({'message': 'Hello Firebase!'})
  
  doc = doc_ref.get()
  if doc.exists:
      print(f"Success! Data: {doc.to_dict()}")
  else:
      print("Failed to connect to Firestore")
  
  # Clean up
  doc_ref.delete()
  ```

**Completion Criteria**: Firebase connected successfully, can read/write to Firestore

---

## Phase 2: User Management System (2 hours)

### Task 2.1: User Collection Structure
**Assigned to**: DA
**Duration**: 1 hour

#### Subtasks:
- [ ] 2.1.1 Create user service `services/user_service.py`
  ```python
  from services.firestore_service import firestore_service
  from services.firebase_service import firebase_service
  from google.cloud import firestore
  from typing import Dict, Optional
  
  class UserService:
      """Service for user management"""
      
      def __init__(self):
          self.fs = firestore_service
          self.fb = firebase_service
      
      def create_user(self, email: str, password: str, user_data: Dict):
          """Create user in Firebase Auth and Firestore"""
          try:
              # Create Firebase Auth user
              auth_user = self.fb.create_user(
                  email=email,
                  password=password,
                  display_name=user_data.get('displayName')
              )
              
              if not auth_user:
                  return None
              
              # Create Firestore user document
              user_doc_data = {
                  'uid': auth_user.uid,
                  'email': email,
                  'username': user_data.get('username'),
                  'displayName': user_data.get('displayName'),
                  'targetRole': user_data.get('targetRole'),
                  'experienceYears': user_data.get('experienceYears', 0),
                  'learningStyle': user_data.get('learningStyle', 'visual'),
                  'skillLevel': user_data.get('skillLevel', 'beginner'),
                  'isActive': True,
                  'createdAt': firestore.SERVER_TIMESTAMP,
                  'updatedAt': firestore.SERVER_TIMESTAMP
              }
              
              self.fs.create_document('users', user_doc_data, auth_user.uid)
              
              return {**user_doc_data, 'id': auth_user.uid}
          except Exception as e:
              print(f"Error creating user: {e}")
              return None
      
      def get_user(self, uid: str):
          """Get user by UID"""
          return self.fs.get_document('users', uid)
      
      def update_user(self, uid: str, data: Dict):
          """Update user data"""
          data['updatedAt'] = firestore.SERVER_TIMESTAMP
          return self.fs.update_document('users', uid, data)
      
      def add_user_skill(self, uid: str, skill_data: Dict):
          """Add skill to user's skills subcollection"""
          skill_data['createdAt'] = firestore.SERVER_TIMESTAMP
          return self.fs.create_subcollection_document(
              'users', uid, 'skills', skill_data
          )
      
      def get_user_skills(self, uid: str):
          """Get all user skills"""
          return self.fs.get_subcollection_documents('users', uid, 'skills')
      
      def update_user_proficiency(self, uid: str, skill_id: str, proficiency_data: Dict):
          """Update user proficiency for a skill"""
          proficiency_data['updatedAt'] = firestore.SERVER_TIMESTAMP
          return self.fs.create_subcollection_document(
              'users', uid, 'proficiencies', proficiency_data, skill_id
          )
  
  user_service = UserService()
  ```

- [ ] 2.1.2 Define user document structure (documentation)
  ```javascript
  // Collection: users/{userId}
  {
    uid: "firebase_auth_uid",
    username: "john_doe",
    email: "john@example.com",
    displayName: "John Doe",
    photoURL: "https://...",
    targetRole: "Software Developer",
    experienceYears: 5,
    learningStyle: "visual",  // visual, auditory, kinesthetic
    skillLevel: "intermediate",  // beginner, intermediate, advanced
    resumeUploaded: false,
    linkedinUrl: "https://linkedin.com/in/johndoe",
    githubUrl: "https://github.com/johndoe",
    lastActive: Timestamp,
    totalTimeSpent: 3600,  // seconds
    isActive: true,
    createdAt: Timestamp,
    updatedAt: Timestamp
  }
  
  // Subcollection: users/{userId}/skills/{skillId}
  {
    skillRef: reference to /skills/{skillId},
    skillName: "Python Programming",  // Denormalized
    selfAssessment: 3,  // 1-5 scale
    createdAt: Timestamp
  }
  
  // Subcollection: users/{userId}/proficiencies/{skillId}
  {
    skillRef: reference to /skills/{skillId},
    theta: 0.5,  // IRT ability estimate
    standardError: 0.25,
    calibrationCount: 15,
    lastAssessed: Timestamp,
    updatedAt: Timestamp
  }
  ```

**Completion Criteria**: User service created, document structure defined

---

### Task 2.2: User API Endpoints
**Assigned to**: DA
**Duration**: 1 hour

#### Subtasks:
- [ ] 2.2.1 Create API endpoints

  **For Django REST Framework:**
  ```python
  # api/views.py
  from rest_framework.decorators import api_view
  from rest_framework.response import Response
  from rest_framework import status
  from services.user_service import user_service
  
  @api_view(['POST'])
  def create_user(request):
      """Create new user"""
      try:
          email = request.data.get('email')
          password = request.data.get('password')
          user_data = request.data.get('userData', {})
          
          user = user_service.create_user(email, password, user_data)
          
          if user:
              return Response(user, status=status.HTTP_201_CREATED)
          return Response(
              {'error': 'Failed to create user'}, 
              status=status.HTTP_400_BAD_REQUEST
          )
      except Exception as e:
          return Response(
              {'error': str(e)}, 
              status=status.HTTP_500_INTERNAL_SERVER_ERROR
          )
  
  @api_view(['GET'])
  def get_user(request, uid):
      """Get user by UID"""
      user = user_service.get_user(uid)
      if user:
          return Response(user)
      return Response(
          {'error': 'User not found'}, 
          status=status.HTTP_404_NOT_FOUND
      )
  
  @api_view(['PUT'])
  def update_user(request, uid):
      """Update user"""
      success = user_service.update_user(uid, request.data)
      if success:
          return Response({'message': 'User updated successfully'})
      return Response(
          {'error': 'Failed to update user'}, 
          status=status.HTTP_400_BAD_REQUEST
      )
  
  @api_view(['POST'])
  def add_user_skill(request, uid):
      """Add skill to user"""
      skill_id = user_service.add_user_skill(uid, request.data)
      if skill_id:
          return Response({'skillId': skill_id}, status=status.HTTP_201_CREATED)
      return Response(
          {'error': 'Failed to add skill'}, 
          status=status.HTTP_400_BAD_REQUEST
      )
  
  @api_view(['GET'])
  def get_user_skills(request, uid):
      """Get user skills"""
      skills = user_service.get_user_skills(uid)
      return Response(skills)
  ```

  **For FastAPI:**
  ```python
  # api/routes/users.py
  from fastapi import APIRouter, HTTPException
  from pydantic import BaseModel
  from services.user_service import user_service
  from typing import Optional
  
  router = APIRouter(prefix="/users", tags=["users"])
  
  class UserCreate(BaseModel):
      email: str
      password: str
      username: str
      displayName: Optional[str] = None
      targetRole: Optional[str] = None
      experienceYears: Optional[int] = 0
  
  class UserUpdate(BaseModel):
      displayName: Optional[str] = None
      targetRole: Optional[str] = None
      experienceYears: Optional[int] = None
  
  class SkillAdd(BaseModel):
      skillId: str
      skillName: str
      selfAssessment: int
  
  @router.post("/")
  async def create_user(user_data: UserCreate):
      """Create new user"""
      user = user_service.create_user(
          user_data.email, 
          user_data.password, 
          user_data.dict()
      )
      if user:
          return user
      raise HTTPException(status_code=400, detail="Failed to create user")
  
  @router.get("/{uid}")
  async def get_user(uid: str):
      """Get user by UID"""
      user = user_service.get_user(uid)
      if user:
          return user
      raise HTTPException(status_code=404, detail="User not found")
  
  @router.put("/{uid}")
  async def update_user(uid: str, user_data: UserUpdate):
      """Update user"""
      success = user_service.update_user(uid, user_data.dict(exclude_unset=True))
      if success:
          return {"message": "User updated successfully"}
      raise HTTPException(status_code=400, detail="Failed to update user")
  
  @router.post("/{uid}/skills")
  async def add_user_skill(uid: str, skill_data: SkillAdd):
      """Add skill to user"""
      skill_id = user_service.add_user_skill(uid, skill_data.dict())
      if skill_id:
          return {"skillId": skill_id}
      raise HTTPException(status_code=400, detail="Failed to add skill")
  
  @router.get("/{uid}/skills")
  async def get_user_skills(uid: str):
      """Get user skills"""
      return user_service.get_user_skills(uid)
  ```

- [ ] 2.2.2 Register routes

  **Django:**
  ```python
  # api/urls.py
  from django.urls import path
  from . import views
  
  urlpatterns = [
      path('users/', views.create_user, name='create_user'),
      path('users/<str:uid>/', views.get_user, name='get_user'),
      path('users/<str:uid>/update/', views.update_user, name='update_user'),
      path('users/<str:uid>/skills/', views.add_user_skill, name='add_user_skill'),
      path('users/<str:uid>/skills/list/', views.get_user_skills, name='get_user_skills'),
  ]
  
  # jobreadiness/urls.py
  from django.contrib import admin
  from django.urls import path, include
  
  urlpatterns = [
      path('admin/', admin.site.urls),
      path('api/', include('api.urls')),
  ]
  ```

  **FastAPI:**
  ```python
  # main.py
  from fastapi import FastAPI
  from api.routes import users
  
  app = FastAPI(title="ShikshaAI API")
  
  app.include_router(users.router)
  
  @app.get("/")
  async def root():
      return {"message": "ShikshaAI API - Firebase Edition"}
  ```

**Completion Criteria**: User CRUD API endpoints working

---

## Phase 3: Skills Taxonomy System (2 hours)

### Task 3.1: Skills & Occupation Collections
**Assigned to**: DB
**Duration**: 1 hour

#### Subtasks:
- [ ] 3.1.1 Create skills service `services/skills_service.py`
  ```python
  from services.firestore_service import firestore_service
  from google.cloud import firestore
  from typing import Dict, List, Optional
  
  class SkillsService:
      """Service for skills and occupations management"""
      
      def __init__(self):
          self.fs = firestore_service
      
      # SKILLS
      def create_skill(self, skill_data: Dict):
          """Create new skill"""
          skill_data['createdAt'] = firestore.SERVER_TIMESTAMP
          skill_data['updatedAt'] = firestore.SERVER_TIMESTAMP
          return self.fs.create_document('skills', skill_data)
      
      def get_skill(self, skill_id: str):
          """Get skill by ID"""
          return self.fs.get_document('skills', skill_id)
      
      def search_skills(self, query: str, limit: int = 10):
          """Search skills by name"""
          # Note: Firestore doesn't support full-text search natively
          # For production, use Algolia or Typesense
          skills = self.fs.get_documents('skills', limit=limit)
          query_lower = query.lower()
          return [
              skill for skill in skills 
              if query_lower in skill.get('preferredLabel', '').lower()
              or any(query_lower in label.lower() 
                    for label in skill.get('alternativeLabels', []))
          ]
      
      def get_skills_by_type(self, skill_type: str):
          """Get skills by type"""
          filters = [('skillType', '==', skill_type)]
          return self.fs.get_documents('skills', filters=filters)
      
      # OCCUPATIONS
      def create_occupation(self, occupation_data: Dict):
          """Create new occupation"""
          occupation_data['createdAt'] = firestore.SERVER_TIMESTAMP
          occupation_data['updatedAt'] = firestore.SERVER_TIMESTAMP
          return self.fs.create_document('occupations', occupation_data)
      
      def get_occupation(self, occupation_id: str):
          """Get occupation by ID"""
          return self.fs.get_document('occupations', occupation_id)
      
      def get_occupation_skills(self, occupation_id: str):
          """Get required skills for an occupation"""
          occupation = self.get_occupation(occupation_id)
          if occupation and 'requiredSkills' in occupation:
              # Fetch full skill details
              skills = []
              for skill_req in occupation['requiredSkills']:
                  skill_ref = skill_req.get('skillRef')
                  if skill_ref:
                      skill = skill_ref.get().to_dict()
                      if skill:
                          skills.append({
                              **skill,
                              'importance': skill_req.get('importance'),
                              'requiredProficiencyTheta': skill_req.get('requiredProficiencyTheta')
                          })
              return skills
          return []
  
  skills_service = SkillsService()
  ```

- [ ] 3.1.2 Define collection structures (documentation)
  ```javascript
  // Collection: skills/{skillId}
  {
    escoUri: "http://data.europa.eu/esco/skill/...",
    preferredLabel: "Python Programming",
    alternativeLabels: ["Python", "Python3", "Python Development"],
    description: "Programming language for general-purpose programming",
    skillType: "technical",  // technical, soft, knowledge
    prerequisites: [skillRef1, skillRef2],  // References to other skills
    createdAt: Timestamp,
    updatedAt: Timestamp
  }
  
  // Subcollection: skills/{skillId}/embeddings/{embeddingId}
  {
    vector: [0.123, 0.456, ...],  // 768-dimensional embedding
    modelName: "text-embedding-004",
    createdAt: Timestamp
  }
  
  // Collection: occupations/{occupationId}
  {
    escoUri: "http://data.europa.eu/esco/occupation/...",
    onetCode: "15-1252.00",
    preferredLabel: "Software Developer",
    alternativeLabels: ["Software Engineer", "Developer", "Programmer"],
    description: "Develop, create, and modify general computer applications software or specialized utility programs",
    parentRef: reference,  // Self-reference for hierarchy
    requiredSkills: [
      {
        skillRef: reference to /skills/{skillId},
        skillName: "Python Programming",  // Denormalized
        importance: 0.9,  // 0-1 scale
        requiredProficiencyTheta: 1.5  // IRT theta score
      }
    ],
    createdAt: Timestamp,
    updatedAt: Timestamp
  }
  ```

- [ ] 3.1.3 Create sample data script `scripts/seed_skills.py`
  ```python
  from services.skills_service import skills_service
  from services.firestore_service import firestore_service
  
  def seed_skills():
      """Create sample skills"""
      skills = [
          {
              'preferredLabel': 'Python Programming',
              'alternativeLabels': ['Python', 'Python3', 'Python Development'],
              'description': 'Programming language for general-purpose programming',
              'skillType': 'technical'
          },
          {
              'preferredLabel': 'JavaScript',
              'alternativeLabels': ['JS', 'ECMAScript'],
              'description': 'Programming language for web development',
              'skillType': 'technical'
          },
          {
              'preferredLabel': 'Communication',
              'alternativeLabels': ['Verbal Communication', 'Written Communication'],
              'description': 'Ability to convey information effectively',
              'skillType': 'soft'
          }
      ]
      
      skill_ids = []
      for skill in skills:
          skill_id = skills_service.create_skill(skill)
          skill_ids.append(skill_id)
          print(f"Created skill: {skill['preferredLabel']} (ID: {skill_id})")
      
      return skill_ids
  
  def seed_occupations(skill_ids):
      """Create sample occupations"""
      db = firestore_service.db
      
      occupations = [
          {
              'onetCode': '15-1252.00',
              'preferredLabel': 'Software Developer',
              'alternativeLabels': ['Software Engineer', 'Developer'],
              'description': 'Develop computer applications software',
              'requiredSkills': [
                  {
                      'skillRef': db.collection('skills').document(skill_ids[0]),
                      'skillName': 'Python Programming',
                      'importance': 0.9,
                      'requiredProficiencyTheta': 1.5
                  },
                  {
                      'skillRef': db.collection('skills').document(skill_ids[1]),
                      'skillName': 'JavaScript',
                      'importance': 0.8,
                      'requiredProficiencyTheta': 1.2
                  }
              ]
          }
      ]
      
      for occupation in occupations:
          occ_id = skills_service.create_occupation(occupation)
          print(f"Created occupation: {occupation['preferredLabel']} (ID: {occ_id})")
  
  if __name__ == '__main__':
      print("Seeding skills...")
      skill_ids = seed_skills()
      
      print("\\nSeeding occupations...")
      seed_occupations(skill_ids)
      
      print("\\nSeeding complete!")
  ```

**Completion Criteria**: Skills and occupations services created, sample data script ready

---

### Task 3.2: Skills API Endpoints
**Assigned to**: DB
**Duration**: 1 hour

#### Subtasks:
- [ ] 3.2.1 Create skills API endpoints

  **FastAPI Example:**
  ```python
  # api/routes/skills.py
  from fastapi import APIRouter, HTTPException
  from pydantic import BaseModel
  from services.skills_service import skills_service
  from typing import List, Optional
  
  router = APIRouter(prefix="/skills", tags=["skills"])
  
  class SkillCreate(BaseModel):
      preferredLabel: str
      alternativeLabels: List[str] = []
      description: str
      skillType: str
  
  class OccupationCreate(BaseModel):
      onetCode: str
      preferredLabel: str
      alternativeLabels: List[str] = []
      description: str
  
  @router.post("/")
  async def create_skill(skill_data: SkillCreate):
      """Create new skill"""
      skill_id = skills_service.create_skill(skill_data.dict())
      if skill_id:
          return {"skillId": skill_id}
      raise HTTPException(status_code=400, detail="Failed to create skill")
  
  @router.get("/{skill_id}")
  async def get_skill(skill_id: str):
      """Get skill by ID"""
      skill = skills_service.get_skill(skill_id)
      if skill:
          return skill
      raise HTTPException(status_code=404, detail="Skill not found")
  
  @router.get("/search/{query}")
  async def search_skills(query: str, limit: int = 10):
      """Search skills"""
      return skills_service.search_skills(query, limit)
  
  @router.get("/type/{skill_type}")
  async def get_skills_by_type(skill_type: str):
      """Get skills by type"""
      return skills_service.get_skills_by_type(skill_type)
  
  # Occupations
  @router.post("/occupations/")
  async def create_occupation(occupation_data: OccupationCreate):
      """Create new occupation"""
      occ_id = skills_service.create_occupation(occupation_data.dict())
      if occ_id:
          return {"occupationId": occ_id}
      raise HTTPException(status_code=400, detail="Failed to create occupation")
  
  @router.get("/occupations/{occupation_id}")
  async def get_occupation(occupation_id: str):
      """Get occupation by ID"""
      occupation = skills_service.get_occupation(occupation_id)
      if occupation:
          return occupation
      raise HTTPException(status_code=404, detail="Occupation not found")
  
  @router.get("/occupations/{occupation_id}/skills")
  async def get_occupation_skills(occupation_id: str):
      """Get required skills for occupation"""
      return skills_service.get_occupation_skills(occupation_id)
  ```

- [ ] 3.2.2 Register routes in main app
  ```python
  # main.py
  from api.routes import users, skills
  
  app.include_router(users.router)
  app.include_router(skills.router)
  ```

**Completion Criteria**: Skills API endpoints working

---

## Phase 4: Cloud Functions Setup (1.5 hours)

### Task 4.1: Cloud Functions Configuration
**Assigned to**: DB
**Duration**: 45 minutes

#### Subtasks:
- [ ] 4.1.1 Install Firebase CLI
  ```bash
  npm install -g firebase-tools
  firebase login
  ```

- [ ] 4.1.2 Initialize Cloud Functions
  ```bash
  firebase init functions
  # Select Python as language
  # Choose existing project
  ```

- [ ] 4.1.3 Create sample Cloud Function `functions/main.py`
  ```python
  from firebase_functions import firestore_fn, https_fn
  from firebase_admin import initialize_app, firestore
  import google.cloud.firestore
  
  initialize_app()
  
  @firestore_fn.on_document_created(document="users/{userId}")
  def on_user_created(event: firestore_fn.Event[firestore_fn.DocumentSnapshot]):
      """Trigger when new user is created"""
      user_data = event.data.to_dict()
      user_id = event.params["userId"]
      
      print(f"New user created: {user_data.get('email')} (ID: {user_id})")
      
      # Initialize user points
      db = firestore.client()
      db.collection('userPoints').document(user_id).set({
          'userId': user_id,
          'totalPoints': 0,
          'level': 1,
          'currentStreak': 0,
          'longestStreak': 0,
          'lastLoginDate': firestore.SERVER_TIMESTAMP
      })
      
      print(f"Initialized points for user: {user_id}")
  
  @https_fn.on_request()
  def hello_world(req: https_fn.Request) -> https_fn.Response:
      """Sample HTTP function"""
      return https_fn.Response("Hello from Cloud Functions!")
  ```

- [ ] 4.1.4 Deploy Cloud Function (optional for Day 1)
  ```bash
  firebase deploy --only functions
  ```

**Completion Criteria**: Cloud Functions initialized, sample function created

---

### Task 4.2: Firestore Security Rules
**Assigned to**: Both
**Duration**: 45 minutes

#### Subtasks:
- [ ] 4.2.1 Create Firestore security rules `firestore.rules`
  ```javascript
  rules_version = '2';
  service cloud.firestore {
    match /databases/{database}/documents {
      
      // Helper functions
      function isAuthenticated() {
        return request.auth != null;
      }
      
      function isOwner(userId) {
        return isAuthenticated() && request.auth.uid == userId;
      }
      
      // Users collection
      match /users/{userId} {
        allow read: if isOwner(userId);
        allow create: if isAuthenticated();
        allow update: if isOwner(userId);
        allow delete: if false;  // Prevent deletion
        
        // User subcollections
        match /skills/{skillId} {
          allow read, write: if isOwner(userId);
        }
        
        match /proficiencies/{proficiencyId} {
          allow read, write: if isOwner(userId);
        }
        
        match /studyPlans/{planId} {
          allow read, write: if isOwner(userId);
        }
      }
      
      // Skills - read-only for all authenticated users
      match /skills/{skillId} {
        allow read: if isAuthenticated();
        allow write: if false;  // Only via Cloud Functions
        
        match /embeddings/{embeddingId} {
          allow read: if isAuthenticated();
          allow write: if false;
        }
      }
      
      // Occupations - read-only
      match /occupations/{occupationId} {
        allow read: if isAuthenticated();
        allow write: if false;
      }
      
      // User points - read by owner, write by Cloud Functions
      match /userPoints/{userId} {
        allow read: if isOwner(userId);
        allow write: if false;  // Only Cloud Functions
      }
      
      // Leaderboard - read-only
      match /leaderboardEntries/{entryId} {
        allow read: if isAuthenticated();
        allow write: if false;
      }
    }
  }
  ```

- [ ] 4.2.2 Deploy security rules
  ```bash
  firebase deploy --only firestore:rules
  ```

- [ ] 4.2.3 Create Firestore indexes `firestore.indexes.json`
  ```json
  {
    "indexes": [
      {
        "collectionGroup": "skills",
        "queryScope": "COLLECTION",
        "fields": [
          { "fieldPath": "skillType", "order": "ASCENDING" },
          { "fieldPath": "preferredLabel", "order": "ASCENDING" }
        ]
      },
      {
        "collectionGroup": "leaderboardEntries",
        "queryScope": "COLLECTION",
        "fields": [
          { "fieldPath": "period", "order": "ASCENDING" },
          { "fieldPath": "points", "order": "DESCENDING" }
        ]
      }
    ],
    "fieldOverrides": []
  }
  ```

**Completion Criteria**: Security rules deployed, indexes configured

---

## Phase 5: Testing & Documentation (1 hour)

### Task 5.1: Manual Testing
**Assigned to**: Both
**Duration**: 30 minutes

#### Subtasks:
- [ ] 5.1.1 Test user creation
  ```bash
  # Using curl or Postman
  curl -X POST http://localhost:8000/api/users/ \\
    -H "Content-Type: application/json" \\
    -d '{
      "email": "test@example.com",
      "password": "test123456",
      "username": "testuser",
      "displayName": "Test User",
      "targetRole": "Software Developer"
    }'
  ```

- [ ] 5.1.2 Test user retrieval
  ```bash
  curl http://localhost:8000/api/users/{uid}
  ```

- [ ] 5.1.3 Test skills endpoints
  ```bash
  # Search skills
  curl http://localhost:8000/api/skills/search/python
  
  # Get skill by ID
  curl http://localhost:8000/api/skills/{skill_id}
  ```

- [ ] 5.1.4 Verify Firestore data in Firebase Console
  - Go to Firebase Console → Firestore Database
  - Check that users, skills, occupations collections exist
  - Verify document structure matches schema

- [ ] 5.1.5 Test Cloud Function (if deployed)
  - Create a new user
  - Check that userPoints document is created automatically
  - View Cloud Functions logs in Firebase Console

**Completion Criteria**: All endpoints return expected responses, data visible in Firestore

---

### Task 5.2: Documentation
**Assigned to**: DA
**Duration**: 30 minutes

#### Subtasks:
- [ ] 5.2.1 Create README.md
  ```markdown
  # ShikshaAI - Firebase Edition
  
  AI-powered career development platform built with Firebase/Firestore.
  
  ## Setup
  
  1. Install dependencies:
     ```bash
     pip install -r requirements.txt
     ```
  
  2. Configure Firebase:
     - Create Firebase project
     - Download service account key
     - Add to `.env` file
  
  3. Run server:
     ```bash
     # Django
     python manage.py runserver
     
     # FastAPI
     uvicorn main:app --reload
     ```
  
  ## API Endpoints
  
  ### Users
  - POST /api/users/ - Create user
  - GET /api/users/{uid} - Get user
  - PUT /api/users/{uid} - Update user
  - POST /api/users/{uid}/skills - Add skill
  - GET /api/users/{uid}/skills - Get user skills
  
  ### Skills
  - POST /api/skills/ - Create skill
  - GET /api/skills/{id} - Get skill
  - GET /api/skills/search/{query} - Search skills
  - GET /api/skills/type/{type} - Get skills by type
  
  ### Occupations
  - POST /api/skills/occupations/ - Create occupation
  - GET /api/skills/occupations/{id} - Get occupation
  - GET /api/skills/occupations/{id}/skills - Get required skills
  ```

- [ ] 5.2.2 Update `.gitignore`
  ```
  # Python
  venv/
  __pycache__/
  *.pyc
  *.pyo
  *.pyd
  .Python
  
  # Environment
  .env
  .env.local
  
  # Firebase
  serviceAccountKey.json
  .firebase/
  
  # IDE
  .vscode/
  .idea/
  *.swp
  *.swo
  
  # Logs
  *.log
  ```

- [ ] 5.2.3 Create `.env.example`
  ```env
  DEBUG=True
  SECRET_KEY=your-secret-key-here
  
  # Firebase
  FIREBASE_PROJECT_ID=your-project-id
  FIREBASE_PRIVATE_KEY_PATH=./serviceAccountKey.json
  
  # Google Cloud
  GOOGLE_API_KEY=your-gemini-api-key
  
  # Stripe
  STRIPE_SECRET_KEY=your-stripe-key
  STRIPE_WEBHOOK_SECRET=your-webhook-secret
  ```

**Completion Criteria**: Documentation complete and clear

---

## Summary Checklist

### Must Complete Today
- [x] Firebase project created and configured
- [x] Firestore database enabled
- [x] Firebase Authentication enabled
- [x] Service account key downloaded
- [x] User collection and API working
- [x] Skills and Occupation collections created
- [x] Cloud Functions initialized
- [x] Security rules deployed
- [x] Sample data created
- [x] Basic API endpoints working

### Good to Have (If Time Permits)
- [ ] Cloud Functions deployed to Firebase
- [ ] Comprehensive test suite
- [ ] API documentation with Swagger/OpenAPI
- [ ] Frontend scaffolding

---

## Developer Sync Points

### Morning Standup (15 min)
- Review tasks for the day
- Assign Phase 1 tasks
- Resolve any blockers

### Mid-Day Check-in (15 min)
- Progress update on Phases 1-3
- Code review of completed tasks
- Adjust timeline if needed

### End-of-Day Review (30 min)
- Demo completed features
- Code review and merge
- Plan for Day 2
- Document any issues

---

## Time Tracking

| Phase | Estimated | Actual | Notes |
|-------|-----------|--------|-------|
| Phase 1: Initialization | 1.5h | | |
| Phase 2: User System | 2h | | |
| Phase 3: Skills System | 2h | | |
| Phase 4: Cloud Functions | 1.5h | | |
| Phase 5: Testing | 1h | | |
| **Total** | **8h** | | |

---

**Notes**:
- Each developer works in parallel on assigned tasks
- Regular commits to version control after each subtask
- Pull requests reviewed by peer before merging
- All tests must pass before marking task complete
- Use Firebase Console to verify data structure
