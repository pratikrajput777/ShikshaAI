# Firebase & Firestore Conversion Guide

## 📋 Overview

This document outlines the complete conversion strategy from PostgreSQL to Firebase/Firestore for the ShikshaAI platform. This conversion transforms the application from a traditional Django + PostgreSQL architecture to a modern Firebase-first architecture while maintaining all core functionality.

---

## 🎯 Conversion Strategy

### Why Firebase/Firestore?

1. **Serverless Architecture**: No database server management required
2. **Real-time Capabilities**: Built-in real-time data synchronization
3. **Scalability**: Automatic scaling without configuration
4. **Cost-Effective**: Pay only for what you use
5. **Integrated Ecosystem**: Authentication, Storage, Functions, Hosting all in one
6. **Global CDN**: Data replicated across multiple regions
7. **Offline Support**: Built-in offline data persistence

### Architecture Changes

| Component | PostgreSQL Version | Firebase Version |
|-----------|-------------------|------------------|
| **Database** | PostgreSQL 15+ | Cloud Firestore |
| **Authentication** | Django Auth | Firebase Authentication |
| **File Storage** | Local/S3 | Firebase Storage |
| **Real-time** | Django Channels + WebSockets | Firestore Real-time Listeners |
| **Background Jobs** | Celery + Redis | Cloud Functions |
| **Caching** | Redis | Firestore + Local Cache |
| **Search** | PostgreSQL Full-Text | Algolia/Typesense (or Firestore queries) |

---

## 🗄️ Data Model Conversion

### PostgreSQL → Firestore Mapping

#### 1. **Relational Tables → Collections**

**PostgreSQL:**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(150),
    email VARCHAR(254),
    target_role VARCHAR(200)
);
```

**Firestore:**
```javascript
// Collection: users
// Document ID: auto-generated or custom
{
  username: "john_doe",
  email: "john@example.com",
  targetRole: "Software Developer",
  createdAt: Timestamp,
  updatedAt: Timestamp
}
```

#### 2. **Foreign Keys → References**

**PostgreSQL:**
```sql
CREATE TABLE user_skills (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    skill_id INTEGER REFERENCES skills(id)
);
```

**Firestore (Option 1 - Subcollection):**
```javascript
// Collection: users/{userId}/skills/{skillId}
{
  skillRef: reference to /skills/{skillId},
  selfAssessment: 3,
  createdAt: Timestamp
}
```

**Firestore (Option 2 - Embedded):**
```javascript
// Collection: users/{userId}
{
  username: "john_doe",
  skills: [
    {
      skillId: "skill_123",
      skillRef: reference,
      selfAssessment: 3
    }
  ]
}
```

#### 3. **ArrayField → Firestore Arrays**

**PostgreSQL:**
```python
from django.contrib.postgres.fields import ArrayField

class Skill(models.Model):
    alternative_labels = ArrayField(
        models.CharField(max_length=100),
        default=list
    )
```

**Firestore:**
```javascript
// Collection: skills/{skillId}
{
  preferredLabel: "Python Programming",
  alternativeLabels: ["Python", "Python3", "Python Development"],
  skillType: "technical"
}
```

#### 4. **JSONField → Firestore Maps**

**PostgreSQL:**
```python
class StudyPlan(models.Model):
    metadata = models.JSONField(default=dict)
```

**Firestore:**
```javascript
// Collection: studyPlans/{planId}
{
  userId: "user_123",
  metadata: {
    generatedBy: "gemini-pro",
    version: "1.0",
    estimatedHours: 40
  }
}
```

---

## 📊 Complete Collection Structure

### Core Collections

#### 1. **users**
```javascript
{
  uid: "firebase_auth_uid", // From Firebase Auth
  username: "john_doe",
  email: "john@example.com",
  displayName: "John Doe",
  photoURL: "https://...",
  targetRole: "Software Developer",
  experienceYears: 5,
  learningStyle: "visual",
  skillLevel: "intermediate",
  resumeUploaded: false,
  linkedinUrl: "https://linkedin.com/in/johndoe",
  githubUrl: "https://github.com/johndoe",
  lastActive: Timestamp,
  totalTimeSpent: 3600, // seconds
  isActive: true,
  createdAt: Timestamp,
  updatedAt: Timestamp
}

