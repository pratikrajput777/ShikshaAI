from firebase_admin import firestore

db = firestore.client()

def seed_phase3_data():

    # Occupation
    occ_ref = db.collection("occupations").document("software_developer")
    occ_ref.set({
        "preferred_label": "Software Developer",
        "alternative_labels": ["Software Engineer", "Programmer"],
        "description": "Develops software applications",
        "parent_id": None
    })

    # Skill
    skill_ref = db.collection("skills").document("python")
    skill_ref.set({
        "preferred_label": "Python",
        "alternative_labels": ["Python Programming"],
        "skill_type": "technical",
        "prerequisite_skill_ids": []
    })

    # Mapping
    db.collection("occupation_skills").document().set({
        "occupation_id": occ_ref.id,
        "skill_id": skill_ref.id,
        "importance": 0.9,
        "required_proficiency_theta": 1.2
    })

    # Embedding
    db.collection("skill_embeddings").document("python").set({
        "skill_id": skill_ref.id,
        "vector": [0.01, 0.22, -0.11],
        "model_name": "dummy-model"
    })

    print("✅ Phase 3 Firestore data inserted successfully")