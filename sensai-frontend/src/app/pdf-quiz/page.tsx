"use client";

import { useState } from "react";
import PDFUpload from "../../components/PDFUpload";
import PDFQuizView from "../../components/PDFQuizView";

export default function PDFQuizPage() {
  const [currentQuiz, setCurrentQuiz] = useState<{
    id: number;
    title: string;
  } | null>(null);

  const handleQuizGenerated = (quizId: number, title: string) => {
    setCurrentQuiz({ id: quizId, title });
  };

  const handleBackToUpload = () => {
    setCurrentQuiz(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto py-8">
        {currentQuiz ? (
          <PDFQuizView
            quizId={currentQuiz.id}
            onBack={handleBackToUpload}
          />
        ) : (
          <PDFUpload onQuizGenerated={handleQuizGenerated} />
        )}
      </div>
    </div>
  );
}
