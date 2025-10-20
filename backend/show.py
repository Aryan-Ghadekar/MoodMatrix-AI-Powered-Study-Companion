import os
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
import io
import base64
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import tempfile
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_ppt_to_images(ppt_path, output_dir):
    """
    Convert PowerPoint slides to images using python-pptx and PIL
    """
    try:
        prs = Presentation(ppt_path)
        os.makedirs(output_dir, exist_ok=True)
        
        image_paths = []
        
        for i, slide in enumerate(prs.slides):
            # Create a visual representation of the slide
            img = create_slide_image(slide, i)
            output_path = os.path.join(output_dir, f"slide_{i+1}.png")
            img.save(output_path, "PNG", quality=95)
            image_paths.append(output_path)
            logger.info(f"Generated image for slide {i+1}: {output_path}")
        
        return image_paths
        
    except Exception as e:
        logger.error(f"Error converting PPT to images: {e}")
        raise Exception(f"PPT to image conversion failed: {str(e)}")

def create_slide_image(slide, slide_index):
    """
    Create a visual representation of a slide using PIL
    """
    try:
        # Create a larger image for better quality (16:9 aspect ratio)
        width, height = 1200, 675
        
        # Use a professional background color
        bg_color = '#1e293b'  # Dark blue-gray
        
        img = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(img)
        
        # Add slide border
        border_color = '#334155'
        draw.rectangle([5, 5, width-5, height-5], outline=border_color, width=2)
        
        # Add header with slide number
        header_color = '#4361ee'
        draw.rectangle([0, 0, width, 60], fill=header_color)
        
        # Try to use a font, fallback to default if not available
        try:
            title_font = ImageFont.truetype("arial.ttf", 24)
            content_font = ImageFont.truetype("arial.ttf", 16)
        except:
            title_font = ImageFont.load_default()
            content_font = ImageFont.load_default()
        
        # Add slide number and title
        draw.text((width//2, 30), f"Slide {slide_index + 1}", fill='white', 
                 font=title_font, anchor='mm')
        
        # Extract and display text content
        slide_text = []
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                clean_text = ' '.join(shape.text.strip().split())
                if clean_text and clean_text not in slide_text:
                    slide_text.append(clean_text)
        
        # Display text content
        y_position = 80
        max_lines = 10
        line_height = 25
        
        for i, text in enumerate(slide_text[:max_lines]):
            if y_position < height - 50:
                # Wrap long text
                words = text.split()
                lines = []
                current_line = []
                
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    # Simple line length check
                    if len(test_line) < 80:
                        current_line.append(word)
                    else:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                
                if current_line:
                    lines.append(' '.join(current_line))
                
                # Display wrapped lines
                for line in lines[:3]:  # Max 3 lines per text block
                    if y_position < height - 50:
                        draw.text((30, y_position), f"• {line}", fill='#e2e8f0', 
                                 font=content_font)
                        y_position += line_height
        
        # If there are more lines, indicate with ellipsis
        if len(slide_text) > max_lines:
            draw.text((30, y_position), "• ...", fill='#94a3b8', font=content_font)
        
        # Add footer
        footer_text = "SlideSense - PPT to Quiz Generator"
        draw.text((width//2, height-20), footer_text, fill='#64748b', 
                 font=content_font, anchor='mm')
        
        return img
        
    except Exception as e:
        logger.error(f"Error creating slide image: {e}")
        # Return a basic placeholder if something goes wrong
        return create_placeholder_image(slide_index)

def create_placeholder_image(slide_index):
    """
    Create a placeholder image when slide generation fails
    """
    width, height = 1200, 675
    img = Image.new('RGB', (width, height), '#1e293b')
    draw = ImageDraw.Draw(img)
    
    # Add border
    draw.rectangle([5, 5, width-5, height-5], outline='#334155', width=2)
    
    # Add header
    draw.rectangle([0, 0, width, 60], fill='#4361ee')
    
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    # Add slide number
    draw.text((width//2, 30), f"Slide {slide_index + 1}", fill='white', 
             font=font, anchor='mm')
    
    # Add placeholder message
    draw.text((width//2, height//2 - 20), "Slide Preview", fill='#94a3b8', 
             font=font, anchor='mm')
    draw.text((width//2, height//2 + 20), "Content will be displayed here", 
             fill='#64748b', font=font, anchor='mm')
    
    return img

def get_slide_image_base64(image_path):
    """
    Convert image to base64 for web display
    """
    try:
        if os.path.exists(image_path):
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode('utf-8')
        else:
            return create_placeholder_base64()
    except Exception as e:
        logger.error(f"Error converting image to base64: {e}")
        return create_placeholder_base64()

def create_placeholder_base64():
    """
    Create a placeholder image as base64
    """
    img = Image.new('RGB', (800, 450), '#1e293b')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    # Add placeholder text
    draw.text((400, 200), "Slide Image\nNot Available", fill='#94a3b8', 
             anchor='mm', font=font)
    draw.text((400, 250), "Preview will be shown here", fill='#64748b', 
             anchor='mm', font=font)
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def ensure_slide_images(presentation_data, ppt_file_path):
    """
    Ensure that slide images are generated for a presentation
    """
    try:
        # Create images directory for this presentation
        pres_name = Path(ppt_file_path).stem
        images_dir = f"static/images/{pres_name}"
        os.makedirs(images_dir, exist_ok=True)
        
        logger.info(f"Images directory: {images_dir}")
        logger.info(f"Total slides: {presentation_data['total_slides']}")
        
        # Check if images already exist
        existing_images = [f for f in os.listdir(images_dir) if f.startswith("slide_") and f.endswith(".png")]
        logger.info(f"Existing images: {existing_images}")
        
        if len(existing_images) < presentation_data["total_slides"]:
            # Generate missing images
            logger.info(f"Generating images for {pres_name}...")
            try:
                image_paths = convert_ppt_to_images(ppt_file_path, images_dir)
                logger.info(f"Generated {len(image_paths)} images")
                
                # Update presentation data with image paths
                for i, slide_data in enumerate(presentation_data["slides"]):
                    slide_num = i + 1
                    image_path = os.path.join(images_dir, f"slide_{slide_num}.png")
                    slide_data["image_path"] = image_path
                    slide_data["image_url"] = f"/static/images/{pres_name}/slide_{slide_num}.png"
                    logger.info(f"Set image_url for slide {slide_num}: {slide_data['image_url']}")
                    
            except Exception as e:
                logger.error(f"Error generating images: {e}")
                # If image generation fails, set placeholder URLs
                for i, slide_data in enumerate(presentation_data["slides"]):
                    slide_num = i + 1
                    slide_data["image_url"] = f"/slide-image/{Path(ppt_file_path).name}/{i}"
        else:
            # Use existing images
            logger.info(f"Using existing images for {pres_name}")
            for i, slide_data in enumerate(presentation_data["slides"]):
                slide_num = i + 1
                image_path = os.path.join(images_dir, f"slide_{slide_num}.png")
                slide_data["image_path"] = image_path
                slide_data["image_url"] = f"/static/images/{pres_name}/slide_{slide_num}.png"
                logger.info(f"Using existing image_url for slide {slide_num}: {slide_data['image_url']}")
        
        return presentation_data
        
    except Exception as e:
        logger.error(f"Error ensuring slide images: {e}")
        # Return original data if image generation fails, but set placeholder URLs
        for i, slide_data in enumerate(presentation_data["slides"]):
            slide_data["image_url"] = f"/slide-image/{Path(ppt_file_path).name}/{i}"
        return presentation_data