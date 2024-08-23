from ultralytics import YOLO
import cv2

from src.services.cv_service.sort.sort import *
from src.services.cv_service.util import get_car, read_license_plate



results = {}

# load models
coco_model = YOLO('yolov8n.pt') #for cars detection
license_plate_detector = YOLO('license_plate_detector.pt') #for license plates detection

vehicles = [2, 3, 5, 7]


# Function to process frame (for both video and image)
def process_frame(frame, frame_nmr, results, vehicles):

    results[frame_nmr] = {}
    # Detect vehicles
    detections = coco_model(frame)[0]
    detections_ = []
    for detection in detections.boxes.data.tolist():
        x1, y1, x2, y2, score, class_id = detection
        if int(class_id) in vehicles:  # Ensure vehicles is a list of class IDs for vehicles
            detections_.append([x1, y1, x2, y2, score])


    # Detect license plates
    license_plates = license_plate_detector(frame)[0]
    for license_plate in license_plates.boxes.data.tolist():
        x1, y1, x2, y2, score, class_id = license_plate

        # Assign license plate to car
        xcar1, ycar1, xcar2, ycar2, car_id = get_car(license_plate, detections_)

        if car_id != -1:
            # Crop license plate
            license_plate_crop = frame[int(y1):int(y2), int(x1): int(x2), :]

            # Process license plate
            license_plate_crop_ = cv2.cvtColor(license_plate_crop, cv2.COLOR_BGR2GRAY)

            # kernel = np.ones((1, 1), np.uint8)
            # license_plate_crop_ = cv2.dilate(license_plate_crop, kernel, iterations=1)  #license_plate_dilate
            # license_plate_crop_ = cv2.erode(license_plate_crop_gray, kernel, iterations=1)    #license_plate_erode 
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))

            # Apply CLAHE to the grayscale image
            enhanced_image = clahe.apply(license_plate_crop_)
            #license_plate_crop_ = cv2.adaptiveThreshold(license_plate_crop_, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            license_plate_crop__ = cv2.equalizeHist(enhanced_image)
            license_plate_crop___ = cv2.fastNlMeansDenoising(license_plate_crop__, None, 30, 7, 21)
            #_, license_plate_crop_ = cv2.threshold(license_plate_crop_gray, 64, 255, cv2.THRESH_BINARY)

            # Read license plate number
            license_plate_text, license_plate_text_score = read_license_plate(license_plate_crop___)
            print(license_plate_text)
            # cv2.imshow("Image", license_plate_crop_)
            # cv2.waitKey(0)

            if license_plate_text is not None:
                results[frame_nmr][car_id] = {
                    'car': {'bbox': [xcar1, ycar1, xcar2, ycar2]},
                    'license_plate': {
                        'bbox': [x1, y1, x2, y2],
                        'text': license_plate_text,
                        'bbox_score': score,
                        'text_score': license_plate_text_score
                    }
                }

# Main function to handle video or image
def process_video_or_image(input_source, vehicles, s_type):
    results = {}
    frame_nmr = -1
    
    if s_type=='vid':
        # Video processing
        vid = cv2.VideoCapture(input_source)
        ret = True
        while ret:
            frame_nmr += 1
            ret, frame = vid.read()
            if ret:
                process_frame(frame, 0, results, vehicles)
        vid.release()

    elif s_type=='pic':
        # Image processing
        # frame_nmr = 0
        frame = cv2.imread(input_source)
        if frame is None:
            raise ValueError("Failed to read image.")
        process_frame(frame, 0, results, vehicles)
    else:
        print("Could not read the file.")

    return results