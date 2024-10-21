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
import numpy as np
import base64
from flask_cors import CORS
import os
import threading
from io import BytesIO
import subprocess
import google.generativeai as genai
from dotenv import load_dotenv
import logging


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

def fingerspell_animation(text, results):
    animation_result = []
    for letter in text.lower():
        if letter in asl_shapes:
            animation_result.append(f"Letter: {letter.upper()} - ASL Shape: {asl_shapes[letter]}")
        else:
            animation_result.append(f"Letter: {letter.upper()} - ASL Shape: Not available")
        time.sleep(1)

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
logging.basicConfig(level=logging.INFO)

@app.route('/gemini-ai', methods=['POST'])
def gemini_ai():
    # Start measuring the time for the function execution
    start_time = time.time()
    
    # Get the user input from the request
    data = request.json
    prompt = data.get('prompt')

    # Log the input prompt
    logging.info(f"Received prompt: {prompt}")

    try:
        # Choose the Gemini model
        model = genai.GenerativeModel("gemini-pro")
        
        # Set a timeout for generating content
        response = model.generate_content(prompt, timeout=5)  # Set a 5-second timeout

        # Log the duration of the response generation
        duration = time.time() - start_time
        logging.info(f"Content generated in {duration:.2f} seconds")

        # Return the generated text in the response
        return jsonify({'generatedText': response.text})

    except genai.TimeoutError:
        logging.error("The generation request timed out.")
        return jsonify({'error': 'The generation request timed out.'}), 504
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500

    
