import google.generativeai as genai
from django.conf import settings
import os

# ==================================================
# Configure Gemini (Only Once)
# ==================================================
genai.configure(api_key=settings.GEMINI_API_KEY)

# Create model instance ONCE (Very Important)
model = genai.GenerativeModel("gemini-2.5-flash")


# ==================================================
# Generate Assignment
# ==================================================
def generate_assignment(board, class_name, chapter, num_questions):
    prompt = f"""
Create a school assignment strictly based on the following details:

Board: {board}
Class: {class_name}
Chapter: {chapter}
Number of questions: {num_questions}

Rules:
1. Do not add any extra text
2. Do not add explanations or answers
3. Start directly from Question 1
4. Format clearly as numbered questions
5. Follow NCERT textbook style
"""

    response = model.generate_content(prompt)
    return response.text.strip()


# ==================================================
# Extract Text From File (OCR) → 1 API CALL
# ==================================================
def extract_text_from_file(uploaded_file_path):
    """
    Extracts text from:
    - PDF
    - PNG
    - JPG / JPEG
    """

    if not os.path.exists(uploaded_file_path):
        return ""

    prompt_extract = """
Extract all readable handwritten or printed text from this file.
Return ONLY the text.
Do NOT explain anything.
"""

    # Detect MIME type
    if uploaded_file_path.lower().endswith(".pdf"):
        mime_type = "application/pdf"
    elif uploaded_file_path.lower().endswith(".png"):
        mime_type = "image/png"
    else:
        mime_type = "image/jpeg"

    with open(uploaded_file_path, "rb") as f:
        response = model.generate_content(
            [
                prompt_extract,
                {
                    "mime_type": mime_type,
                    "data": f.read(),
                },
            ]
        )

    return response.text.strip()


# ==================================================
# Evaluate Submission → 1 API CALL
# ==================================================
def evaluate_submission(assignment_text, student_answer, max_marks=10):
    """
    Evaluates student answer question-by-question.
    Always returns marks + feedback.
    """

    prompt_evaluate = f"""
You are a strict school teacher.

Total Marks for this test: {max_marks}

IMPORTANT:
- Divide marks logically based on number of questions.
- If a question is partially correct, give partial marks.
- If a question is not attempted, give 0.
- Final marks MUST NOT exceed {max_marks}.
- Final format must be exactly: Marks: <number>/{max_marks}

Assignment:
{assignment_text}

Student Answer:
{student_answer}

Return EXACT format:

Detailed Analysis:
<Question-wise feedback>

Overall Feedback:
<Summary>

Marks: <number>/{max_marks}
"""

    result = model.generate_content(prompt_evaluate)
    return result.text.strip()


# ==================================================
# Main Processing Function
# ==================================================
def process_and_evaluate_submission(
    assignment_text,
    student_answer_text=None,
    uploaded_file_path=None,
    max_marks=10,
):
    """
    Maximum API Calls:
    - 0 calls → If no answer
    - 1 call → If only text
    - 2 calls → If file + evaluation
    """

    extracted_text = ""

    # ==========================
    # Call 1: OCR (if file exists)
    # ==========================
    if uploaded_file_path:
        extracted_text = extract_text_from_file(uploaded_file_path)

    # ==========================
    # Combine Answers
    # ==========================
    final_student_answer = ""

    if student_answer_text:
        final_student_answer += student_answer_text.strip()

    if extracted_text:
        final_student_answer += "\n" + extracted_text

    # ==========================
    # If no answer → Skip AI
    # ==========================
    if not final_student_answer.strip():
        return {
            "evaluation": "Marks: 0\n\nFeedback:\nNo answer submitted.",
            "extracted_text": extracted_text,
            "final_answer": final_student_answer,
        }

    # ==========================
    # Call 2: Evaluation
    # ==========================
    evaluation_result = evaluate_submission(
        assignment_text,
        final_student_answer,
        max_marks,
    )

    return {
        "evaluation": evaluation_result,
        "extracted_text": extracted_text,
        "final_answer": final_student_answer,
    }
