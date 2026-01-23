from django.conf import settings

def sync_study_plan_to_firestore(study_plan):
    db = settings.FIRESTORE_CLIENT

    doc_ref = (
        db.collection("users")
          .document(str(study_plan.user_id))
          .collection("study_plans")
          .document(str(study_plan.id))
    )

    doc_ref.set(
        {
            "target_occupation_id": study_plan.target_occupation_id,
            "status": study_plan.status,
            "progress": float(study_plan.progress_percentage),
        },
        merge=True
    )
