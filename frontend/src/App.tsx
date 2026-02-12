import { BrowserRouter, Routes, Route } from "react-router-dom";

import AssessmentPage from "@/features/learning/assessment/AssessmentPage";
import StudyPlanPage from "@/features/learning/study-plan/StudyPlanPage";
import LessonViewer from "@/features/learning/lesson/LessonViewer";
import CFUQuizPage from "@/features/learning/quiz/CFUQuizPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>

        <Route path="/assessments" element={<AssessmentPage />} />
        <Route path="/study-plan" element={<StudyPlanPage />} />
        <Route path="/lessons/:id" element={<LessonViewer />} />
        <Route path="/lessons/:id/quiz" element={<CFUQuizPage />} />

      </Routes>
    </BrowserRouter>
  );
}

export default App;
