import ast
import csv
import cv2
import numpy as np
import pandas as pd
from PIL import ImageFont, ImageDraw, Image

def draw_text_with_pil(image, text, license_number_score, position, font_path='arial.ttf', color=(0, 255, 0)):
    """
    Draw UTF-8 text on the image using PIL to handle non-ASCII characters.

    Args:
        image: OpenCV image.
        text (str): Text to draw.
        position (tuple): Position to draw the text (x, y).
        font_path (str): Path to the TTF font file.
        font_size (int): Font size for the text.
        color (tuple): Text color in BGR format.
    """
    # Convert the OpenCV image (BGR) to a PIL image (RGB)
    image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    
    # Load the font
    font = ImageFont.truetype(font_path, size=50)
    
    # Create a drawing context
    draw = ImageDraw.Draw(image_pil)

    text_to_draw = f'{text} ({license_number_score:.2f})'
    
    # Draw the text using PIL
    draw.text(position, text_to_draw, font=font, fill=color)
    
    # Convert back to OpenCV format (BGR)
    image = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
    
    return image



def draw_bboxes_from_csv(image_path, csv_path, output_path):
    """
    Draw bounding boxes and scores on the image from the CSV file.

    Args:
        image_path (str): Path to the original image.
        csv_path (str): Path to the CSV file containing bounding box data.
        output_path (str): Path to save the image with drawn bounding boxes.
    """
    # Read the image
    image = cv2.imread(image_path)

    # Open the CSV file and read bounding box data
    with open(csv_path, 'r', encoding='utf-16') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            # Parse car bounding box
            car_bbox_str = row['car_bbox'].strip('[]').split()
            car_bbox = [int(float(val)) for val in car_bbox_str]
            car_id = row['car_id']
            
            # Parse license plate bounding box
            lp_bbox_str = row['license_plate_bbox'].strip('[]').split()
            lp_bbox = [int(float(val)) for val in lp_bbox_str]
            license_number = row['license_number']
            license_number_score = float(row['license_number_score'])
            
            # Draw car bounding box
            cv2.rectangle(image, (car_bbox[0], car_bbox[1]), (car_bbox[2], car_bbox[3]), (255, 0, 0), 3)
            cv2.putText(image, f'Car ID: {car_id}', (car_bbox[0], car_bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 0), 2)
            
            # Draw license plate bounding box
            cv2.rectangle(image, (lp_bbox[0], lp_bbox[1]), (lp_bbox[2], lp_bbox[3]), (0, 255, 0), 3)
            image = draw_text_with_pil(image, license_number, license_number_score, (lp_bbox[0], lp_bbox[1] - 50))
            # cv2.putText(image, f'({license_number_score:.2f})', 
            #             (lp_bbox[0], lp_bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # Save the image with drawn bounding boxes
    cv2.imwrite(output_path, image)
    print(f"Output saved to {output_path}")

# Example usage
#draw_bboxes_from_csv('hir.jpg', 'test.csv', 'test_b.jpg')