from flask import Flask, request, jsonify, render_template,send_file
from twilio.rest import Client
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
import numpy as np
import base64
from flask_cors import CORS
import os
import threading
from io import BytesIO
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

    
