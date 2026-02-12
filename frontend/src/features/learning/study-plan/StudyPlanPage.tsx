import { useEffect, useState } from "react";
import api from "@/lib/axios";

type StudyPlan = {
  id: number;
  title: string;
  description?: string;
};

export default function StudyPlanPage() {
  const [plans, setPlans] = useState<StudyPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get("/study-plans/")
      .then((res) => {
        setPlans(res.data || []);
      })
      .catch((err) => {
        console.error(err);
        setError("Failed to load study plans");
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ padding: 16 }}>Loading...</div>;
  if (error) return <div style={{ padding: 16, color: "red" }}>{error}</div>;

  return (
    <div style={{ padding: 20 }}>
      <h2>Study Plans</h2>

      {plans.length === 0 && <p>No study plans found</p>}

      <ul>
        {plans.map((p) => (
          <li key={p.id}>
            <strong>{p.title}</strong>
            {p.description && <div>{p.description}</div>}
          </li>
        ))}
      </ul>
    </div>
  );
}
