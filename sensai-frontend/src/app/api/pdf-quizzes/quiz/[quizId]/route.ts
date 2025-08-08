import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export async function GET(
  request: NextRequest,
  context: { params: { quizId: string } }
) {
  try {
    const { quizId } = await context.params;

    // Forward the request to the backend
    const response = await fetch(`${BACKEND_URL}/pdf-quizzes/quiz/${quizId}`, {
      method: "GET",
      headers: {
        "Authorization": request.headers.get("Authorization") || "",
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json(
        { error: `Backend error: ${response.statusText}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Quiz retrieval error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
