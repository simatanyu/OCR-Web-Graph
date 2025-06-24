import cv2
from PIL import Image
import pytesseract
import pandas as pd
import os
import time
from datetime import datetime
from itertools import count
import threading
import requests
import numpy as np
import traceback

SERVER_URL = "http://10.0.0.194:5000/upload_csv"

# Path to the folder containing images
folder_path = "/home/dirpi/third/TestLib"
output_file = "/home/dirpi/third-website/Extracted_Numbers.csv"

# Tesseract OCR Configuration
myconfig = r"--psm 10 --oem 3 -c tessedit_char_whitelist=0123456789."

# Global variables
processed_images = set()
results_array = []  # Array to store processed image results in memory

# Function to write results to CSV
def save_results_to_csv(output_file):
    global results_array
    if results_array:  # Only save if there's data
        data = pd.DataFrame(results_array)
        data = data[['Timestamp', 'Extracted Numbers']]
        data.columns = ['timestamp', 'value']
        data.to_csv(output_file, index=False)
        print(f"Results saved to {output_file}")

# Function to process images in the folder
def process_images(folder_path):
    global processed_images, results_array
    
    x, y, w, h =0, 120, 900, 260 #ROI region
    
    block_size = 97 #size of each element
    adaptive_c = 8 # connection size
    
    processed_images.clear() # Clear cache for test
    
    image_files = sorted(os.listdir(folder_path))
    for image_file in image_files:
        if image_file in processed_images:
            continue

        image_path = os.path.join(folder_path, image_file)
        if image_path.endswith((".png", ".jpg", ".jpeg")):
            image = cv2.imread(image_path)
            if image is None:
                continue

            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            roi = gray_image[y:y + h, x:x + w]
            
            im_bw = cv2.adaptiveThreshold(
                roi, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, #Reverse mode
                block_size,
                adaptive_c
            )
            im_bw = cv2.medianBlur(im_bw, 3)
            kernal = np.ones((1,3), np.uint8)
            im_bw = cv2.dilate(im_bw, kernal, iterations = 1)

            pil_image = Image.fromarray(im_bw)
            text = pytesseract.image_to_string(pil_image, config=myconfig)
            numbers = "".join([char for char in text if char.isdigit()])

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result = {
                "Timestamp": timestamp,
                "Image File": image_file,
                "Extracted Numbers": numbers
            }

            results_array.append(result)  # Store the result in memory
            processed_images.add(image_file)  # Mark as processed
            save_and_upload_data(numbers) # Upload after read
            print(f"Processed: {image_file}")

# Function to start processing images in a separate thread
def start_processing():
    max_checks = 2  # Check up to 10 times for new images
    check_count = 0
    last_save_time = time.time()  # Record the last save time

    while check_count < max_checks:
        process_images(folder_path)

        # Save results to CSV every 5 minutes
        if time.time() - last_save_time >= 10:  # 300 seconds = 5 minutes
            save_results_to_csv(output_file)
            last_save_time = time.time()

        # Exit if no new images are found
        if len(os.listdir(folder_path)) == 0:
            print("No new images detected. Exiting processing loop.")
            save_results_to_csv(output_file)  # Save final results
            break

        time.sleep(10)
        check_count += 1

def save_and_upload_data(value):
    """Save CSV and Upload"""
    timestamp = time.strftime("%H:%M:%S")

        # upload section for flask server
    data = {"timestamp": timestamp,"value": value}
    response = requests.post(SERVER_URL, json=data)
    print("Please return it:", response.json())

def start_processing_with_debug():
    try:
        start_processing()
    except Exception as e:
        print("thread error:", e)
        traceback.print_exc()
        
# Start image processing in a separate thread
processing_thread = threading.Thread(target=start_processing_with_debug, daemon = False)
processing_thread.start()
processing_thread.join()
