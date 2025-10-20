import sys
import os
sys.path.append('.')

from show import convert_ppt_to_images, ensure_slide_images
from ppt import process_ppt_file

def test_image_generation():
    # Test with a sample PPT file
    ppt_path = "static/uploads/your_test_file.pptx"  # Replace with actual file path
    
    if not os.path.exists(ppt_path):
        print(f"Test file not found: {ppt_path}")
        return
    
    print("Testing image generation...")
    
    # Test process_ppt_file
    presentation_data = process_ppt_file(ppt_path)
    print(f"Processed {presentation_data['total_slides']} slides")
    
    # Test ensure_slide_images
    presentation_data = ensure_slide_images(presentation_data, ppt_path)
    
    # Check results
    for i, slide in enumerate(presentation_data["slides"]):
        print(f"Slide {i+1}:")
        print(f"  - image_url: {slide.get('image_url', 'NOT SET')}")
        print(f"  - image_path: {slide.get('image_path', 'NOT SET')}")
        if slide.get('image_path'):
            print(f"  - file exists: {os.path.exists(slide['image_path'])}")

if __name__ == "__main__":
    test_image_generation()