// Subcollections:
// - users/{userId}/skills
// - users/{userId}/proficiencies
// - users/{userId}/studyPlans
// - users/{userId}/sessions
```

#### 2. **skills**
```javascript
{
  escoUri: "http://data.europa.eu/esco/skill/...",
  preferredLabel: "Python Programming",
  alternativeLabels: ["Python", "Python3"],
  description: "Programming language for...",
  skillType: "technical", // technical, soft, knowledge
  prerequisites: [skillRef1, skillRef2], // References
  createdAt: Timestamp,
  updatedAt: Timestamp
}

// Subcollections:
// - skills/{skillId}/embeddings
```

#### 3. **occupations**
```javascript
{
  escoUri: "http://data.europa.eu/esco/occupation/...",
  onetCode: "15-1252.00",
  preferredLabel: "Software Developer",
  alternativeLabels: ["Software Engineer", "Developer"],
  description: "Develop, create, and modify...",
  parentRef: reference, // Self-reference for hierarchy
  requiredSkills: [
    {
      skillRef: reference,
      importance: 0.9,
      requiredProficiencyTheta: 1.5
    }
  ],
  createdAt: Timestamp,
  updatedAt: Timestamp
}
```

#### 4. **diagnosticSessions**
```javascript
{
  userRef: reference,
  skillRef: reference,
  status: "in_progress", // in_progress, completed, abandoned
  currentTheta: 0.5,
  standardError: 0.25,
  questionCount: 8,
  startedAt: Timestamp,
  completedAt: Timestamp,
  convergenceReached: false,
  finalTheta: null,
  finalSE: null
}

// Subcollections:
// - diagnosticSessions/{sessionId}/answers
```

#### 5. **questionBank**
```javascript
{
  skillRef: reference,
  questionText: "What is the output of...",
  options: ["A", "B", "C", "D"],
  correctAnswer: "B",
  explanation: "The correct answer is B because...",
  
  // IRT Parameters
  difficulty: 0.5, // b parameter (-4 to +4)
  discrimination: 1.2, // a parameter (0.5 to 2.5)
  guessing: 0.25, // c parameter (0 to 0.5)
  
  questionType: "multiple_choice",
  difficultyLevel: "medium",
  bloomLevel: "application",
  tags: ["loops", "python", "syntax"],
  
  timesAsked: 150,
  timesCorrect: 90,
  
  createdAt: Timestamp,
  updatedAt: Timestamp
}
```

#### 6. **studyPlans**
```javascript
{
  userRef: reference,
  occupationRef: reference,
  title: "Software Developer Learning Path",
  description: "Personalized plan based on skill gaps",
  status: "active", // draft, active, completed, archived
  
  skillGaps: [
    {
      skillRef: reference,
      currentTheta: 0.5,
      requiredTheta: 2.0,
      priority: 1
    }
  ],
  
  estimatedHours: 120,
  completionPercentage: 35,
  
  generatedBy: "gemini-pro",
  generationMetadata: {
    model: "gemini-1.5-pro",
    promptVersion: "v2.1",
    cost: 0.002
  },
  
  createdAt: Timestamp,
  updatedAt: Timestamp,
  startedAt: Timestamp,
  completedAt: null
}

// Subcollections:
// - studyPlans/{planId}/modules
```

#### 7. **learningModules**
```javascript
{
  studyPlanRef: reference,
  title: "Python Fundamentals",
  description: "Master the basics of Python",
  orderIndex: 1,
  status: "locked", // locked, available, in_progress, completed
  
  estimatedHours: 20,
  completionPercentage: 0,
  
  prerequisites: [moduleRef1, moduleRef2],
  
  createdAt: Timestamp,
  updatedAt: Timestamp
}

// Subcollections:
// - learningModules/{moduleId}/lessons
```

#### 8. **lessons**
```javascript
{
  moduleRef: reference,
  title: "Variables and Data Types",
  content: "# Variables in Python\n\n...", // Markdown
  orderIndex: 1,
  status: "available",
  
  learningObjectives: [
    "Understand variable declaration",
    "Learn about data types"
  ],
  
  estimatedMinutes: 30,
  
  generatedBy: "gemini-flash",
  generationCost: 0.0001,
  
  completedAt: null,
  createdAt: Timestamp,
  updatedAt: Timestamp
}

// Subcollections:
// - lessons/{lessonId}/cfuQuizzes
// - lessons/{lessonId}/resources
```

#### 9. **cfuQuizzes**
```javascript
{
  lessonRef: reference,
  questions: [
    {
      questionText: "What is a variable?",
      options: ["A", "B", "C", "D"],
      correctAnswer: "A",
      explanation: "Variables store data...",
      difficulty: "easy"
    }
  ],
  passingScore: 70,
  createdAt: Timestamp
}

