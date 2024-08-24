from src.services.cv_service.sort.sort import *
from .lic_rec import *
from src.services.cv_service.visualize_image import draw_bboxes_from_csv
from src.services.cv_service.util import write_csv


VIDEO_FORMATS = ('.mp4', '.avi', '.mov', '.mkv', '.flv')
IMAGE_FORMATS = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')

def is_video_file(file_path):
    return file_path.lower().endswith(VIDEO_FORMATS)

def is_image_file(file_path):
    return file_path.lower().endswith(IMAGE_FORMATS)

def main(input_source):
    if is_video_file(input_source):
        print(f"Detected {input_source} as a video file.")
        s_type = 'vid'
        results = process_video_or_image(input_source, vehicles, s_type)
        write_csv(results, './reads.csv')
    elif is_image_file(input_source):
        s_type = 'pic'
        print(f"Detected {input_source} as an image file.")
        results = process_video_or_image(input_source, vehicles, s_type)
        write_csv(results, './reads.csv')
        draw_bboxes_from_csv(input_source, 'reads.csv', 'reads_on_car.jpg')
    else:
        print(f"File format not recognized as video or image.")
    return results