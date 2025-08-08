


from fastapi import APIRouter, HTTPException, Depends
from typing import List
import json
import logging
import traceback
from api.pdf_quiz import PDFQuizService
from api.models import (
    PDFUploadRequest,
    PDFUploadResponse,
    QuizSubmission,
    QuizSubmissionResponse,
    GeneratedQuiz
)
from api.routes.auth import get_current_user_id

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

router = APIRouter()
pdf_quiz_service = PDFQuizService()


@router.post("/upload", response_model=PDFUploadResponse)
async def upload_pdf(
    request: PDFUploadRequest,
    user_id: int = Depends(get_current_user_id)
):
    """Upload a PDF document and generate a quiz."""
    try:
        # Upload and process PDF
        pdf_document = await pdf_quiz_service.upload_pdf(
            request.title,
            request.file_content,
            user_id
        )
    except Exception as e:
        logging.error("Error uploading PDF: %s\n%s", str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error uploading PDF: {str(e)}")

    try:
        # Generate quiz
        quiz = await pdf_quiz_service.generate_quiz(pdf_document.id)
        if not quiz or not quiz.questions:
            logging.error("Quiz generation failed: No quiz or questions returned for PDF id %s", pdf_document.id)
            raise HTTPException(status_code=500, detail="Quiz generation failed: No questions generated.")
        return PDFUploadResponse(
            id=quiz.id,
            title=quiz.title,
            message=f"PDF uploaded and quiz generated successfully! Quiz ID: {quiz.id}"
        )
    except Exception as e:
        logging.error("Error generating quiz: %s\n%s", str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error generating quiz: {str(e)}")


@router.post("/quiz/{quiz_id}/submit", response_model=QuizSubmissionResponse)
async def submit_quiz(
    quiz_id: int,
    submission: QuizSubmission,
    user_id: int = Depends(get_current_user_id)
):
    """Submit quiz answers and get results."""
    try:
        # Validate that the quiz_id in the path matches the submission
        if quiz_id != submission.quiz_id:
            raise HTTPException(status_code=400, detail="Quiz ID mismatch")
        
        # Convert answers to the expected format
        answers = []
        for answer in submission.answers:
            if "question_id" in answer and "answer" in answer:
                answers.append({
                    "question_id": answer["question_id"],
                    "answer": answer["answer"]
                })
        
        result = await pdf_quiz_service.submit_quiz(quiz_id, user_id, answers)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting quiz: {str(e)}")


@router.get("/quiz/{quiz_id}", response_model=GeneratedQuiz)
async def get_quiz(quiz_id: int):
    try:
        quiz = await pdf_quiz_service.get_quiz(quiz_id)
        return quiz
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error("Error fetching quiz: %s\n%s", str(e), traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error fetching quiz: {str(e)}")

@router.get("/quizzes", response_model=List[GeneratedQuiz])
async def list_user_quizzes(
    user_id: int = Depends(get_current_user_id)
):
    """List all quizzes for the current user."""
    try:
        # This would need to be implemented in the service
        # For now, return empty list
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving quizzes: {str(e)}")