// Subcollections:
// - cfuQuizzes/{quizId}/attempts
```

#### 10. **cfuAttempts**
```javascript
{
  quizRef: reference,
  userRef: reference,
  lessonRef: reference,
  
  answers: [
    {
      questionIndex: 0,
      selectedAnswer: "A",
      isCorrect: true
    }
  ],
  
  score: 80,
  passed: true,
  timeSpent: 180, // seconds
  
  attemptedAt: Timestamp
}

// Subcollections:
// - cfuAttempts/{attemptId}/remediations (if failed)
```

#### 11. **conversationSessions** (Mock Interviews)
```javascript
{
  userRef: reference,
  occupationRef: reference,
  jobDescription: "We are looking for...",
  
  status: "in_progress", // scheduled, in_progress, completed, abandoned
  
  questionCount: 0,
  currentQuestionIndex: 0,
  
  startedAt: Timestamp,
  completedAt: null,
  
  metadata: {
    interviewType: "technical",
    difficulty: "medium"
  }
}

// Subcollections:
// - conversationSessions/{sessionId}/turns
// - conversationSessions/{sessionId}/evaluations
```

#### 12. **interviewTurns**
```javascript
{
  sessionRef: reference,
  turnNumber: 1,
  speaker: "interviewer", // interviewer, candidate
  
  // For interviewer
  questionText: "Tell me about yourself",
  questionType: "behavioral",
  audioUrl: "gs://bucket/audio/question_1.mp3",
  
  // For candidate
  transcriptText: "I am a software developer...",
  responseTime: 45, // seconds
  
  timestamp: Timestamp
}
```

#### 13. **interviewEvaluations**
```javascript
{
  sessionRef: reference,
  userRef: reference,
  
  // Three-Judge Scores
  technicalScore: 85,
  technicalFeedback: "Strong technical knowledge...",
  technicalCriteria: {
    accuracy: 90,
    depth: 85,
    problemSolving: 80,
    communication: 85
  },
  
  behavioralScore: 78,
  behavioralFeedback: "Good use of STAR method...",
  behavioralCriteria: {
    starStructure: 80,
    leadership: 75,
    communication: 80,
    selfAwareness: 75
  },
  
  structuralScore: 82,
  structuralFeedback: "Well-organized responses...",
  structuralCriteria: {
    organization: 85,
    conciseness: 80,
    completeness: 80,
    professionalism: 85
  },
  
  overallScore: 82, // Weighted average
  
  strengths: [
    "Clear communication",
    "Strong technical foundation"
  ],
  weaknesses: [
    "Could provide more specific examples",
    "Time management in responses"
  ],
  recommendations: [
    "Practice STAR method more",
    "Prepare more concrete examples"
  ],
  
  evaluatedAt: Timestamp,
  evaluatedBy: "gemini-pro"
}
```

#### 14. **achievements**
```javascript
{
  title: "First Steps",
  description: "Complete your first lesson",
  icon: "🎯",
  category: "learning",
  
  unlockCriteria: {
    type: "lesson_count",
    threshold: 1
  },
  
  bonusPoints: 50,
  rarity: "common", // common, rare, epic, legendary
  
  createdAt: Timestamp
}
```

#### 15. **userAchievements**
```javascript
{
  userRef: reference,
  achievementRef: reference,
  unlockedAt: Timestamp,
  progress: 100
}
```

#### 16. **userPoints**
```javascript
{
  userRef: reference,
  totalPoints: 5420,
  level: 7,
  currentStreak: 5,
  longestStreak: 12,
  lastLoginDate: Timestamp,
  
  pointsHistory: [
    {
      action: "lesson_complete",
      points: 50,
      timestamp: Timestamp
    }
  ]
}
```

#### 17. **leaderboardEntries**
```javascript
{
  userRef: reference,
  username: "john_doe",
  displayName: "John Doe",
  photoURL: "https://...",
  
  period: "weekly", // weekly, monthly, all_time
  rank: 5,
  points: 1250,
  
  periodStart: Timestamp,
  periodEnd: Timestamp,
  updatedAt: Timestamp
}
```

#### 18. **subscriptions**
```javascript
{
  userRef: reference,
  
  tier: "pro", // free, pro, premium, enterprise
  status: "active", // active, canceled, past_due, trialing
  
  stripeCustomerId: "cus_...",
  stripeSubscriptionId: "sub_...",
  stripePriceId: "price_...",
  
  currentPeriodStart: Timestamp,
  currentPeriodEnd: Timestamp,
  cancelAtPeriodEnd: false,
  
  trialStart: null,
  trialEnd: null,
  
  createdAt: Timestamp,
  updatedAt: Timestamp
}
```

#### 19. **featureUsage**
```javascript
{
  userRef: reference,
  subscriptionRef: reference,
  
  period: "2026-01", // YYYY-MM
  
  assessmentsUsed: 5,
  studyPlansCreated: 2,
  interviewsCompleted: 3,
  
  limits: {
    assessments: 10,
    studyPlans: 5,
    interviews: 10
  },
  
  updatedAt: Timestamp
}
```

#### 20. **referralCodes**
```javascript
{
  userRef: reference,
  code: "JOHN2026",
  
  timesUsed: 5,
  maxUses: null, // null = unlimited
  
  bonusPoints: 100,
  discountPercent: 10,
  
  expiresAt: null,
  isActive: true,
  
  createdAt: Timestamp
}
```

---

## 🔄 Key Conversion Patterns

### 1. **Queries**

**PostgreSQL:**
```python
users = User.objects.filter(
    target_role="Software Developer",
    experience_years__gte=3
).order_by('-created_at')[:10]
```

**Firestore:**
```python
from google.cloud import firestore

