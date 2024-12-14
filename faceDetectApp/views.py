from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from django.contrib import messages
import logging

import os
import cv2
import face_recognition
import numpy as np
import base64
from datetime import datetime, timedelta
from .models import User, Attendance

# Set up logging
logger = logging.getLogger(__name__)

# Directory for storing user images
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "../user_images")
os.makedirs(IMAGES_DIR, exist_ok=True)

# Load known face encodings
def load_face_encodings():
    known_encodings = []
    known_ids = []
    for filename in os.listdir(IMAGES_DIR):
        if filename.endswith(".jpg"):
            uid = os.path.splitext(filename)[0]
            image_path = os.path.join(IMAGES_DIR, filename)
            try:
                image = face_recognition.load_image_file(image_path)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    known_encodings.append(encodings[0])
                    known_ids.append(uid)
                else:
                    logger.warning(f"No face detected in {filename}")
            except Exception as e:
                logger.error(f"Error processing image {filename}: {e}")
    return known_encodings, known_ids

# Initialize known face encodings and IDs
KNOWN_FACE_ENCODINGS, KNOWN_FACE_IDS = load_face_encodings()

def index(request):
    """
    Render the main page for attendance tracking.
    """
    return render(request, 'index.html')

def info(request):
    """
    Handle user registration and save the captured image.
    """
    global KNOWN_FACE_ENCODINGS, KNOWN_FACE_IDS  # Make these variables modifiable

    if request.method == "POST":
        uid = request.POST.get("uid")
        name = request.POST.get("name")
        frame_data = request.POST.get("frame")

        # Decode the base64 image
        try:
            frame_data = frame_data.split(",")[1]
            frame_bytes = base64.b64decode(frame_data)
            image_path = os.path.join(IMAGES_DIR, f"{uid}.jpg")
            with open(image_path, "wb") as image_file:
                image_file.write(frame_bytes)
        except Exception as e:
            return render(request, 'register.html', {"error": f"Error processing image: {e}"})

        # Save user details in the database
        User.objects.create(uid=uid, name=name)
        messages.success(request, f"User {name} registered successfully!")

        # Encode the new user's face and update global variables
        try:
            image = face_recognition.load_image_file(image_path)
            encoding = face_recognition.face_encodings(image)
            if encoding:
                KNOWN_FACE_ENCODINGS.append(encoding[0])
                KNOWN_FACE_IDS.append(uid)
                logger.info(f"New user {name} (ID: {uid}) added successfully.")
                logger.info(f"Updated Encodings: {len(KNOWN_FACE_ENCODINGS)} users known.")
            else:
                logger.warning(f"No face detected in the uploaded image for user {name}.")
                messages.error(request, f"No face detected in the uploaded image for user {name}.")
        except Exception as e:
            logger.error(f"Error encoding the new user's face: {e}")
            messages.error(request, f"Error processing the image for {name}: {e}")

        return redirect("index")

    return render(request, 'register.html')

@csrf_exempt
def process_frame(request):
    if request.method == "POST":
        try:
            # Decode incoming data
            frame_data = request.body.decode('utf-8')
            if not frame_data:
                return JsonResponse({"success": False, "message": "No frame data provided."})

            # Decode Base64 frame
            frame_data = frame_data.split(",")[1]
            frame_bytes = base64.b64decode(frame_data)
            np_array = np.frombuffer(frame_bytes, dtype=np.uint8)
            frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

            if frame is None:
                return JsonResponse({"success": False, "message": "Failed to decode frame data."})

            # Process frame
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)

            if not face_locations:
                return JsonResponse({"success": False, "message": "No face detected."})

            # Encode faces and compare
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            for encoding in face_encodings:
                face_distances = face_recognition.face_distance(KNOWN_FACE_ENCODINGS, encoding)
                best_match_index = np.argmin(face_distances)

                logger.info(f"Processing face encodings for UID: {KNOWN_FACE_IDS[best_match_index]}")
                logger.info(f"Distances: {face_distances}")
                logger.info(f"Best match index: {best_match_index}, Distance: {face_distances[best_match_index]}")

                if face_distances[best_match_index] < 0.4:  # Adjust threshold
                    uid = KNOWN_FACE_IDS[best_match_index]
                    try:
                        user = User.objects.get(uid=uid)
                    except User.DoesNotExist:
                        return JsonResponse({"success": False, "message": "User not found in the database. Please register."})

                    # Check if user is already IN
                    attendance = Attendance.objects.filter(uid=uid, out_time=None).last()
                    if attendance:
                        # Check the time difference
                        time_difference = now() - attendance.in_time
                        if time_difference < timedelta(seconds=30):
                            return JsonResponse({
                                "success": False,
                                "message": f"{user.name}, please wait before logging OUT."
                            })
                        attendance.out_time = now()
                        attendance.save()
                        return JsonResponse({"success": True, "message": f"{user.name}, You are OUT."})
                    else:
                        # Log IN if no active record
                        Attendance.objects.create(uid=uid, name=user.name, in_time=now())
                        return JsonResponse({"success": True, "message": f"{user.name}, You are IN."})

            return JsonResponse({"success": False, "message": "Face not recognized. Please register."})
        except Exception as e:
            # Log the exception for debugging
            logger.error(f"Error in process_frame: {e}")
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "message": "Invalid request method."})

def face_recognition_view(request):
    """
    Render the face recognition page.
    """
    return render(request, 'face_recognition.html')

def attendance(request):
    """
    Render the attendance page.
    """
    logs = Attendance.objects.all()
    return render(request, 'attendance.html', {"logs": logs})