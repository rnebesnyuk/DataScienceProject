import re
import string
import easyocr
import cv2 
import numpy as np
from matplotlib import pyplot as plt



# Mapping dictionaries for character conversion
dict_char_to_int = {'O': '0',
                    'I': '1',
                    'J': '3',
                    'A': '4',
                    'G': '6',
                    'S': '5',
                    'Q': 'O',
                    'U': 'O',
                    '|': 'I', 
                    '/': 'I',
                    ':': '-',
                    '.': '-',
                    '!':'1'}

dict_int_to_char = {'1': 'I',
                    '0': 'O',
                    '5': 'S',
                    '4': 'A',
                    '|': 'I',
                    ']': 'I',
                    '/': 'I',
                    "'": 'I',
                    'Q': 'O',
                    'U': 'O',
                    ':': '-',
                    '.': '-',
                    '[': 'C',
                    '₽': 'P',
                    'L': 'I',
                    '!':'I'}

def get_car(license_plate, vehicle_track_ids):
    x1, y1, x2, y2, score, class_id = license_plate

    foundIt = False
    for j in range(len(vehicle_track_ids)):
        xcar1, ycar1, xcar2, ycar2, car_id = vehicle_track_ids[j]

        if x1 > xcar1 and y1 > ycar1 and x2 < xcar2 and y2 < ycar2:
            car_indx = j
            foundIt = True
            break

    if foundIt:
        return vehicle_track_ids[car_indx]

    return -1, -1, -1, -1, -1


def sequence_format(text, aspect_ratio):
    # Remove spaces

    letters_first = []
    digits = []
    letters_last = []

    if aspect_ratio == "rectangular":
        letters = []
        digits = []

        for char in text:
            if char.isalpha():
                letters.append(char)
            elif char.isdigit():
                digits.append(char)
        return ''.join(letters[:2]) + ''.join(digits) + ''.join(letters[2:])

    elif aspect_ratio == "square":
        # Logic for square plate: Rearrange characters to fit 2 letters + 4 digits + 2 letters
        letters = text[:4]
        digits = text[4:]

        # Rearrange to fit the 2 letters + 4 digits + 2 letters rule
        if len(letters) >= 4 and len(digits) >= 4:
            # Take the first 2 letters, then 4 digits, then the next 2 letters
            letters_first = letters[:2]
            letters_last = letters[2:]
            digits = digits[:]
            
            return ''.join(letters_first) + ''.join(digits) + ''.join(letters_last)

    # Return the original text if it doesn't match any known pattern
    return text


def format_license(text):

    text_ = ''
    mapping = {0: dict_int_to_char, 1: dict_int_to_char,  6: dict_int_to_char, 7: dict_int_to_char,
                2: dict_char_to_int, 3: dict_char_to_int, 4: dict_char_to_int, 5: dict_char_to_int}

    for j in range(len(text[:8])):
        if text[j] in mapping[j].keys():
            text_ += mapping[j][text[j]]
        else:
            text_ += text[j]
    return text_


def simple_format(text):
    if '|' in text:
        text = text.replace('|', 'I')
    return text


def read_license_plate(license_plate_crop):

    reader = easyocr.Reader(['en', 'uk'], gpu=False)

    detections = reader.readtext(license_plate_crop)
    print(detections)

    filtered_texts = []

    image_height, image_width = license_plate_crop.shape

    image_with_boxes = license_plate_crop.copy()

    for detection in detections:
        bbox, text, score = detection
        text = text.upper().replace(' ', '')

        if text.startswith('UA') or text.startswith('WA') or text.startswith('VA') and len(filtered_texts)==0:
                continue
        if len(detections)<2:
            return simple_format(text), score
        if len(filtered_texts)==0 and 2<len(text)<4:
            text = text[-2:]

        x1, y1 = bbox[0]
        x2, y2 = bbox[2]
        t = format_license(text)
        filtered_texts.append(t)
        cv2.rectangle(image_with_boxes, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)


    concatenated_text = ''.join(filtered_texts)

    if concatenated_text.startswith('UA'):
        concatenated_text = concatenated_text[2:].strip()  # Remove 'UA' and any leading spaces
    elif concatenated_text.startswith('U'):
        concatenated_text = concatenated_text[1:].strip()  # Remove 'U' and any leading spaces
    elif concatenated_text.startswith('L'):
        concatenated_text = concatenated_text[1:].strip()  # Remove 'L' and any leading spaces
    elif concatenated_text.startswith('('):
        concatenated_text = concatenated_text[1:].strip()  # Remove 'L' and any leading spaces
    print(concatenated_text)
    middle = format_license(concatenated_text)
    print(middle)
    aspect_ratio = image_width / image_height
    
    # Classify based on aspect ratio
    if aspect_ratio < 1.95:  # Arbitrary threshold for rectangular vs square (can adjust)
        plate_shape = "square"
    else:
        plate_shape = "rectangular"

    print(f"Aspect Ratio: {aspect_ratio}, Plate Shape: {plate_shape}")

    temp = sequence_format(concatenated_text, plate_shape)
    # plt.figure(figsize=(10, 6))
    # plt.imshow(cv2.cvtColor(image_with_boxes, cv2.COLOR_BGR2RGB))
    # plt.title("Accepted License Plate Regions")
    # plt.axis("off")
    # plt.show()
    pattern = re.compile(r'.{2}.{4}.{2}')

    matching_detection = None
    
    match = pattern.search(concatenated_text)  # Search for the pattern within the text
    if match:
        matching_detection = match.group()
        temp = sequence_format(matching_detection, plate_shape)
        return format_license(temp), score
    if concatenated_text:
        return concatenated_text, score
    
    return None, None
    

def write_csv(results, output_path):

    with open(output_path, 'w', encoding='utf-16') as f:
        f.write('{},{},{},{},{},{},{}\n'.format('frame_nmr', 'car_id', 'car_bbox',
                                                'license_plate_bbox', 'license_plate_bbox_score', 'license_number',
                                                'license_number_score'))

        for frame_nmr in results.keys():
            for car_id in results[frame_nmr].keys():
                #print(results[frame_nmr][car_id])
                if 'car' in results[frame_nmr][car_id].keys() and \
                    'license_plate' in results[frame_nmr][car_id].keys() and \
                    'text' in results[frame_nmr][car_id]['license_plate'].keys():
                    f.write('{},{},{},{},{},{},{}\n'.format(frame_nmr,
                                                            car_id,
                                                            '[{} {} {} {}]'.format(
                                                                results[frame_nmr][car_id]['car']['bbox'][0],
                                                                results[frame_nmr][car_id]['car']['bbox'][1],
                                                                results[frame_nmr][car_id]['car']['bbox'][2],
                                                                results[frame_nmr][car_id]['car']['bbox'][3]),
                                                            '[{} {} {} {}]'.format(
                                                                results[frame_nmr][car_id]['license_plate']['bbox'][0],
                                                                results[frame_nmr][car_id]['license_plate']['bbox'][1],
                                                                results[frame_nmr][car_id]['license_plate']['bbox'][2],
                                                                results[frame_nmr][car_id]['license_plate']['bbox'][3]),
                                                            results[frame_nmr][car_id]['license_plate']['bbox_score'],
                                                            results[frame_nmr][car_id]['license_plate']['text'],
                                                            results[frame_nmr][car_id]['license_plate']['text_score'])
                            )
        f.close()