import { useEffect, useState } from "react";
import api from "@/lib/axios";

type Skill = {
  id: number;
  name: string;
  level: number;
};

export default function SkillRadar() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get("/skills/")
      .then((res) => {
        setSkills(res.data || []);
      })
      .catch((err) => {
        console.error(err);
        setError("Failed to load skills");
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ padding: 16 }}>Loading...</div>;
  if (error) return <div style={{ padding: 16, color: "red" }}>{error}</div>;

  return (
    <div style={{ padding: 20 }}>
      <h2>Skill Radar</h2>

      {skills.length === 0 && <p>No skills found</p>}

      <ul>
        {skills.map((s) => (
          <li key={s.id}>
            {s.name} – level {s.level}
          </li>
        ))}
      </ul>
    </div>
  );
}
