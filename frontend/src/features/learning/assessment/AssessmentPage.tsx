import { useEffect, useState } from "react";
import api from "@/lib/axios";

type Assessment = {
  id: number;
  title: string;
  description?: string;
};

export default function AssessmentPage() {
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get("/assessments/")
      .then((res) => {
        setAssessments(res.data || []);
      })
      .catch((err) => {
        console.error(err);
        setError("Failed to load assessments");
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ padding: 16 }}>Loading...</div>;

  if (error)
    return (
      <div style={{ padding: 16, color: "red" }}>
        {error}
      </div>
    );

  return (
    <div style={{ padding: 20 }}>
      <h2>Assessments</h2>

      {assessments.length === 0 && (
        <p>No assessments found</p>
      )}

      <ul>
        {assessments.map((a) => (
          <li key={a.id}>
            <strong>{a.title}</strong>
            {a.description && (
              <div>{a.description}</div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
