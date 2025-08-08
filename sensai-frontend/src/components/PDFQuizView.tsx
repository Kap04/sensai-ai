"use client";

import { useState, useEffect } from "react";
import { 
  CheckCircle, 
  XCircle, 
  HelpCircle, 
  Eye, 
  EyeOff,
  Loader2,
  Trophy,
  BookOpen
} from "lucide-react";

interface QuizQuestion {
  id: number;
  question_text: string;
  question_type: "mcq" | "short_answer";
  options?: string[];
  correct_answer: string;
  hint: string;
  citation: string;
  points: number;
}

interface QuizResult {
  question_id: number;
  is_correct: boolean;
  user_answer: string;
  correct_answer: string;
  citation: string;
  points_earned: number;
  total_points: number;
}

interface QuizSubmissionResponse {
  results: QuizResult[];
  total_score: number;
  max_score: number;
  percentage: number;
}

interface PDFQuizViewProps {
  quizId: number;
  onBack: () => void;
}

export default function PDFQuizView({ quizId, onBack }: PDFQuizViewProps) {
  const [quiz, setQuiz] = useState<{
    id: number;
    title: string;
    questions: QuizQuestion[];
  } | null>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [showHints, setShowHints] = useState<Record<number, boolean>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [results, setResults] = useState<QuizSubmissionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchQuiz();
  }, [quizId]);

  const fetchQuiz = async () => {
    try {
      setLoading(true);
      const userId = 1; // For now, use a default user ID
      
      const response = await fetch(`/api/pdf-quizzes/quiz/${quizId}`, {
        headers: {
          "Authorization": `Bearer ${userId}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch quiz: ${response.statusText}`);
      }

      const quizData = await response.json();
      setQuiz(quizData);
    } catch (error) {
      console.error("Error fetching quiz:", error);
      setError(error instanceof Error ? error.message : "Failed to load quiz");
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerChange = (questionId: number, answer: string) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }));
  };

  const toggleHint = (questionId: number) => {
    setShowHints(prev => ({
      ...prev,
      [questionId]: !prev[questionId]
    }));
  };

  const handleSubmit = async () => {
    if (!quiz) return;

    setIsSubmitting(true);
    try {
      const userId = 1; // For now, use a default user ID
      
      const submissionData = {
        quiz_id: quizId,
        answers: Object.entries(answers).map(([questionId, answer]) => ({
          question_id: parseInt(questionId),
          answer: answer
        }))
      };

      const response = await fetch(`/api/pdf-quizzes/quiz/${quizId}/submit`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${userId}`,
        },
        body: JSON.stringify(submissionData),
      });

      if (!response.ok) {
        throw new Error(`Submission failed: ${response.statusText}`);
      }

      const result = await response.json();
      setResults(result);
    } catch (error) {
      console.error("Error submitting quiz:", error);
      setError(error instanceof Error ? error.message : "Failed to submit quiz");
    } finally {
      setIsSubmitting(false);
    }
  };

  const getQuestionResult = (questionId: number) => {
    if (!results) return null;
    return results.results.find(r => r.question_id === questionId);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="animate-spin h-8 w-8 text-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <XCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
        <button
          onClick={onBack}
          className="mt-4 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
        >
          Go Back
        </button>
      </div>
    );
  }

  if (!quiz) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <p>Quiz not found.</p>
        <button
          onClick={onBack}
          className="mt-4 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
        >
          Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={onBack}
          className="mb-4 text-blue-600 hover:text-blue-800 flex items-center"
        >
          ← Back to Upload
        </button>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">{quiz.title}</h1>
        <p className="text-gray-600">
          {quiz.questions.length} questions • Read each question carefully and provide your answers below.
        </p>
      </div>

      {/* Results Summary */}
      {results && (
        <div className="mb-8 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Trophy className="h-8 w-8 text-yellow-500" />
              <div>
                <h2 className="text-xl font-bold text-gray-900">
                  Quiz Results
                </h2>
                <p className="text-gray-600">
                  Score: {results.total_score}/{results.max_score} ({results.percentage.toFixed(1)}%)
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-blue-600">
                {results.percentage.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-500">
                {results.total_score} of {results.max_score} points
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Questions */}
      <div className="space-y-8">
        {quiz.questions.map((question, index) => {
          const result = getQuestionResult(question.id);
          const isCorrect = result?.is_correct;
          const showResult = results !== null;

          return (
            <div
              key={question.id}
              className={`bg-white rounded-lg shadow-md p-6 border-2 ${
                showResult
                  ? isCorrect
                    ? "border-green-200 bg-green-50"
                    : "border-red-200 bg-red-50"
                  : "border-gray-200"
              }`}
            >
              {/* Question Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                    {index + 1}
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">
                      {question.question_text}
                    </h3>
                    <div className="flex items-center space-x-2 mt-1">
                      <BookOpen className="h-4 w-4 text-gray-400" />
                      <span className="text-sm text-gray-500">{question.citation}</span>
                    </div>
                  </div>
                </div>
                {showResult && (
                  <div className="flex-shrink-0">
                    {isCorrect ? (
                      <CheckCircle className="h-6 w-6 text-green-500" />
                    ) : (
                      <XCircle className="h-6 w-6 text-red-500" />
                    )}
                  </div>
                )}
              </div>

              {/* Question Content */}
              <div className="space-y-4">
                {question.question_type === "mcq" ? (
                  <div className="space-y-2">
                    {question.options?.map((option, optionIndex) => (
                      <label
                        key={optionIndex}
                        className={`flex items-center p-3 rounded-md border cursor-pointer transition-colors ${
                          answers[question.id] === option
                            ? "border-blue-500 bg-blue-50"
                            : "border-gray-200 hover:border-gray-300"
                        } ${
                          showResult
                            ? option === question.correct_answer
                              ? "border-green-500 bg-green-50"
                              : answers[question.id] === option && !isCorrect
                              ? "border-red-500 bg-red-50"
                              : ""
                            : ""
                        }`}
                      >
                        <input
                          type="radio"
                          name={`question-${question.id}`}
                          value={option}
                          checked={answers[question.id] === option}
                          onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                          disabled={showResult}
                          className="sr-only"
                        />
                        <div className="flex items-center justify-center w-4 h-4 border-2 rounded-full mr-3">
                          {answers[question.id] === option && (
                            <div className="w-2 h-2 bg-blue-600 rounded-full" />
                          )}
                        </div>
                        <span className="text-gray-900">{option}</span>
                      </label>
                    ))}
                  </div>
                ) : (
                  <div>
                    <textarea
                      value={answers[question.id] || ""}
                      onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                      disabled={showResult}
                      placeholder="Type your answer here..."
                      className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
                      rows={3}
                    />
                  </div>
                )}

                {/* Hint */}
                <div className="border-t pt-4">
                  <button
                    onClick={() => toggleHint(question.id)}
                    className="flex items-center text-blue-600 hover:text-blue-800 text-sm"
                  >
                    {showHints[question.id] ? (
                      <EyeOff className="h-4 w-4 mr-1" />
                    ) : (
                      <Eye className="h-4 w-4 mr-1" />
                    )}
                    <HelpCircle className="h-4 w-4 mr-1" />
                    {showHints[question.id] ? "Hide Hint" : "Show Hint"}
                  </button>
                  {showHints[question.id] && (
                    <div className="mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                      <p className="text-sm text-yellow-800">{question.hint}</p>
                    </div>
                  )}
                </div>

                {/* Results */}
                {showResult && (
                  <div className="border-t pt-4">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-700">Your Answer:</span>
                        <span className="text-sm text-gray-900">
                          {result && result.user_answer !== undefined && result.user_answer !== ""
                            ? result.user_answer
                            : answers[question.id] || "No answer provided"}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-700">Correct Answer:</span>
                        <span className="text-sm text-gray-900">{question.correct_answer}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-700">Points:</span>
                        <span className="text-sm text-gray-900">
                          {(typeof result?.points_earned === "number" ? result.points_earned : 0)}/
                          {(typeof result?.total_points === "number" ? result.total_points : 0)}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Submit Button */}
      {!results && (
        <div className="mt-8 flex justify-center">
          <button
            onClick={handleSubmit}
            // Disable unless all questions have an answer
            disabled={
              isSubmitting ||
              !quiz ||
              quiz.questions.some(q => !answers[q.id] || answers[q.id].trim() === "")
            }
            className="px-8 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="animate-spin -ml-1 mr-3 h-5 w-5" />
                Submitting...
              </>
            ) : (
              "Submit Quiz"
            )}
          </button>
        </div>
      )}
    </div>
  );
}
