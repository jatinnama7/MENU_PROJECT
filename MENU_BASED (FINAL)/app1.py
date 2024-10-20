from flask import Flask, request, jsonify, render_template,send_file
from twilio.rest import Client
import mediapipe as mp
import pyautogui
import random
import time 
from googlesearch import search
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from geopy.geocoders import Nominatim
from googletrans import Translator
from gtts import gTTS
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import pythoncom
import cv2
import cvzone
from cvzone.HandTrackingModule import HandDetector
import numpy as np
import base64
from flask_cors import CORS
import os
import threading
from io import BytesIO
import pygame
import subprocess
import google.generativeai as genai
from dotenv import load_dotenv


load_dotenv()
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')  

@app.route('/port')
def port():
    return render_template('project.html')


@app.route('/send-whatsapp-message', methods=['POST'])
def send_whatsapp_message():
    data = request.json
    what_message = data.get('text_message')
    phone_number = data.get('phone_number')
    
    if not what_message:
        return jsonify({'status': 'error', 'message': 'Message body is required.'}), 400
    
    try:
        # Twilio credentials
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')   
        client = Client(account_sid, auth_token)
        
        # Sending WhatsApp message
        client.messages.create(
            body=what_message,
            from_= os.getenv('TWILIO_WHATSAPP_FROM'),
            to=f'whatsapp:+91{phone_number}'  # Add appropriate country code
        )
        
        return jsonify({'status': 'success', 'message': 'WhatsApp message sent successfully!'})
    
    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to send WhatsApp message.'}), 500