db = firestore.Client()
users_ref = db.collection('users')
query = users_ref.where('targetRole', '==', 'Software Developer') \
                 .where('experienceYears', '>=', 3) \
                 .order_by('createdAt', direction=firestore.Query.DESCENDING) \
                 .limit(10)

users = query.stream()
```

### 2. **Joins (Denormalization)**

**PostgreSQL:**
```python
study_plans = StudyPlan.objects.select_related('user', 'occupation').all()
```

**Firestore (Denormalized):**
```python
# Store user and occupation data directly in study plan
study_plan = {
    'userRef': user_ref,
    'userName': 'John Doe',  # Denormalized
    'userEmail': 'john@example.com',  # Denormalized
    'occupationRef': occupation_ref,
    'occupationTitle': 'Software Developer',  # Denormalized
    ...
}
```

### 3. **Transactions**

**PostgreSQL:**
```python
from django.db import transaction

with transaction.atomic():
    user.points += 50
    user.save()
    PointsHistory.objects.create(user=user, points=50)
```

**Firestore:**
```python
from google.cloud import firestore

@firestore.transactional
def award_points(transaction, user_ref, points):
    user_doc = user_ref.get(transaction=transaction)
    user_data = user_doc.to_dict()
    
    new_points = user_data['totalPoints'] + points
    transaction.update(user_ref, {'totalPoints': new_points})
    
    history_ref = user_ref.collection('pointsHistory').document()
    transaction.set(history_ref, {
        'points': points,
        'action': 'lesson_complete',
        'timestamp': firestore.SERVER_TIMESTAMP
    })

transaction = db.transaction()
award_points(transaction, user_ref, 50)
```

### 4. **Real-time Updates**

**Django Channels (WebSocket):**
```python
class ProgressConsumer(AsyncWebsocketConsumer):
    async def receive(self, text_data):
        # Handle message
        await self.send(text_data=json.dumps({'progress': 50}))
```

**Firestore Real-time Listener:**
```python
def on_snapshot(doc_snapshot, changes, read_time):
    for doc in doc_snapshot:
        print(f'Progress: {doc.to_dict()["completionPercentage"]}')

# Client-side listener
study_plan_ref.on_snapshot(on_snapshot)
```

### 5. **Background Jobs**

**Celery:**
```python
from celery import shared_task

@shared_task
def generate_study_plan(user_id):
    # Generate plan
    return plan_id
```

**Cloud Functions:**
```python
from firebase_functions import firestore_fn, https_fn
from firebase_admin import firestore

@firestore_fn.on_document_created(document="skillGaps/{gapId}")
def generate_study_plan(event: firestore_fn.Event[firestore_fn.DocumentSnapshot]):
    gap_data = event.data.to_dict()
    user_id = gap_data['userId']
    
    # Generate study plan using Gemini
    # ...
    
    # Save to Firestore
    db = firestore.client()
    db.collection('studyPlans').add({
        'userId': user_id,
        'status': 'active',
        'createdAt': firestore.SERVER_TIMESTAMP
    })
