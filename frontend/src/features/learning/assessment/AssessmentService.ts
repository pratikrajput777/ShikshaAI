import axios from "@/lib/axios";

export const getAssessments = async () => {
  const res = await axios.get("/assessments/");
  return res.data;
};
