# Day 01: Foundation & Core Infrastructure 🏗️

## 📚 What You Will Achieve Today

By the end of Day 1, you will have:

1. ✅ Complete Django/FastAPI project structure with proper configuration
2. ✅ Firebase project setup with Firestore database
3. ✅ Cloud Functions infrastructure for background jobs
4. ✅ Firebase Authentication integration
5. ✅ Core Firestore collections for Users, Skills taxonomy, and Occupations
6. ✅ Basic API endpoints for user management
7. ✅ Firebase Admin SDK configuration
8. ✅ Environment configuration and security setup

## 🎯 Learning Objectives

### Backend Fundamentals
- **Django/FastAPI Architecture**: Understand service-based architecture
- **Firestore Data Modeling**: Master document structures and subcollections
- **Firebase Admin SDK**: Learn server-side Firebase integration
- **Cloud Functions**: Serverless async task processing
- **Environment Management**: Secure configuration with `.env` files

### System Design Concepts
- **NoSQL Database Design**: Denormalization, subcollections, and references
- **RESTful API Design**: URL patterns, viewsets/routers, and serializers
- **Authentication**: Firebase Authentication integration
- **Serverless Architecture**: Cloud Functions deployment

### Security Best Practices
- **Environment Variables**: Never commit secrets to version control
- **Firebase Security Rules**: Firestore access control
- **Service Account Keys**: Secure credential management
- **Firebase Authentication**: Built-in security features

## 🛠️ Technology Stack (Day 1)

| Technology | Version | Purpose |
|------------|---------|---------|
| Django/FastAPI | 4.2.7/0.109+ | Web framework |
| Firebase Admin SDK | 6.3.0 | Firebase server integration |
| Cloud Firestore | Latest | NoSQL document database |
| Firebase Auth | Latest | User authentication |
| Cloud Functions | Latest | Serverless background jobs |
| Firebase Storage | Latest | File storage & CDN |

## 📊 Firestore Collections (Day 1)

### Collections to Create
1. **users** - User profiles with Firebase Auth integration
2. **users/{userId}/skills** - User's self-reported skills (subcollection)
3. **users/{userId}/proficiencies** - IRT-based skill proficiency tracking (subcollection)
4. **occupations** - Job roles from ESCO/O*NET with denormalized skills
5. **skills** - Skills taxonomy with semantic embeddings
6. **skills/{skillId}/embeddings** - Vector embeddings (subcollection)
7. **skillSynonyms** - Alternative terms for skills

## 📋 Prerequisites

- Python 3.10+ installed
- Google Cloud account (Firebase free tier)
- Node.js 18+ (for Cloud Functions)
- Basic understanding of Python and NoSQL
- Familiarity with command line
- Text editor/IDE (VS Code, PyCharm, etc.)

## ⏱️ Estimated Time

- **Setup & Installation**: 2 hours
- **Firestore Collections Setup**: 3 hours
- **API Endpoints**: 2 hours
- **Testing & Troubleshooting**: 1 hour
- **Total**: ~8 hours (1 working day for 2 developers)

## 🎓 Key Concepts to Master

### 1. Service-Based Architecture
Learn how to organize code with Firebase:
```
project/
├── services/       # Business logic services
│   ├── firestore_service.py
│   ├── auth_service.py
│   └── gemini_service.py
├── functions/      # Cloud Functions
│   ├── index.js
│   └── triggers/
└── api/           # API endpoints
```

### 2. Firestore Data Modeling
Understand document structures and relationships:
- Document fields: strings, numbers, arrays, maps, references
- Subcollections: Nested data organization
- References: Linking documents across collections
- Denormalization: Optimizing for read performance

### 3. Firebase-Specific Features
- **Arrays**: Store lists directly in documents
- **Maps**: Nested object structures
- **References**: Link to other documents
- **Timestamps**: Server-side timestamp generation
- **Transactions**: Atomic operations

### 4. Cloud Functions
Understand serverless background processing:
- Firestore triggers (onCreate, onUpdate, onDelete)
- HTTP functions for API endpoints
- Scheduled functions for periodic tasks
- Event-driven architecture

## 📖 Resources for Day 1

### Official Documentation
- [Firebase Documentation](https://firebase.google.com/docs)
- [Firestore Data Model](https://firebase.google.com/docs/firestore/data-model)
- [Firebase Admin SDK for Python](https://firebase.google.com/docs/admin/setup)
- [Cloud Functions Documentation](https://firebase.google.com/docs/functions)

### Tutorials
- Firebase for Python Developers
- Firestore Data Modeling Best Practices
- Cloud Functions Getting Started

## 🚀 Success Criteria

By end of day, you should be able to:

- [x] Run `python manage.py runserver` or `uvicorn main:app` successfully
- [x] Access Firebase Console and view Firestore data
- [x] Create users via Firebase Auth and API endpoint
- [x] View Firestore collections and documents
- [x] Deploy a simple Cloud Function
- [x] Query Firestore from Python backend

## 🎯 Next Steps (Day 2 Preview)

Tomorrow you will implement:
- IRT-based diagnostic assessment engine
- Question bank with difficulty parameters
- Adaptive question selection algorithm
- Skill gap analysis system

---

**Remember**: Take breaks, ask questions, and don't rush. Understanding the fundamentals is crucial for the rest of the project!
