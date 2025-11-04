let word = "";
let sentence = "";
let previousSentence = "";
let autoSpeak = false;
let speechSynth = window.speechSynthesis;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    updateDisplay();
    setInterval(fetchPrediction, 500);
});

function fetchPrediction() {
    fetch("/get_prediction")
        .then(response => response.json())
        .then(data => {
            const char = data.prediction || "_";
            document.getElementById("char").innerText = char;
        })
        .catch(error => {
            document.getElementById("char").innerText = "E";
        });
}

function addChar() {
    const char = document.getElementById("char").innerText;
    if (char && char !== "_" && char !== "E") {
        sentence += char;
        updateDisplay();
        updateWordSuggestions();
    }
}

function addSpace() {
    sentence += " ";
    updateDisplay();
}

function deleteLast() {
    if (sentence.length > 0) {
        previousSentence = sentence;
        sentence = sentence.slice(0, -1);
        updateDisplay();
    }
}

function clearAll() {
    previousSentence = sentence;
    sentence = "";
    document.getElementById("translation").innerText = "";
    updateDisplay();
}

function undo() {
    if (previousSentence) {
        const temp = sentence;
        sentence = previousSentence;
        previousSentence = temp;
        updateDisplay();
    }
}

function autoSpeakToggle() {
    autoSpeak = !autoSpeak;
    const btn = document.getElementById("autoSpeakBtn");
    btn.textContent = autoSpeak ? "Auto Speak ON" : "Auto Speak OFF";
}

function speakText() {
    const translatedText = document.getElementById("translation").innerText;
    const englishText = sentence.trim();
    
    // If there's a Kannada translation, speak that, otherwise speak English
    const textToSpeak = translatedText && translatedText !== "Translation failed" && translatedText !== "Translation offline" ? translatedText : englishText;
    const langToUse = textToSpeak === translatedText ? 'kn' : 'en';
    
    if (!textToSpeak) return;
    
    if ('speechSynthesis' in window) {
        // Stop any current speech
        speechSynth.cancel();
        
        const utterance = new SpeechSynthesisUtterance(textToSpeak);
        
        // Set language based on the text
        if (textToSpeak === translatedText && translatedText !== englishText) {
            // It's a translation - try to use Kannada
            utterance.lang = 'kn-IN'; // Kannada
            utterance.rate = 0.8; // Slower for better pronunciation
        } else {
            // It's English text
            utterance.lang = 'en-US'; // English
        }
        
        // Get available voices and try to find appropriate one
        const voices = speechSynth.getVoices();
        let selectedVoice = null;
        
        if (utterance.lang === 'kn-IN') {
            // Try to find Kannada voice
            selectedVoice = voices.find(voice => 
                voice.lang.includes('kn') || 
                voice.lang.includes('hi') || // Fallback to Hindi if Kannada not available
                voice.name.toLowerCase().includes('kannada') ||
                voice.name.toLowerCase().includes('indian')
            );
        } else {
            // Find English voice
            selectedVoice = voices.find(voice => voice.lang.includes('en'));
        }
        
        if (selectedVoice) {
            utterance.voice = selectedVoice;
        }
        
        utterance.onstart = function() {
            console.log('Started speaking:', textToSpeak);
        };
        
        utterance.onend = function() {
            console.log('Finished speaking');
        };
        
        utterance.onerror = function(event) {
            console.error('Speech synthesis error:', event);
            // Fallback: try with default settings
            if (utterance.lang !== 'en-US') {
                const fallbackUtterance = new SpeechSynthesisUtterance(textToSpeak);
                fallbackUtterance.lang = 'en-US';
                speechSynth.speak(fallbackUtterance);
            }
        };
        
        speechSynth.speak(utterance);
    }
}

function translateText() {
    const text = sentence.trim();
    if (!text) return;

    const lang = document.getElementById("lang").value;
    
    // Show loading
    document.getElementById("translation").innerText = "Translating...";
    
    fetch(`/translate?lang=${lang}&text=${encodeURIComponent(text)}`)
        .then(response => response.json())
        .then(data => {
            const translatedText = data.translated || "Translation failed";
            document.getElementById("translation").innerText = translatedText;
            
            if (autoSpeak && translatedText !== "Translation failed") {
                setTimeout(() => {
                    speakText();
                }, 500);
            }
        })
        .catch(error => {
            document.getElementById("translation").innerText = "Translation offline";
        });
}

function updateWordSuggestions() {
    const currentWord = sentence.trim().split(' ').pop() || "";
    
    if (!currentWord) {
        document.getElementById("wordSuggestions").innerHTML = `
            <div class="suggestion-item">HELLO</div>
            <div class="suggestion-item">THANK</div>
            <div class="suggestion-item">HELP</div>
            <div class="suggestion-item">YOU</div>
        `;
        return;
    }

    fetch(`/suggest?prefix=${encodeURIComponent(currentWord.toLowerCase())}`)
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById("wordSuggestions");
            container.innerHTML = "";
            
            if (data.suggestions && data.suggestions.length > 0) {
                data.suggestions.slice(0, 4).forEach(suggestion => {
                    const div = document.createElement("div");
                    div.className = "suggestion-item";
                    div.textContent = suggestion.toUpperCase();
                    div.onclick = () => selectWord(suggestion);
                    container.appendChild(div);
                });
            } else {
                // Show default suggestions if no matches
                container.innerHTML = `
                    <div class="suggestion-item">HELLO</div>
                    <div class="suggestion-item">THANK</div>
                    <div class="suggestion-item">HELP</div>
                    <div class="suggestion-item">YOU</div>
                `;
            }
        });
}

function selectWord(selectedWord) {
    const words = sentence.trim().split(' ');
    words.pop(); // Remove the partial word
    words.push(selectedWord);
    sentence = words.join(' ') + ' ';
    updateDisplay();
}

function updateDisplay() {
    document.getElementById("sentence").innerText = sentence;
    updateWordSuggestions();
}

// Load voices when they become available
speechSynth.onvoiceschanged = function() {
    console.log('Available voices:', speechSynth.getVoices().length);
};

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    switch(event.key) {
        case ' ':
            event.preventDefault();
            addSpace();
            break;
        case 'Enter':
            event.preventDefault();
            addChar();
            break;
        case 'Backspace':
            event.preventDefault();
            deleteLast();
            break;
    }
});