@app.route('/send-text-message', methods=['POST'])
def send_text_message():
    data = request.json
    text_message = data.get('text_message')
    phone_number = data.get('phone_number')
    # acc_sid=os.getenv('TWILIO_ACCOUNT_SID')
    # acc_pass = os.getenv('TWILIO_AUTH_TOKEN') 
    try:
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token =  os.getenv("TWILIO_AUTH_TOKEN")
        client = Client(account_sid, auth_token)
        client.messages.create(
            body=text_message,
            from_=os.getenv('TWILIO_SMS_FROM'),          
            to= phone_number          
        )
        return jsonify({'status': 'success', 'message': 'Text message sent successfully!'})
    except Exception as e:
        print(f"Error sending text message: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to send text message.'}), 500

@app.route('/send-email', methods=['POST'])
def send_email():
    data = request.json
    email = data.get('email')
    subject = data.get('subject')
    content = data.get('content')
    try:
        sender_email = os.getenv('SENDER_EMAIL')
        sender_password = os.getenv('SENDER_PASSWORD')      
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(content, 'plain'))
        server.sendmail(sender_email, email, msg.as_string())
        server.quit()
        return jsonify({'status': 'success', 'message': 'Email sent successfully!'})
    except Exception as e:
        print(f"Error sending email: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to send email.'}), 500

@app.route('/send-bulk-email', methods=['POST'])
def send_bulk_email():
    try:
        subject = request.form['subject']
        body = request.form['body']
        recipients = request.form.getlist('recipients[]')
        attachments = request.files.getlist('attachments')

        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_user = os.getenv('SENDER_EMAIL')
        smtp_password = os.getenv('SENDER_PASSWORD')

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)

        for recipient in recipients:
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = recipient.strip()
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))

            for attachment in attachments:
                part = MIMEApplication(attachment.read(), Name=attachment.filename)
                part['Content-Disposition'] = f'attachment; filename="{attachment.filename}"'
                msg.attach(part)

            server.send_message(msg)

        server.quit()
        return jsonify({'status': 'success', 'message': 'Bulk emails sent successfully.'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to send bulk emails: {str(e)}'})

@app.route('/google-search', methods=['POST'])
def google_search():
    query = request.json['query']
    try:
        results = list(search(query,num_results=5))
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to perform Google search: {str(e)}'})
    

@app.route('/control_volume', methods=['POST'])
def control_volume():
    try:
        # Initialize COM for the current thread
        pythoncom.CoInitialize()

        data = request.json
        command = data.get('action')  # Changed to 'action' to match AJAX
        vol = data.get('volume', 0.5)  # Default volume is 50%

        # Log or print for debugging
        print(f"Command received: {command}")
        print(f"Volume received: {vol}")

        # Get the audio device
        devices = AudioUtilities.GetSpeakers()
        if devices is None:
            return jsonify({'message': 'Audio device not found.', 'status': 'error'}), 500

        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        if volume is None:
            return jsonify({'message': 'Unable to access audio volume interface.', 'status': 'error'}), 500

        # Process the commands
        if command == 'set_volume':
            if 0.0 <= vol <= 1.0:
                print(f"Setting volume to {vol * 100:.0f}%")
                volume.SetMasterVolumeLevelScalar(vol, None)  # Set volume
                current_vol = volume.GetMasterVolumeLevelScalar()  # Get the current volume for validation
                print(f"Current system volume: {current_vol * 100:.0f}%")
                return jsonify({'message': f"Volume set to {current_vol * 100:.0f}%", 'status': 'success'})
            else:
                return jsonify({'message': "Invalid volume value. Please enter a value between 0.0 and 1.0.", 'status': 'error'}), 400

        elif command == 'mute':
            volume.SetMute(True, None)
            return jsonify({'message': "Audio muted.", 'status': 'success'})

        elif command == 'unmute':
            volume.SetMute(False, None)
            return jsonify({'message': "Audio unmuted.", 'status': 'success'})

        else:
            return jsonify({'message': "Invalid command.", 'status': 'error'}), 400

    except Exception as e:
        return jsonify({'message': f"An error occurred: {str(e)}", 'status': 'error'}), 500


@app.route('/get-location', methods=['POST'])
def get_location():
    try:
        location_name = request.json.get('location')
        loc = Nominatim(user_agent="GetLoc")
        getLoc = loc.geocode(location_name)

        if getLoc:
            return jsonify({
                'address': getLoc.address,
                'latitude': getLoc.latitude,
                'longitude': getLoc.longitude,
                'status': 'success'
            })
        else:
            return jsonify({'message': 'Location not found.', 'status': 'error'}), 400

    except Exception as e:
        return jsonify({'message': f"An error occurred: {str(e)}", 'status': 'error'}), 500


@app.route('/translate-and-speak', methods=['POST'])
def translate_and_speak():
    try:
        data = request.json
        lang1 = data.get('src_lang', 'en').strip().lower()
        text = data.get('text', '').strip()
        lang2 = data.get('dest_lang', 'en').strip().lower()

        if not text:
            return jsonify({'message': 'Text is required for translation.', 'status': 'error'}), 400

        translator = Translator()
        translation = translator.translate(text, src=lang1, dest=lang2)

        audio = gTTS(text=translation.text, lang=lang2)
        audio_file = "static/Msg.mp3"
        audio.save(audio_file)

        return jsonify({
            'original_text': text,
            'translated_text': translation.text,
            'audio_url': f'/{audio_file}',
            'status': 'success'
        })

    except Exception as e:
        return jsonify({'message': f"An error occurred: {str(e)}", 'status': 'error'}), 500
    


@app.route('/capture-image', methods=['POST'])
def capture_image():
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return 'Error: Could not open video capture.', 500

    ret, frame = cap.read()
    cv2.waitKey(3000)
    cap.release()
    
    if not ret:
        return 'Error: Failed to grab frame.', 500
    
    # Detect and crop face
    result_image = detect_and_crop_face(frame)
    
    # Save the result image
    output_path = 'output_image.jpg'
    cv2.imwrite(output_path, result_image)
    
    return send_file(output_path, mimetype='image/jpeg')

def detect_and_crop_face(image):
    # Load OpenCV's pre-trained Haar Cascade model for face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    if len(faces) == 0:
        print("No face detected.")
        return image

    for (x, y, w, h) in faces:
        cropped_face = image[y:y+h, x:x+w]
        resized_face = cv2.resize(cropped_face, (100, 100))
        image[y:y+100, x:x+100] = resized_face

    return image

def encode_image(image):
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8')

@app.route('/apply-filters', methods=['POST'])
def apply_filters():
    # Capture image from webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return jsonify({'error': 'Could not open video capture.'}), 500

    ret, frame = cap.read()
    cv2.waitKey(3000)
    cap.release()
    
    if not ret:
        return jsonify({'error': 'Failed to grab frame.'}), 500

    # Apply filters
    images = []
    
    # 1. Original Image
    images.append(encode_image(frame))
    
    # 2. Apply Gaussian Blur
    gaussian_blur = cv2.GaussianBlur(frame, (15, 15), 0)
    images.append(encode_image(gaussian_blur))
    
    # 3. Apply Median Blur
    median_blur = cv2.medianBlur(frame, 15)
    images.append(encode_image(median_blur))
    
    # 4. Apply Bilateral Filter
    bilateral_filter = cv2.bilateralFilter(frame, 15, 75, 75)
    images.append(encode_image(bilateral_filter))
    
    # 5. Apply Edge Detection (Canny)
    edges = cv2.Canny(frame, 100, 200)
    images.append(encode_image(edges))
    
    # 6. Apply Sharpening Filter
    kernel = np.array([[0, -1, 0],
                       [-1, 5, -1],
                       [0, -1, 0]])
    sharpened = cv2.filter2D(frame, -1, kernel)
    images.append(encode_image(sharpened))
    
    # 7. Apply Emboss Filter
    kernel_emboss = np.array([[-2, -1, 0],
                              [-1, 1, 1],
                              [0, 1, 2]])
    embossed = cv2.filter2D(frame, -1, kernel_emboss)
    images.append(encode_image(embossed))
    
    return jsonify({'images': images})


def create_random_color():
    """Generate a random color in BGR format"""
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

def create_custom_image():
    # Create a blank image with 3 channels (RGB) and a white background
    image = np.ones((500, 500, 3), dtype=np.uint8) * 255  # 500x500 pixels with a white background

    # Draw random shapes with random properties
    # Random red rectangle
    top_left = (random.randint(0, 400), random.randint(0, 400))
    bottom_right = (top_left[0] + random.randint(50, 150), top_left[1] + random.randint(50, 150))
    cv2.rectangle(image, top_left, bottom_right, create_random_color(), -1)

    # Random green circle
    center = (random.randint(50, 450), random.randint(50, 450))
    radius = random.randint(20, 100)
    cv2.circle(image, center, radius, create_random_color(), -1)

    # Random blue line
    start_point = (random.randint(0, 500), random.randint(0, 500))
    end_point = (random.randint(0, 500), random.randint(0, 500))
    thickness = random.randint(1, 10)
    cv2.line(image, start_point, end_point, create_random_color(), thickness)

    # Random yellow ellipse
    ellipse_center = (random.randint(50, 450), random.randint(50, 450))
    axes = (random.randint(30, 100), random.randint(20, 80))
    angle = random.randint(0, 360)
    cv2.ellipse(image, ellipse_center, axes, angle, 0, 360, create_random_color(), -1)

    # Add random text with varying position and size
    font_scale = random.uniform(0.5, 2.0)
    text_position = (random.randint(50, 300), random.randint(50, 450))
    cv2.putText(image, 'Random Image', text_position, cv2.FONT_HERSHEY_SIMPLEX, font_scale, create_random_color(), 2, cv2.LINE_AA)

    # Convert image to byte array for sending
    _, buffer = cv2.imencode('.jpg', image)
    return BytesIO(buffer)

@app.route('/create-custom-image', methods=['POST'])
def create_custom_image_endpoint():
    image_bytes = create_custom_image()
    return send_file(image_bytes, mimetype='image/jpeg')



# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True)

# Load filter images (ensure transparent backgrounds)
sunglasses = cv2.imread('sunglass.png', cv2.IMREAD_UNCHANGED)
star = cv2.imread('stars.png', cv2.IMREAD_UNCHANGED)

def encode_image(image):
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8')

@app.route('/apply-face-filter', methods=['POST'])
def apply_face_filter():
    # Capture image from webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return jsonify({'error': 'Could not open video capture.'}), 500

    ret, frame = cap.read()
    cv2.waitKey(2000)
    cap.release()
    
    if not ret:
        return jsonify({'error': 'Failed to grab frame.'}), 500

    # Convert the frame to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detect facial landmarks
    results = face_mesh.process(rgb_frame)
    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0].landmark
        frame = apply_filters(frame, landmarks)

    # Encode and return the final image with face filters
    encoded_image = encode_image(frame)
    return jsonify({'image': encoded_image})

def overlay_filter(image, filter_img, position, size):
    filter_img = cv2.resize(filter_img, size)
    alpha_s = filter_img[:, :, 3] / 255.0
    alpha_l = 1.0 - alpha_s
    x, y = position

    for c in range(0, 3):
        image[y:y + filter_img.shape[0], x:x + filter_img.shape[1], c] = (
            alpha_s * filter_img[:, :, c] + alpha_l * image[y:y + filter_img.shape[0], x:x + filter_img.shape[1], c]
        )

    return image

def apply_filters(image, landmarks):
    h, w, _ = image.shape
    left_eye = landmarks[33]
    right_eye = landmarks[263]

    sunglasses_width = int(abs(right_eye.x - left_eye.x) * w * 2)
    sunglasses_height = int(sunglasses_width * 0.4)
    x = int(left_eye.x * w) - sunglasses_width // 4
    y = int(left_eye.y * h) - sunglasses_height // 2
    image = overlay_filter(image, sunglasses, (x, y), (sunglasses_width, sunglasses_height))

    forehead = landmarks[10]
    star_size = 50
    x = int(forehead.x * w) - star_size // 2
    y = int(forehead.y * h) - star_size - 30
    image = overlay_filter(image, star, (x, y), (star_size, star_size))

    return image

#Fingerspell animation

CORS(app)

asl_shapes = {
    'a': '👊', 'b': '✋', 'c': '🤏', 'd': '👆', 'e': '🤞', 'f': '👌',
    'g': '🤜', 'h': '🖖', 'i': '🤙', 'j': '🤚', 'k': '🤞', 'l': '👍',
    'm': '🤟', 'n': '🤘', 'o': '👌', 'p': '👇', 'q': '👉', 'r': '🤞',
    's': '✊', 't': '👍', 'u': '🤟', 'v': '✌', 'w': '👐', 'x': '🤞',
    'y': '🤙', 'z': '👈'
}

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def fingerspell_animation(text, results):
    animation_result = []
    for letter in text.lower():
        clear_console()
        if letter in asl_shapes:
            animation_result.append(f"Letter: {letter.upper()} - ASL Shape: {asl_shapes[letter]}")
        else:
            animation_result.append(f"Letter: {letter.upper()} - ASL Shape: Not available")
        time.sleep(1)

    clear_console()
    animation_result.append("Animation complete!")
    results.extend(animation_result)

@app.route('/fingerspell', methods=['POST'])
def fingerspell():
    data = request.get_json()
    text_to_spell = data.get('text', '')

    if not text_to_spell:
        return jsonify({"error": "Text is required"}), 400

    results = []
    thread = threading.Thread(target=fingerspell_animation, args=(text_to_spell, results))
    thread.start()
    thread.join()

    return jsonify({"results": results})

@app.route('/handle-hand-gestures', methods=['POST'])
def handle_hand_gestures_route():
    # Initialize the HandDetector
    detector = HandDetector(detectionCon=0.7, maxHands=1)

    # Initialize Pygame and load music
    pygame.mixer.init()
    pygame.mixer.music.load('song.mp3')  # Replace with your music file
    pygame.mixer.music.play(-1)  # Start playing the music in an infinite loop
    pygame.mixer.music.pause()   # Pause it initially

    # Function to detect fist gesture
    def is_fist(hand):
        if hand:
            # Check if all fingertips are below their respective MCP joints
            if (hand["lmList"][8][1] > hand["lmList"][5][1] and
                hand["lmList"][12][1] > hand["lmList"][9][1] and
                hand["lmList"][16][1] > hand["lmList"][13][1] and
                hand["lmList"][20][1] > hand["lmList"][17][1]):
                return True
        return False

    # Function to detect open hand gesture
    def is_open_hand(hand):
        if hand:
            # Check if all fingertips are above their respective MCP joints
            if (hand["lmList"][8][1] < hand["lmList"][5][1] and
                hand["lmList"][12][1] < hand["lmList"][9][1] and
                hand["lmList"][16][1] < hand["lmList"][13][1] and
                hand["lmList"][20][1] < hand["lmList"][17][1]):
                return True
        return False

    # Capture the video from webcam
    cap = cv2.VideoCapture(0)
    music_playing = False
    last_gesture = None
    gesture_delay = 0.5  # Delay in seconds to prevent rapid state changes
    last_gesture_time = time.time()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            continue

        # Find the hands
        hands, frame = detector.findHands(frame)

        current_time = time.time()
        if hands:
            hand = hands[0]

            if is_fist(hand) and last_gesture != "fist" and (current_time - last_gesture_time) > gesture_delay:
                if music_playing:
                    pygame.mixer.music.pause()
                    music_playing = False
                    print("Music Paused")
                last_gesture = "fist"
                last_gesture_time = current_time

            elif is_open_hand(hand) and last_gesture != "open_hand" and (current_time - last_gesture_time) > gesture_delay:
                if not music_playing:
                    pygame.mixer.music.unpause()
                    music_playing = True
                    print("Music Playing")
                last_gesture = "open_hand"
                last_gesture_time = current_time

        else:
            last_gesture = None

        # Display the image
        cv2.imshow('Hand Movement Detection', frame)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    pygame.mixer.music.stop()
    pygame.mixer.quit()

    return jsonify({'status': 'success', 'message': 'Gesture handling complete!'})


# Configure the Gemini API
api = os.getenv('GENAI_API_KEY')
genai.configure(api_key=api)

@app.route('/gemini-ai', methods=['POST'])
def gemini_ai():
    # Get the user input from the request
    data = request.json
    prompt = data.get('prompt')

    # Choose the Gemini model and generate text
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)

    # Return the generated text in the response
    return jsonify({'generatedText': response.text})

