from flask import Flask, render_template, Response, jsonify, request, send_file
import cv2
import joblib
import numpy as np
import mediapipe as mp
import time
import requests
import os
import io
from collections import Counter
from gtts import gTTS
import pygame
import threading
import tempfile

app = Flask(__name__)

# Initialize pygame mixer for audio playback
pygame.mixer.init()

# Load model and word list
try:
    model = joblib.load("isl_letters_only_model.pkl")
    print("Model loaded successfully")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

try:
    with open("words.txt", "r", encoding="utf-8") as f:
        word_list = [line.strip().lower() for line in f if line.strip()]
    print(f"Loaded {len(word_list)} words")
except Exception as e:
    print(f"Error loading words: {e}")
    word_list = ["cat", "dog", "hello", "good", "morning", "night", "please", "thank", "you"]

# MediaPipe setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_draw = mp.solutions.drawing_utils

# Global variables for prediction
last_prediction = ""
recent_preds = []
last_prediction_time = 0
cooldown = 0.2

# Audio management
current_audio_file = None

def gen_frames():
    global last_prediction, recent_preds, last_prediction_time
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    while True:
        success, frame = cap.read()
        if not success:
            print("Error: Could not read frame")
            break
            
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)
        
        row = []
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                for lm in hand_landmarks.landmark:
                    row.extend([lm.x, lm.y, lm.z])
            
            # Pad or truncate to 126 features (42 landmarks * 3 coordinates)
            while len(row) < 126:
                row.extend([0.0, 0.0, 0.0])
            row = row[:126]
            
            # Make prediction with cooldown
            current_time = time.time()
            if current_time - last_prediction_time > cooldown and model is not None:
                try:
                    prediction = model.predict([row])[0]
                    recent_preds.append(prediction)
                    if len(recent_preds) > 5:
                        recent_preds.pop(0)
                    if recent_preds:
                        last_prediction = Counter(recent_preds).most_common(1)[0][0]
                    last_prediction_time = current_time
                except Exception as e:
                    print(f"Prediction error: {e}")
                    last_prediction = "E"
        
        # Display prediction on frame
        cv2.putText(frame, f"Prediction: {last_prediction}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
            
        frame = buffer.tobytes()
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    cap.release()

def speak_kannada_async(text):
    """Generate and play Kannada speech in a separate thread"""
    def play_audio():
        try:
            global current_audio_file
            
            # Stop any currently playing audio
            pygame.mixer.music.stop()
            
            # Create gTTS for Kannada
            tts = gTTS(text=text, lang='kn', slow=False)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                tts.save(fp.name)
                current_audio_file = fp.name
            
            # Play the audio
            pygame.mixer.music.load(current_audio_file)
            pygame.mixer.music.play()
            
            # Wait for playback to complete
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
                
            # Clean up
            try:
                if os.path.exists(current_audio_file):
                    os.unlink(current_audio_file)
            except:
                pass
                
        except Exception as e:
            print(f"TTS Error: {e}")
    
    # Run in separate thread to avoid blocking
    thread = threading.Thread(target=play_audio)
    thread.daemon = True
    thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_prediction')
def get_prediction():
    return jsonify({'prediction': last_prediction})

def simple_translate(text, target_lang='kn'):
    """Simple fallback translation using word mapping"""
    # Enhanced English to Kannada word mapping
    word_map = {
        'hello': 'ನಮಸ್ಕಾರ',
        'cat': 'ಬೆಕ್ಕು',
        'dog': 'ನಾಯಿ',
        'good': 'ಒಳ್ಳೆಯ',
        'morning': 'ಬೆಳಗ್ಗೆ',
        'night': 'ರಾತ್ರಿ',
        'please': 'ದಯವಿಟ್ಟು',
        'thank': 'ಧನ್ಯವಾದ',
        'you': 'ನೀವು',
        'i': 'ನಾನು',
        'we': 'ನಾವು',
        'they': 'ಅವರು',
        'this': 'ಇದು',
        'that': 'ಅದು',
        'is': 'ಆಗಿದೆ',
        'are': 'ಆಗಿದ್ದಾರೆ',
        'the': '',
        'a': '',
        'an': '',
        'yes': 'ಹೌದು',
        'no': 'ಇಲ್ಲ',
        'water': 'ನೀರು',
        'food': 'ಆಹಾರ',
        'help': 'ಸಹಾಯ',
        'name': 'ಹೆಸರು',
        'my': 'ನನ್ನ',
        'your': 'ನಿಮ್ಮ',
        'what': 'ಏನು',
        'when': 'ಯಾವಾಗ',
        'where': 'ಎಲ್ಲಿ',
        'why': 'ಏಕೆ',
        'how': 'ಹೇಗೆ',
        'come': 'ಬನ್ನಿ',
        'go': 'ಹೋಗು',
        'see': 'ನೋಡು',
        'eat': 'ತಿನ್ನು',
        'drink': 'ಕುಡಿ',
        'sleep': 'ಮಲಗು',
        'walk': 'ನಡೆ',
        'run': 'ಓಡು',
        'big': 'ದೊಡ್ಡ',
        'small': 'ಚಿಕ್ಕ',
        'hot': 'ಬಿಸಿ',
        'cold': 'ತಂಪಾದ',
        'beautiful': 'ಸುಂದರ',
        'happy': 'ಸಂತೋಷ',
        'sad': 'ದುಃಖ',
        'family': 'ಕುಟುಂಬ',
        'friend': 'ಸ್ನೇಹಿತ',
        'house': 'ಮನೆ',
        'school': 'ಶಾಲೆ',
        'book': 'ಪುಸ್ತಕ',
        'pen': 'ಪೆನ್',
        'teacher': 'ಶಿಕ್ಷಕ',
        'student': 'ವಿದ್ಯಾರ್ಥಿ'
    }
    
    words = text.lower().split()
    translated_words = []
    
    for word in words:
        if word in word_map:
            if word_map[word]:  # Skip empty translations for articles
                translated_words.append(word_map[word])
        else:
            translated_words.append(f"[{word}]")
    
    return ' '.join(translated_words) if translated_words else text

@app.route('/translate')
def translate():
    lang = request.args.get('lang', 'kn')
    text = request.args.get('text', '')
    
    if not text or text.strip() == "":
        return jsonify({'translated': ''})
    
    try:
        # Try online translation first
        url = f"https://api.mymemory.translated.net/get?q={text}&langpair=en|{lang}"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        translated = data.get("responseData", {}).get("translatedText", "")
        
        if translated and translated != text and not translated.startswith("MYMEMORY"):
            return jsonify({'translated': translated})
        else:
            # Fallback to simple translation
            translated = simple_translate(text, lang)
            return jsonify({'translated': translated})
            
    except Exception as e:
        print(f"Translation error: {e}")
        # Final fallback
        translated = simple_translate(text, lang)
        return jsonify({'translated': translated})

@app.route('/speak')
def speak():
    """Endpoint to speak Kannada text"""
    text = request.args.get('text', '')
    lang = request.args.get('lang', 'kn')
    
    if not text or text.strip() == "":
        return jsonify({'status': 'error', 'message': 'No text provided'})
    
    try:
        speak_kannada_async(text)
        return jsonify({'status': 'success', 'message': 'Playing audio'})
    except Exception as e:
        print(f"Speech error: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/stop_speech')
def stop_speech():
    """Stop currently playing speech"""
    try:
        pygame.mixer.music.stop()
        return jsonify({'status': 'success', 'message': 'Speech stopped'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/suggest')
def suggest():
    prefix = request.args.get('prefix', '').lower().strip()
    if not prefix:
        return jsonify({'suggestions': []})
    
    try:
        matches = [w for w in word_list if w.startswith(prefix)]
        return jsonify({'suggestions': matches[:5]})
    except Exception as e:
        print(f"Suggestion error: {e}")
        return jsonify({'suggestions': []})

if __name__ == '__main__':
    print("Starting ISL to Text Converter...")
    print("Available routes:")
    print("  / - Main page")
    print("  /video_feed - Camera feed with hand detection")
    print("  /get_prediction - Get current predicted character")
    print("  /translate - Translate text to Kannada")
    print("  /speak - Speak Kannada text")
    print("  /stop_speech - Stop current speech")
    print("  /suggest - Get word suggestions")
    app.run(debug=True, host='0.0.0.0', port=5000)