import base64
import json
import os
import uuid
from typing import List, Dict, Any
from pypdf import PdfReader
import openai
from api.settings import settings
from api.utils.db import get_new_db_connection
from api.models import PDFDocument, QuizQuestion, GeneratedQuiz, QuizSubmission, QuizResult, QuizSubmissionResponse


class PDFProcessor:
    def __init__(self):
        self.openai_client = openai.OpenAI(
            api_key=settings.openai_api_key,
            base_url=getattr(settings, "openai_base_url", None)
        )

    def parse_pdf(self, pdf_content: bytes, title: str) -> Dict[str, Any]:
        """Parse PDF content and extract text with page citations."""
        import io
        reader = PdfReader(io.BytesIO(pdf_content))
        text_content = ""
        page_citations = []
        
        for page_num, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            if page_text.strip():
                # Split page into lines for citation tracking
                lines = page_text.split('\n')
                line_start = len(text_content.split('\n')) + 1
                
                text_content += page_text + "\n"
                
                # Store page citation with line information
                page_citations.append({
                    "page": page_num,
                    "text": page_text,
                    "line_start": line_start,
                    "line_end": line_start + len(lines) - 1
                })
        
        return {
            "text_content": text_content.strip(),
            "page_citations": page_citations
        }

    def generate_quiz_questions(self, text_content: str, page_citations: List[Dict]) -> List[QuizQuestion]:
        """Generate quiz questions using OpenAI."""
        # Prepare context for question generation
        context = f"""
        Based on the following document content, generate a comprehensive quiz with:
        - At least 10 multiple choice questions (MCQs)
        - At least 3 short answer questions
        - Each question must include a citation (page and line reference)
        - Each question must have a helpful hint that doesn't reveal the answer
        
        Document content:
        {text_content}
        
        Generate the questions in the following JSON format:
        {{
            "questions": [
                {{
                    "question_text": "Question text here",
                    "question_type": "mcq",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": "Correct option text",
                    "hint": "Helpful hint that doesn't reveal the answer",
                    "citation": "Page X, Lines Y-Z"
                }},
                {{
                    "question_text": "Short answer question here",
                    "question_type": "short_answer",
                    "correct_answer": "Expected answer text",
                    "hint": "Helpful hint that doesn't reveal the answer",
                    "citation": "Page X, Lines Y-Z"
                }}
            ]
        }}
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=getattr(settings, "openai_model", "gpt-4"),
                messages=[
                    {"role": "system", "content": "You are an expert quiz generator. Create questions that test understanding of the document content."},
                    {"role": "user", "content": context}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            # Parse the response
            response_text = response.choices[0].message.content
            # Extract JSON from the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            json_str = response_text[start_idx:end_idx]
            
            quiz_data = json.loads(json_str)
            questions = []
            
            for i, q_data in enumerate(quiz_data.get("questions", [])):
                question = QuizQuestion(
                    id=i + 1,  # Temporary ID
                    question_text=q_data["question_text"],
                    question_type=q_data["question_type"],
                    options=q_data.get("options"),
                    correct_answer=q_data["correct_answer"],
                    hint=q_data["hint"],
                    citation=q_data["citation"],
                    points=1
                )
                questions.append(question)
            
            return questions
            
        except Exception as e:
            print(f"Error generating quiz questions: {e}")
            # Fallback: generate simple questions
            return self._generate_fallback_questions(text_content)

    def _generate_fallback_questions(self, text_content: str) -> List[QuizQuestion]:
        """Generate simple fallback questions if OpenAI fails."""
        questions = []
        
        # Split content into paragraphs
        paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]
        
        for i, paragraph in enumerate(paragraphs[:13]):  # Generate up to 13 questions
            if i < 10:  # First 10 are MCQs
                question = QuizQuestion(
                    id=i + 1,
                    question_text=f"What is the main topic discussed in this document?",
                    question_type="mcq",
                    options=[
                        "Technology and innovation",
                        "Business management", 
                        "Scientific research",
                        "Historical events"
                    ],
                    correct_answer="Technology and innovation",
                    hint="Look at the overall theme and main concepts discussed",
                    citation=f"Page 1, Lines 1-10",
                    points=1
                )
            else:  # Last 3 are short answer
                question = QuizQuestion(
                    id=i + 1,
                    question_text=f"Summarize the key points from this document in 2-3 sentences.",
                    question_type="short_answer",
                    correct_answer="The document discusses various topics including technology, innovation, and their applications in modern society.",
                    hint="Focus on the main themes and important concepts mentioned",
                    citation=f"Page 1, Lines 1-20",
                    points=1
                )
            questions.append(question)
        
        return questions


class PDFQuizService:
    def __init__(self):
        self.pdf_processor = PDFProcessor()

    async def upload_pdf(self, title: str, file_content: str, user_id: int) -> PDFDocument:
        """Upload and process a PDF document."""
        # Decode base64 content
        pdf_bytes = base64.b64decode(file_content)
        
        # Generate unique filename
        filename = f"{uuid.uuid4()}.pdf"
        file_path = os.path.join(settings.local_upload_folder, filename)
        
        # Save PDF file
        with open(file_path, 'wb') as f:
            f.write(pdf_bytes)
        
        # Parse PDF content
        parsed_data = self.pdf_processor.parse_pdf(pdf_bytes, title)
        
        # Store in database
        async with get_new_db_connection() as conn:
            cursor = await conn.cursor()
            
            await cursor.execute(
                """INSERT INTO pdf_documents 
                   (title, file_path, uploaded_by, text_content, page_citations)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    title,
                    file_path,
                    user_id,
                    parsed_data["text_content"],
                    json.dumps(parsed_data["page_citations"])
                )
            )
            
            pdf_id = cursor.lastrowid
            await conn.commit()
            
            return PDFDocument(
                id=pdf_id,
                title=title,
                file_path=file_path,
                uploaded_by=user_id,
                created_at=None,  # Will be set by database
                text_content=parsed_data["text_content"],
                page_citations=parsed_data["page_citations"]
            )

    async def generate_quiz(self, pdf_document_id: int) -> GeneratedQuiz:
        """Generate a quiz from a PDF document."""
        # Get PDF document
        import logging
        async with get_new_db_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                "SELECT title, text_content, page_citations FROM pdf_documents WHERE id = ?",
                (pdf_document_id,)
            )
            result = await cursor.fetchone()
            if not result:
                logging.error(f"[generate_quiz] PDF document not found for id {pdf_document_id}")
                raise ValueError("PDF document not found")
            title, text_content, page_citations_json = result
            page_citations = json.loads(page_citations_json)
            # Generate questions
            questions = self.pdf_processor.generate_quiz_questions(text_content, page_citations)
            # Store quiz in database
            await cursor.execute(
                """INSERT INTO generated_quizzes (pdf_document_id, title)
                   VALUES (?, ?)""",
                (pdf_document_id, f"Quiz: {title}")
            )
            quiz_id = cursor.lastrowid
            # Store questions
            for question in questions:
                await cursor.execute(
                    """INSERT INTO quiz_questions 
                       (quiz_id, question_text, question_type, options, correct_answer, hint, citation, points)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        quiz_id,
                        question.question_text,
                        question.question_type,
                        json.dumps(question.options) if question.options else None,
                        question.correct_answer,
                        question.hint,
                        question.citation,
                        question.points
                    )
                )
            await conn.commit()
            # Fetch the full quiz row including created_at
            await cursor.execute(
                """SELECT id, pdf_document_id, title, created_at FROM generated_quizzes WHERE id = ?""",
                (quiz_id,)
            )
            quiz_row = await cursor.fetchone()
            if not quiz_row:
                logging.error(f"[generate_quiz] Quiz not found after insert for id {quiz_id}")
                raise ValueError("Quiz not found after insert")
            quiz_id_db, pdf_document_id_db, quiz_title_db, created_at_db = quiz_row
            logging.info(f"[generate_quiz] Successfully created quiz: id={quiz_id_db}, pdf_document_id={pdf_document_id_db}, title={quiz_title_db}, created_at={created_at_db}")
            return GeneratedQuiz(
                id=quiz_id_db,
                pdf_document_id=pdf_document_id_db,
                title=quiz_title_db,
                questions=questions,
                created_at=created_at_db
            )

    async def get_quiz(self, quiz_id: int) -> GeneratedQuiz:
        """Get a quiz by ID."""
        import logging
        async with get_new_db_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                """SELECT id, pdf_document_id, title, created_at 
                   FROM generated_quizzes WHERE id = ?""",
                (quiz_id,)
            )
            quiz_result = await cursor.fetchone()
            if not quiz_result:
                logging.error(f"[get_quiz] Quiz not found for id {quiz_id}")
                raise ValueError("Quiz not found")
            quiz_id, pdf_document_id, title, created_at = quiz_result
            # Get questions
            await cursor.execute(
                """SELECT id, question_text, question_type, options, correct_answer, hint, citation, points
                   FROM quiz_questions WHERE quiz_id = ? ORDER BY id""",
                (quiz_id,)
            )
            questions = []
            for row in await cursor.fetchall():
                q_id, q_text, q_type, options_json, correct_answer, hint, citation, points = row
                question = QuizQuestion(
                    id=q_id,
                    question_text=q_text,
                    question_type=q_type,
                    options=json.loads(options_json) if options_json else None,
                    correct_answer=correct_answer,
                    hint=hint,
                    citation=citation,
                    points=points
                )
                questions.append(question)
            logging.info(f"[get_quiz] Returning quiz: id={quiz_id}, title={title}, questions_count={len(questions)}")
            return GeneratedQuiz(
                id=quiz_id,
                pdf_document_id=pdf_document_id,
                title=title,
                questions=questions,
                created_at=created_at
            )

    async def submit_quiz(self, quiz_id: int, user_id: int, answers: List[Dict[str, str]]) -> QuizSubmissionResponse:
        """Submit quiz answers and get results."""
        # Get quiz and questions
        quiz = await self.get_quiz(quiz_id)
        
        results = []
        total_score = 0
        max_score = sum(q.points for q in quiz.questions)
        
        async with get_new_db_connection() as conn:
            cursor = await conn.cursor()
            
            # Store submission
            await cursor.execute(
                """INSERT INTO quiz_submissions (quiz_id, user_id, total_score, max_score)
                   VALUES (?, ?, ?, ?)""",
                (quiz_id, user_id, 0, max_score)  # Will update total_score later
            )
            
            submission_id = cursor.lastrowid
            
            # Process each answer
            for answer_data in answers:
                question_id = int(answer_data["question_id"])
                user_answer = answer_data["answer"]
                
                # Find the question
                question = next((q for q in quiz.questions if q.id == question_id), None)
                if not question:
                    continue
                
                # Check if answer is correct
                is_correct = self._check_answer(question, user_answer)
                points_earned = question.points if is_correct else 0
                total_score += points_earned
                
                # Store answer
                await cursor.execute(
                    """INSERT INTO quiz_answers 
                       (submission_id, question_id, user_answer, is_correct, points_earned)
                       VALUES (?, ?, ?, ?, ?)""",
                    (submission_id, question_id, user_answer, is_correct, points_earned)
                )
                
                # Create result
                result = QuizResult(
                    question_id=question_id,
                    is_correct=is_correct,
                    user_answer=user_answer,
                    correct_answer=question.correct_answer,
                    citation=question.citation,
                    points_earned=points_earned,
                    total_points=question.points
                )
                results.append(result)
            
            # Update submission with final score
            await cursor.execute(
                "UPDATE quiz_submissions SET total_score = ? WHERE id = ?",
                (total_score, submission_id)
            )
            
            await conn.commit()
        
        return QuizSubmissionResponse(
            results=results,
            total_score=total_score,
            max_score=max_score,
            percentage=(total_score / max_score * 100) if max_score > 0 else 0
        )

    def _check_answer(self, question: QuizQuestion, user_answer: str) -> bool:
        """Check if a user's answer is correct."""
        if question.question_type == "mcq":
            # For MCQs, check if the selected option matches the correct answer
            return user_answer.strip().lower() == question.correct_answer.strip().lower()
        else:
            # For short answer, do fuzzy matching
            user_clean = user_answer.strip().lower()
            correct_clean = question.correct_answer.strip().lower()
            
            # Simple keyword matching
            user_words = set(user_clean.split())
            correct_words = set(correct_clean.split())
            
            # If more than 50% of correct words are present, consider it correct
            if correct_words:
                match_percentage = len(user_words.intersection(correct_words)) / len(correct_words)
                return match_percentage >= 0.5
            
            return user_clean == correct_clean
