import os
import groq
from typing import List, Dict, Any, Optional
import json
from fastapi import HTTPException
from dotenv import load_dotenv
load_dotenv()

class ExplanationGenerator:
    def __init__(self, api_key: str = None):
        # Initialize Groq client
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        self.client = groq.Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"
    
    def generate_explanation_from_content(self, content: str, explanation_type: str = "detailed") -> Dict[str, Any]:
        """
        Generate explanations from presentation content using Groq AI
        
        Args:
            content: Text content from presentation slides
            explanation_type: Type of explanation ("detailed", "simple", "key_points")
        
        Returns:
            Dictionary containing explanation data
        """
        try:
            prompt = self._build_explanation_prompt(content, explanation_type)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert educator and explainer. 
                        Create clear, engaging explanations for presentation content.
                        Always return valid JSON format without any additional text.
                        Make explanations educational, accurate, and easy to understand."""
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
            explanation_data = json.loads(response.choices[0].message.content)
            
            # Add metadata
            explanation_data["metadata"] = {
                "explanation_type": explanation_type,
                "model_used": self.model,
                "content_length": len(content)
            }
            
            return explanation_data
            
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Explanation generation failed: {str(e)}")
    
    def _build_explanation_prompt(self, content: str, explanation_type: str) -> str:
        """Build the prompt for explanation generation"""
        
        type_instructions = {
            "detailed": "Provide comprehensive, in-depth explanations covering all concepts",
            "simple": "Provide simplified explanations suitable for beginners",
            "key_points": "Extract and explain the main key points and takeaways"
        }
        
        instruction = type_instructions.get(explanation_type, "Provide detailed explanations")
        
        return f"""
        Based on the following presentation content, create an educational explanation.
        
        PRESENTATION CONTENT:
        {content}
        
        REQUIREMENTS:
        - {instruction}
        - Break down complex concepts into understandable parts
        - Use clear, concise language
        - Highlight important concepts and relationships
        - Provide context and practical significance where relevant
        - Structure the explanation logically
        
        RESPONSE FORMAT (JSON):
        {{
            "explanation_title": "Explanation of Presentation Content",
            "summary": "Brief overall summary of the content",
            "key_concepts": [
                {{
                    "concept": "Concept Name",
                    "explanation": "Clear explanation of the concept",
                    "importance": "Why this concept matters"
                }}
            ],
            "detailed_explanation": "Comprehensive explanation covering all main points",
            "takeaways": [
                "Key takeaway 1",
                "Key takeaway 2",
                "Key takeaway 3"
            ],
            "difficulty_level": "beginner|intermediate|advanced"
        }}
        
        Return only valid JSON without any additional text.
        """
    
    def generate_explanation_by_slides(self, ppt_file_path: str, slide_numbers: List[int], explanation_type: str = "detailed") -> Dict[str, Any]:
        """
        Generate explanation from specific slides of a PPT file
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
            return self.generate_explanation_from_content(combined_content, explanation_type)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing slides: {str(e)}")
    
    def generate_slide_by_slide_explanation(self, ppt_file_path: str, slide_numbers: List[int]) -> Dict[str, Any]:
        """
        Generate explanations for each slide individually
        """
        try:
            from ppt import get_slide_content
            
            slide_explanations = []
            
            for slide_num in slide_numbers:
                try:
                    slide_content = get_slide_content(ppt_file_path, slide_num - 1)
                    content = slide_content.get('content', '')
                    
                    if content.strip():
                        # Generate explanation for this specific slide
                        prompt = f"""
                        Explain the content of this single presentation slide:
                        
                        SLIDE {slide_num} CONTENT:
                        {content}
                        
                        Provide a clear explanation of what this slide is about, 
                        the key messages it conveys, and any important details.
                        
                        Return JSON format:
                        {{
                            "slide_number": {slide_num},
                            "slide_title": "Brief title of the slide",
                            "main_topic": "Main topic covered",
                            "explanation": "Detailed explanation of the slide content",
                            "key_points": ["Point 1", "Point 2", "Point 3"]
                        }}
                        """
                        
                        response = self.client.chat.completions.create(
                            model=self.model,
                            messages=[
                                {
                                    "role": "system",
                                    "content": "You are an expert presentation analyst. Provide clear explanations for individual slides."
                                },
                                {
                                    "role": "user", 
                                    "content": prompt
                                }
                            ],
                            temperature=0.7,
                            max_tokens=1000,
                            response_format={"type": "json_object"}
                        )
                        
                        slide_data = json.loads(response.choices[0].message.content)
                        slide_explanations.append(slide_data)
                    else:
                        slide_explanations.append({
                            "slide_number": slide_num,
                            "slide_title": "Empty Slide",
                            "main_topic": "No content",
                            "explanation": "This slide appears to be empty or contains no text content.",
                            "key_points": []
                        })
                        
                except Exception as e:
                    slide_explanations.append({
                        "slide_number": slide_num,
                        "slide_title": "Error Processing Slide",
                        "main_topic": "Processing Error",
                        "explanation": f"Could not generate explanation for this slide: {str(e)}",
                        "key_points": []
                    })
            
            return {
                "type": "slide_by_slide",
                "total_slides": len(slide_explanations),
                "slide_explanations": slide_explanations,
                "metadata": {
                    "model_used": self.model,
                    "slides_covered": slide_numbers
                }
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating slide-by-slide explanations: {str(e)}")

# Initialize explanation generator
try:
    explanation_generator = ExplanationGenerator()
except Exception as e:
    print(f"Warning: Explanation generator initialization failed: {e}")
    explanation_generator = None