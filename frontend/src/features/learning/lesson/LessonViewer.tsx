import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import api from "@/lib/axios";

type Lesson = {
  id: number;
  title: string;
  content?: string;
};

export default function LessonViewer() {
  const { id } = useParams();
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    api
      .get(`/lessons/${id}/`)
      .then((res) => {
        setLesson(res.data);
      })
      .catch((err) => {
        console.error(err);
        setError("Failed to load lesson");
      })
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div style={{ padding: 16 }}>Loading...</div>;
  if (error) return <div style={{ padding: 16, color: "red" }}>{error}</div>;
  if (!lesson) return <div style={{ padding: 16 }}>Lesson not found</div>;

  return (
    <div style={{ padding: 20 }}>
      <h2>{lesson.title}</h2>

      <div style={{ marginTop: 12 }}>
        {lesson.content || "No content"}
      </div>

      <div style={{ marginTop: 20 }}>
        <Link to={`/lessons/${lesson.id}/quiz`}>
          Go to Quiz
        </Link>
      </div>
    </div>
  );
}
