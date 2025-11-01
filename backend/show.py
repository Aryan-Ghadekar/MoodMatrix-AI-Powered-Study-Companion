import os
import subprocess
import tempfile
from pathlib import Path
import logging
import io
import base64
from unittest import result
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_ppt_to_images(ppt_path, output_dir):
    try:
        os.makedirs(output_dir, exist_ok=True)
        ppt_path = os.path.abspath(ppt_path)
        
        pdf_path = os.path.join(output_dir, Path(ppt_path).stem + ".pdf")
        cmd = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            "--headless", "--convert-to", "pdf:impress_pdf_Export",
            "--outdir", output_dir, ppt_path
        ]
        logger.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        logger.info(f"LibreOffice stdout: {result.stdout}")
        logger.error(f"LibreOffice stderr: {result.stderr}")
        
        if result.returncode != 0:
            raise Exception(f"LibreOffice conversion failed: {result.stderr}")
        
        # Now convert the PDF pages to PNG
        images = convert_from_path(pdf_path, poppler_path=r"C:\poppler-25.07.0\Library\bin")
        image_paths = []
        for i, img in enumerate(images):
            img_path = os.path.join(output_dir, f"slide_{i+1}.png")
            img.save(img_path, "PNG")
            image_paths.append(img_path)
            logger.info(f"Generated image: {img_path}")
        
        return image_paths
    
    except Exception as e:
        logger.error(f"Error converting PPT to images: {e}")
        return generate_placeholder_images(output_dir, get_slide_count(ppt_path))
        
    except Exception as e:
        logger.error(f"Error converting PPT to images: {e}")
        # Fallback to placeholder
        return generate_placeholder_images(output_dir, get_slide_count(ppt_path))

def get_slide_count(ppt_path):
    """
    Get the number of slides in the presentation
    """
    try:
        from pptx import Presentation
        prs = Presentation(ppt_path)
        return len(prs.slides)
    except:
        return 10  # Default fallback

def generate_placeholder_images(output_dir, slide_count):
    """
    Generate placeholder images when conversion fails
    """
    image_paths = []
    for i in range(slide_count):
        output_path = os.path.join(output_dir, f"slide_{i+1}.png")
        img = create_placeholder_image(i)
        img.save(output_path, "PNG", quality=95)
        image_paths.append(output_path)
    return image_paths

def create_placeholder_image(slide_index):
    """
    Create a placeholder image
    """
    from PIL import Image, ImageDraw, ImageFont
    
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
    
    # Add message
    draw.text((width//2, height//2 - 20), "Actual Slide Preview", fill='#94a3b8', 
             font=font, anchor='mm')
    draw.text((width//2, height//2 + 20), "Install LibreOffice for better conversion", 
             fill='#64748b', font=font, anchor='mm')
    
    return img

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
    draw.text((400, 250), "Install LibreOffice for better conversion", 
             fill='#64748b', anchor='mm', font=font)
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')