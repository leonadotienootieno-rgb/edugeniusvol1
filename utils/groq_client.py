"""
GROQ AI Client for EduGenius
Handles worksheet generation using Llama 3 via GROQ API
"""

import streamlit as st
from groq import Groq
import json

def get_groq_client():
    """Initialize and return GROQ client"""
    try:
        api_key = st.secrets.get("GROQ_API_KEY", "")
        if not api_key:
            return None
        return Groq(api_key=api_key)
    except Exception:
        return None

def generate_worksheet(
    curriculum: str,
    subject: str,
    topic: str,
    subtopics: list,
    question_type: str,
    num_questions: int,
    difficulty: str,
    include_marking_scheme: bool
) -> str:
    """
    Generate a worksheet with optional marking scheme using GROQ
    
    Parameters:
    - curriculum: e.g., "Cambridge IGCSE", "IB"
    - subject: e.g., "Biology (0610)"
    - topic: The main topic
    - subtopics: List of specific subtopics to cover
    - question_type: MCQ, Structured, Essay, Practical, or Mixed
    - num_questions: Number of questions to generate
    - difficulty: Easy, Medium, Hard, or Exam Style
    - include_marking_scheme: Whether to include answers/marks
    
    Returns:
    - Formatted worksheet text with questions and optional marking scheme
    """
    client = get_groq_client()
    
    if not client:
        return None
    
    # Build the prompt
    subtopics_str = ", ".join(subtopics) if subtopics else topic
    
    prompt = f"""You are an expert {curriculum} {subject} teacher with 20 years of experience.

Create a professional, exam-quality worksheet for {curriculum} {subject} students.

TOPIC: {topic}
SUBTOPICS: {subtopics_str}
QUESTION TYPE: {question_type}
NUMBER OF QUESTIONS: {num_questions}
DIFFICULTY LEVEL: {difficulty}

Requirements:
1. Each question should clearly state the marks available in brackets [ ]
2. Questions should match {curriculum} exam style and format
3. Include a mix of recall, application, and analysis questions
4. For MCQ: provide 4 options (A-D) with one correct answer
5. For Practical: include data analysis, graph interpretation, or experimental design
6. Number questions clearly (1, 2, 3...)
7. Leave appropriate space for student answers
8. Use proper scientific terminology and units
"""

    if include_marking_scheme:
        prompt += """
9. After ALL questions, include a detailed MARKING SCHEME section
10. Marking scheme should show:
    - Correct answers for each question
    - Mark breakdown for multi-part questions
    - Acceptable alternative answers where applicable
    - Common mistakes to watch for
    - Grade boundaries suggestion (A*, A, B, C, D, E)
"""

    prompt += f"""
FORMAT:
---
{curriculum} {subject}
{topic} - Worksheet
{difficulty} Level | {question_type} Questions
Total Marks: [appropriate total]
Time Allowed: [appropriate time]
---

[Questions here]

[MARKING SCHEME - if requested]

Generate the complete worksheet now. Make it ready to print and use in class.
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "You are an expert teacher who creates high-quality, exam-ready worksheets. Always format output clearly with proper spacing, numbering, and professional layout."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4096,
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        st.error(f"Error generating worksheet: {str(e)}")
        return None

def generate_quick_quiz(
    curriculum: str,
    subject: str,
    topic: str,
    num_questions: int = 5
) -> str:
    """Generate a quick MCQ quiz for revision"""
    
    client = get_groq_client()
    
    if not client:
        return None
    
    prompt = f"""Create a quick {num_questions}-question multiple choice quiz for {curriculum} {subject} on the topic: {topic}.

Format:
1. [Question text]
   A) [Option]
   B) [Option]
   C) [Option]
   D) [Option]
   [Answer: Letter - Brief explanation]

Make questions appropriate for {curriculum} level. Include the answer key at the end."""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "Create clear, concise MCQ quizzes with accurate answers."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048,
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        st.error(f"Error generating quiz: {str(e)}")
        return None
