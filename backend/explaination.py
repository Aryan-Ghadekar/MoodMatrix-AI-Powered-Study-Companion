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
                        Always include relevant real-life examples to make concepts relatable.
                        Always return valid JSON format without any additional text.
                        Make explanations educational, accurate, and easy to understand."""
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2500,  # Increased for real-life examples
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
        """Build the prompt for explanation generation with real-life examples"""
        
        type_instructions = {
            "detailed": "Provide comprehensive, in-depth explanations covering all concepts with real-life examples",
            "simple": "Provide simplified explanations suitable for beginners with practical examples", 
            "key_points": "Extract and explain the main key points and takeaways with real-world applications"
        }
        
        instruction = type_instructions.get(explanation_type, "Provide detailed explanations with real-life examples")
        
        return f"""
        Based on the following presentation content, create an educational explanation with REAL-LIFE EXAMPLES.
        
        PRESENTATION CONTENT:
        {content}
        
        REQUIREMENTS:
        - {instruction}
        - Break down complex concepts into understandable parts
        - Use clear, concise language
        - Highlight important concepts and relationships
        - Provide context and practical significance where relevant
        - Structure the explanation logically
        - INCLUDE RELEVANT REAL-LIFE EXAMPLES for each major concept
        - Examples should be practical, relatable, and help understand the concept
        - For technical concepts, provide industry applications
        - For abstract concepts, provide everyday analogies
        
        RESPONSE FORMAT (JSON):
        {{
            "explanation_title": "Explanation of Presentation Content",
            "summary": "Brief overall summary of the content",
            "key_concepts": [
                {{
                    "concept": "Concept Name",
                    "explanation": "Clear explanation of the concept",
                    "importance": "Why this concept matters",
                    "real_life_examples": [
                        {{
                            "example": "Specific real-life example",
                            "explanation": "How this example illustrates the concept"
                        }}
                    ]
                }}
            ],
            "detailed_explanation": "Comprehensive explanation covering all main points with examples",
            "real_world_applications": [
                "Application 1 in industry/business",
                "Application 2 in daily life", 
                "Application 3 in technology/science"
            ],
            "practical_tips": [
                "How to apply this knowledge practically",
                "Tips for implementation", 
                "Common use cases"
            ],
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
        Generate explanations for each slide individually with real-life examples
        """
        try:
            from ppt import get_slide_content
            
            slide_explanations = []
            
            for slide_num in slide_numbers:
                try:
                    slide_content = get_slide_content(ppt_file_path, slide_num - 1)
                    content = slide_content.get('content', '')
                    
                    if content.strip():
                        # Generate explanation for this specific slide with real-life examples
                        # In generate_slide_by_slide_explanation method, update the prompt:
                        prompt = f"""
                        Explain the content of this single presentation slide with REAL-LIFE EXAMPLES:

                        SLIDE {slide_num} CONTENT:
                        {content}

                        Provide a clear explanation of what this slide is about, 
                        the key messages it conveys, and any important details.
                        INCLUDE RELEVANT REAL-LIFE EXAMPLES that help understand the concepts.

                        Return JSON format:
                        {{
                            "slide_number": {slide_num},
                            "slide_title": "Brief title of the slide",
                            "main_topic": "Main topic covered",
                            "explanation": "Detailed explanation of the slide content",
                            "real_life_examples": [
                                {{
                                    "example": "Specific real-world example",
                                    "explanation": "How this example relates to the concept"
                                }}
                            ],
                            "practical_applications": [
                                "Practical application 1",
                                "Practical application 2"
                            ],
                            "key_points": ["Point 1", "Point 2", "Point 3"]
                        }}
                        """
                        
                        response = self.client.chat.completions.create(
                            model=self.model,
                            messages=[
                                {
                                    "role": "system",
                                    "content": "You are an expert presentation analyst. Provide clear explanations for individual slides with practical, real-life examples."
                                },
                                {
                                    "role": "user", 
                                    "content": prompt
                                }
                            ],
                            temperature=0.7,
                            max_tokens=1500,  # Increased for examples
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
                            "real_life_examples": [],
                            "practical_applications": [],
                            "key_points": []
                        })
                        
                except Exception as e:
                    slide_explanations.append({
                        "slide_number": slide_num,
                        "slide_title": "Error Processing Slide",
                        "main_topic": "Processing Error",
                        "explanation": f"Could not generate explanation for this slide: {str(e)}",
                        "real_life_examples": [],
                        "practical_applications": [],
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