```

---

## 🛠️ Technology Stack Changes

### Before (PostgreSQL)
```
Django 4.2.7
PostgreSQL 15+
psycopg2-binary 2.9.9
Redis 5.0.1
Celery 5.3.4
Django Channels 4.0.0
```

### After (Firebase)
```
Django 4.2.7 (or FastAPI for lighter alternative)
firebase-admin 6.3.0
google-cloud-firestore 2.14.0
google-cloud-storage 2.14.0
google-cloud-functions-framework 3.5.0
```

---

## 📝 Migration Checklist

### Phase 1: Setup
- [ ] Create Firebase project
- [ ] Enable Firestore Database
- [ ] Enable Firebase Authentication
- [ ] Enable Firebase Storage
- [ ] Download service account credentials
- [ ] Install Firebase Admin SDK
- [ ] Configure environment variables

### Phase 2: Data Model
- [ ] Design Firestore collection structure
- [ ] Plan denormalization strategy
- [ ] Create security rules
- [ ] Set up indexes
- [ ] Create data validation functions

### Phase 3: Code Migration
- [ ] Replace Django ORM with Firestore SDK
- [ ] Convert models to Firestore documents
- [ ] Update queries and filters
- [ ] Implement transactions
- [ ] Add real-time listeners

### Phase 4: Features
- [ ] Migrate authentication to Firebase Auth
- [ ] Replace Celery with Cloud Functions
- [ ] Update file uploads to Firebase Storage
- [ ] Implement caching strategy
- [ ] Add offline support

### Phase 5: Testing
- [ ] Unit tests for Firestore operations
- [ ] Integration tests
- [ ] Performance testing
- [ ] Security rules testing
- [ ] Load testing

### Phase 6: Deployment
- [ ] Deploy Cloud Functions
- [ ] Configure Firebase Hosting
- [ ] Set up CI/CD pipeline
- [ ] Monitor with Firebase Analytics
- [ ] Set up error tracking

---

## 🔒 Security Rules Example

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // Users can only read/write their own data
    match /users/{userId} {
      allow read: if request.auth != null && request.auth.uid == userId;
      allow write: if request.auth != null && request.auth.uid == userId;
      
      // Subcollections
      match /skills/{skillId} {
        allow read, write: if request.auth != null && request.auth.uid == userId;
      }
      
      match /studyPlans/{planId} {
        allow read, write: if request.auth != null && request.auth.uid == userId;
      }
    }
    
    // Skills are read-only for all authenticated users
    match /skills/{skillId} {
      allow read: if request.auth != null;
      allow write: if false; // Only admins via Cloud Functions
    }
    
    // Occupations are read-only
    match /occupations/{occupationId} {
      allow read: if request.auth != null;
      allow write: if false;
    }
    
    // Question bank is read-only
    match /questionBank/{questionId} {
      allow read: if request.auth != null;
      allow write: if false;
    }
    
    // Leaderboard is read-only
    match /leaderboardEntries/{entryId} {
      allow read: if request.auth != null;
      allow write: if false; // Updated by Cloud Functions
    }
  }
}
```

---

## 💰 Cost Optimization

### Firestore Best Practices

1. **Minimize Reads**
   - Use local caching
   - Implement pagination
   - Use real-time listeners efficiently

2. **Denormalize Data**
   - Store frequently accessed data together
   - Avoid excessive document reads for joins

3. **Batch Operations**
   - Use batch writes (up to 500 operations)
   - Reduce number of individual writes

4. **Index Management**
   - Only create necessary composite indexes
   - Monitor index usage

5. **Document Size**
   - Keep documents under 1MB
   - Split large data into subcollections

---

## 🚀 Performance Optimization

1. **Caching Strategy**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=1000)
   def get_skill(skill_id):
       return db.collection('skills').document(skill_id).get()
   ```

2. **Pagination**
   ```python
   # First page
   first_query = db.collection('users').limit(10)
   docs = first_query.stream()
   last_doc = list(docs)[-1]
   
   # Next page
   next_query = db.collection('users').start_after(last_doc).limit(10)
   ```

3. **Batch Reads**
   ```python
   # Get multiple documents in one request
   doc_refs = [db.collection('skills').document(id) for id in skill_ids]
   docs = db.get_all(doc_refs)
   ```

---

## 📚 Resources

- [Firestore Documentation](https://firebase.google.com/docs/firestore)
- [Firebase Admin SDK for Python](https://firebase.google.com/docs/admin/setup)
- [Firestore Data Modeling](https://firebase.google.com/docs/firestore/manage-data/structure-data)
- [Security Rules Guide](https://firebase.google.com/docs/firestore/security/get-started)
- [Cloud Functions for Firebase](https://firebase.google.com/docs/functions)

---

**This guide will be referenced throughout all day-by-day tutorials for the Firebase conversion.**