@app.route('/docker-pull', methods=['POST'])
def docker_pull():
    data = request.json
    image_name = data.get('image_name')
    try:
        # Pulling the Docker image
        result = subprocess.run(['docker', 'pull', image_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            return jsonify({'status': 'success', 'message': f'Image {image_name} pulled successfully!'})
        else:
            return jsonify({'status': 'error', 'message': result.stderr.decode('utf-8')}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/docker-run', methods=['POST'])
def docker_run():
    data = request.json
    container_name = data.get('container_name')
    image_name = data.get('image_name')
    try:
        # Running the Docker container
        result = subprocess.run(['docker', 'run','-dit', '--name', container_name, image_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            return jsonify({'status': 'success', 'message': f'Container {container_name} is running from image {image_name}!'})
        else:
            return jsonify({'status': 'error', 'message': result.stderr.decode('utf-8')}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/docker-remove', methods=['POST'])
def docker_remove():
    data = request.json
    container_name = data.get('container_name')
    try:
        # Stopping and removing the Docker container
        subprocess.run(['docker', 'stop', container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result = subprocess.run(['docker', 'rm', container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            return jsonify({'status': 'success', 'message': f'Container {container_name} removed successfully!'})
        else:
            return jsonify({'status': 'error', 'message': result.stderr.decode('utf-8')}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/docker-logs', methods=['POST'])
def docker_logs():
    data = request.json
    container_id = data.get('container_id')
    try:
        # Using subprocess to get logs of a Docker container
        result = subprocess.run(['docker', 'logs', container_id], capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({'status': 'success', 'logs': result.stdout.splitlines()})
        else:
            return jsonify({'status': 'error', 'message': result.stderr}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/docker-stop', methods=['POST'])
def docker_stop():
    data = request.json
    container_name = data.get('container_name')
    try:
        # Using subprocess to stop a Docker container
        result = subprocess.run(['docker', 'stop', container_name], capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({'status': 'success', 'message': f'Container {container_name} stopped successfully!'})
        else:
            return jsonify({'status': 'error', 'message': result.stderr}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/docker-remove-image', methods=['POST'])
def docker_remove_image():
    data = request.json
    image_name = data.get('image_name')
    try:
        # Using subprocess to remove a Docker image
        result = subprocess.run(['docker', 'rmi', image_name], capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({'status': 'success', 'message': f'Image {image_name} removed successfully!'})
        else:
            return jsonify({'status': 'error', 'message': result.stderr}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/run-linux-command', methods=['POST'])
def run_linux_command():
    data = request.json
    command = data.get('command')
    try:
        # Run the Linux command
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout if result.stdout else result.stderr
        return jsonify({'status': 'success', 'output': output})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    

if __name__ == '__main__':
    app.run(debug=True,port=5000)
    