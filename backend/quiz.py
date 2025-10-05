import os
import groq
from typing import List, Dict, Any, Optional
import json
from fastapi import HTTPException
from dotenv import load_dotenv
load_dotenv()

class QuizGenerator:
    def __init__(self, api_key: str = None):
        # Initialize Groq client
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        self.client = groq.Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile" 
    
    def generate_quiz_from_content(self, content: str, num_questions: int = 5, question_types: List[str] = None) -> Dict[str, Any]:
        """
        Generate quiz questions from presentation content using Groq AI
        
        Args:
            content: Text content from presentation slides
            num_questions: Number of questions to generate
            question_types: Types of questions (mcq, true_false, short_answer)
        
        Returns:
            Dictionary containing quiz data
        """
        try:
            if question_types is None:
                question_types = ["mcq"]
            
            prompt = self._build_quiz_prompt(content, num_questions, question_types)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert educational content creator. 
                        Create engaging quiz questions based on presentation content.
                        Always return valid JSON format without any additional text.
                        Make questions relevant, clear, and educational."""
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON response
            quiz_data = json.loads(response.choices[0].message.content)
            
            # Add metadata
            quiz_data["metadata"] = {
                "total_questions": len(quiz_data.get("questions", [])),
                "question_types": question_types,
                "model_used": self.model
            }
            
            return quiz_data
            
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")
    
    def _build_quiz_prompt(self, content: str, num_questions: int, question_types: List[str]) -> str:
        """Build the prompt for quiz generation"""
        
        type_instructions = {
            "mcq": "Multiple choice questions with 4 options (A, B, C, D)",
            "true_false": "True/False questions",
            "short_answer": "Short answer questions (1-2 word answers)",
            "fill_blank": "Fill in the blank questions"
        }
        
        selected_instructions = [type_instructions.get(t, t) for t in question_types]
        
        return f"""
        Based on the following presentation content, create {num_questions} quiz questions.
        
        PRESENTATION CONTENT:
        {content}
        
        REQUIREMENTS:
        - Create exactly {num_questions} questions
        - Question types: {', '.join(selected_instructions)}
        - For MCQs: Provide 4 plausible options with one correct answer
        - Include brief explanations for answers
        - Questions should test understanding of key concepts
        - Cover different aspects of the content
        - Make questions clear and unambiguous
        
        RESPONSE FORMAT (JSON):
        {{
            "quiz_title": "Quiz Based on Presentation Content",
            "questions": [
                {{
                    "id": 1,
                    "type": "mcq",
                    "question": "What is the main topic discussed?",
                    "options": {{
                        "A": "Option A text",
                        "B": "Option B text",
                        "C": "Option C text",
                        "D": "Option D text"
                    }},
                    "correct_answer": "A",
                    "explanation": "Brief explanation why this is correct"
                }},
                {{
                    "id": 2,
                    "type": "true_false",
                    "question": "This statement is true or false?",
                    "correct_answer": "true",
                    "explanation": "Brief explanation"
                }}
            ],
            "summary": {{
                "total_questions": {num_questions},
                "difficulty": "mixed",
                "estimated_time": "5-10 minutes"
            }}
        }}
        
        Return only valid JSON without any additional text.
        """
    
    def generate_quiz_by_slides(self, ppt_file_path: str, slide_numbers: List[int], num_questions: int = 5, question_types: List[str] = None) -> Dict[str, Any]:
        """
        Generate quiz from specific slides of a PPT file
        """
        try:
            from ppt import extract_text_from_ppt, get_slide_content
            
            # Extract content from specific slides
            content_parts = []
            for slide_num in slide_numbers:
                try:
                    slide_content = get_slide_content(ppt_file_path, slide_num - 1)  # 0-indexed
                    content_parts.append(f"Slide {slide_num}: {slide_content.get('content', '')}")
                except Exception as e:
                    continue
            
            if not content_parts:
                raise HTTPException(status_code=400, detail="No content found in specified slides")
            
            combined_content = "\n".join(content_parts)
            return self.generate_quiz_from_content(combined_content, num_questions, question_types)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing slides: {str(e)}")

# Initialize quiz generator
try:
    quiz_generator = QuizGenerator()
except Exception as e:
    print(f"Warning: Quiz generator initialization failed: {e}")
    quiz_generator = None