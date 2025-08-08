"use client";

import { useState } from "react";
import { Upload, FileText, Loader2, CheckCircle, AlertCircle } from "lucide-react";

interface PDFUploadProps {
  onQuizGenerated: (quizId: number, title: string) => void;
}

export default function PDFUpload({ onQuizGenerated }: PDFUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{
    type: "success" | "error" | null;
    message: string;
  }>({ type: null, message: "" });

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile && selectedFile.type === "application/pdf") {
      setFile(selectedFile);
      // Auto-generate title from filename
      const fileName = selectedFile.name.replace(/\.pdf$/i, "");
      setTitle(fileName);
    } else if (selectedFile) {
      setUploadStatus({
        type: "error",
        message: "Please select a valid PDF file.",
      });
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!file || !title.trim()) {
      setUploadStatus({
        type: "error",
        message: "Please select a PDF file and enter a title.",
      });
      return;
    }

    setIsUploading(true);
    setUploadStatus({ type: null, message: "" });

    try {
      // Convert file to base64
      const base64 = await fileToBase64(file);

                        // Get user ID from session (you'll need to implement this)
                  const userId = 1; // For MVP, use a default user ID

      const response = await fetch("/api/pdf-quizzes/upload", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${userId}`, // Simple auth for MVP
        },
        body: JSON.stringify({
          title: title.trim(),
          file_content: base64,
        }),
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const result = await response.json();

      setUploadStatus({
        type: "success",
        message: result.message,
      });

      // Call the callback with the generated quiz info
      onQuizGenerated(result.id, result.title);

      // Reset form
      setFile(null);
      setTitle("");
      
    } catch (error) {
      console.error("Upload error:", error);
      setUploadStatus({
        type: "error",
        message: error instanceof Error ? error.message : "Upload failed. Please try again.",
      });
    } finally {
      setIsUploading(false);
    }
  };

  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const result = reader.result as string;
        // Remove the data URL prefix to get just the base64 content
        const base64 = result.split(",")[1];
        resolve(base64);
      };
      reader.onerror = (error) => reject(error);
    });
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md">
      <div className="text-center mb-6">
        <FileText className="mx-auto h-12 w-12 text-blue-600 mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Upload PDF to Generate Quiz
        </h2>
        <p className="text-gray-600">
          Upload a PDF document and we'll automatically generate a comprehensive quiz with questions and citations.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
            Quiz Title
          </label>
          <input
            type="text"
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Enter a title for your quiz"
            required
          />
        </div>

        <div>
          <label htmlFor="pdf-file" className="block text-sm font-medium text-gray-700 mb-2">
            PDF Document
          </label>
          <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md hover:border-gray-400 transition-colors">
            <div className="space-y-1 text-center">
              <Upload className="mx-auto h-12 w-12 text-gray-400" />
              <div className="flex text-sm text-gray-600">
                <label
                  htmlFor="pdf-file"
                  className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
                >
                  <span>Upload a PDF file</span>
                  <input
                    id="pdf-file"
                    name="pdf-file"
                    type="file"
                    accept=".pdf"
                    className="sr-only"
                    onChange={handleFileChange}
                  />
                </label>
                <p className="pl-1">or drag and drop</p>
              </div>
              <p className="text-xs text-gray-500">PDF up to 10MB</p>
            </div>
          </div>
          {file && (
            <div className="mt-2 flex items-center text-sm text-gray-600">
              <FileText className="h-4 w-4 mr-2" />
              {file.name}
            </div>
          )}
        </div>

        {uploadStatus.type && (
          <div
            className={`p-4 rounded-md ${
              uploadStatus.type === "success"
                ? "bg-green-50 border border-green-200"
                : "bg-red-50 border border-red-200"
            }`}
          >
            <div className="flex">
              <div className="flex-shrink-0">
                {uploadStatus.type === "success" ? (
                  <CheckCircle className="h-5 w-5 text-green-400" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-red-400" />
                )}
              </div>
              <div className="ml-3">
                <p
                  className={`text-sm ${
                    uploadStatus.type === "success" ? "text-green-800" : "text-red-800"
                  }`}
                >
                  {uploadStatus.message}
                </p>
              </div>
            </div>
          </div>
        )}

        <button
          type="submit"
          disabled={isUploading || !file || !title.trim()}
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isUploading ? (
            <>
              <Loader2 className="animate-spin -ml-1 mr-3 h-5 w-5" />
              Generating Quiz...
            </>
          ) : (
            "Generate Quiz"
          )}
        </button>
      </form>
    </div>
  );
}
