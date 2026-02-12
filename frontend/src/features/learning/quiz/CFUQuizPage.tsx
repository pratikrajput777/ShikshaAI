import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api from "@/lib/axios";

type Question = {
  id: number;
  text: string;
};

export default function CFUQuizPage() {
  const { id } = useParams();

  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    api
      .get(`/lessons/${id}/quiz/`)
      .then((res) => {
        setQuestions(res.data || []);
      })
      .catch((err) => {
        console.error(err);
        setError("Failed to load quiz");
      })
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div style={{ padding: 16 }}>Loading...</div>;
  if (error) return <div style={{ padding: 16, color: "red" }}>{error}</div>;

  return (
    <div style={{ padding: 20 }}>
      <h2>Quiz</h2>

      {questions.length === 0 && <p>No questions available</p>}

      <ol>
        {questions.map((q) => (
          <li key={q.id} style={{ marginBottom: 10 }}>
            {q.text}
          </li>
        ))}
      </ol>
    </div>
  );
}
