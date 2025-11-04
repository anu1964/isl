let word = "";
let sentence = "";
let previousSentence = "";
let autoSpeak = false;

// Initialize display
document.addEventListener('DOMContentLoaded', function() {
    updateDisplay();
    setInterval(fetchPrediction, 500);
});

function fetchPrediction() {
    fetch("/get_prediction")
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            const char = data.prediction || "_";
            document.getElementById("char").innerText = char;

            // Update letter suggestions
            const letters = getLetterSuggestions(char);
            updateLetterSuggestions(letters);
        })
        .catch(error => {
            console.error('Error fetching prediction:', error);
            document.getElementById("char").innerText = "E";
        });
}

function getLetterSuggestions(currentChar) {
    if (!currentChar || currentChar === "_" || currentChar === "E") {
        return ["A", "B", "C"];
    }
    
    const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
    const index = alphabet.indexOf(currentChar.toUpperCase());
    
    if (index === -1) return ["A", "B", "C"];
    
    return [
        alphabet[(index + 1) % 26],
        alphabet[(index + 2) % 26],
        alphabet[(index + 3) % 26]
    ];
}

function updateLetterSuggestions(letters) {
    const container = document.getElementById("letterSuggestions");
    container.innerHTML = "";
    
    letters.forEach(letter => {
        const span = document.createElement("span");
        span.innerText = letter;
        span.className = "suggestion";
        span.onclick = () => selectLetter(letter);
        container.appendChild(span);
    });
}

function selectLetter(letter) {
    word += letter;
    updateDisplay();
    updateWordSuggestions();
}

function addChar() {
    const char = document.getElementById("char").innerText;
    if (char && char !== "_" && char !== "E") {
        word += char;
        updateDisplay();
        updateWordSuggestions();
    }
}

function addSpace() {
    if (word.trim()) {
        previousSentence = sentence;
        sentence += word + " ";
        word = "";
        updateDisplay();
        translateText();
    }
}

function deleteLast() {
    if (word.length > 0) {
        word = word.slice(0, -1);
    } else if (sentence.trim()) {
        previousSentence = sentence;
        const words = sentence.trim().split(" ");
        words.pop();
        sentence = words.join(" ") + (words.length > 0 ? " " : "");
    }
    updateDisplay();
    updateWordSuggestions();
}

function clearAll() {
    previousSentence = sentence;
    word = "";
    sentence = "";
    updateDisplay();
    document.getElementById("translation").innerText = "_";
    stopSpeech();
}

function undo() {
    if (previousSentence) {
        const temp = sentence;
        sentence = previousSentence;
        previousSentence = temp;
        updateDisplay();
        translateText();
    }
}

function saveSentence() {
    const text = sentence.trim();
    if (!text) {
        alert("No sentence to save!");
        return;
    }
    
    const blob = new Blob([text], { type: "text/plain" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "isl_sentence.txt";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function translateText() {
    const text = sentence.trim();
    if (!text) {
        document.getElementById("translation").innerText = "_";
        return;
    }

    const lang = document.getElementById("lang").value;
    
    fetch(`/translate?lang=${lang}&text=${encodeURIComponent(text)}`)
        .then(response => {
            if (!response.ok) throw new Error('Translation failed');
            return response.json();
        })
        .then(data => {
            const translatedText = data.translated || "Translation unavailable";
            document.getElementById("translation").innerText = translatedText;
            
            // Auto-speak if enabled
            if (autoSpeak && translatedText && translatedText !== "Translation unavailable" && !translatedText.includes("[")) {
                speakTranslation(translatedText);
            }
        })
        .catch(error => {
            console.error('Translation error:', error);
            document.getElementById("translation").innerText = `[Offline: ${text}]`;
        });
}

function speakTranslation() {
    const translatedText = document.getElementById("translation").innerText;
    
    if (!translatedText || translatedText === "_" || translatedText.includes("[") || translatedText === "Translation unavailable") {
        alert("No valid translation to speak!");
        return;
    }
    
    // Disable speak button during playback
    const speakBtn = document.getElementById("speakBtn");
    speakBtn.disabled = true;
    
    fetch(`/speak?text=${encodeURIComponent(translatedText)}&lang=kn`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log('Playing audio...');
                // Re-enable button after a delay (handled by server)
                setTimeout(() => {
                    speakBtn.disabled = false;
                }, 3000);
            } else {
                alert('Speech error: ' + data.message);
                speakBtn.disabled = false;
            }
        })
        .catch(error => {
            console.error('Speech error:', error);
            alert('Failed to play audio: ' + error.message);
            speakBtn.disabled = false;
        });
}

function stopSpeech() {
    fetch('/stop_speech')
        .then(response => response.json())
        .then(data => {
            console.log('Speech stopped');
        })
        .catch(error => {
            console.error('Stop speech error:', error);
        });
}

function autoSpeakToggle() {
    autoSpeak = !autoSpeak;
    const btn = document.getElementById("autoSpeakBtn");
    if (autoSpeak) {
        btn.textContent = "Auto-Speak: ON";
        btn.classList.add('active');
    } else {
        btn.textContent = "Auto-Speak: OFF";
        btn.classList.remove('active');
    }
}

function setVolume(volume) {
    document.getElementById("volumeValue").textContent = volume + '%';
    // Volume is handled by the system, this is for UI only
    // In a real implementation, you might send this to the server
}

function updateWordSuggestions() {
    if (!word.trim()) {
        document.getElementById("wordSuggestions").innerHTML = "";
        return;
    }

    fetch(`/suggest?prefix=${encodeURIComponent(word.toLowerCase())}`)
        .then(response => {
            if (!response.ok) throw new Error('Suggestion failed');
            return response.json();
        })
        .then(data => {
            const container = document.getElementById("wordSuggestions");
            container.innerHTML = "";
            
            if (data.suggestions && data.suggestions.length > 0) {
                data.suggestions.forEach(suggestion => {
                    const span = document.createElement("span");
                    span.innerText = suggestion;
                    span.className = "suggestion";
                    span.onclick = () => selectWord(suggestion);
                    container.appendChild(span);
                });
            }
        })
        .catch(error => {
            console.error('Suggestion error:', error);
        });
}

function selectWord(selectedWord) {
    word = selectedWord;
    updateDisplay();
}

function updateDisplay() {
    document.getElementById("word").innerText = word || "";
    document.getElementById("sentence").innerText = sentence || "";
    
    // Update document title with current word
    if (word) {
        document.title = `ISL - ${word}`;
    } else if (sentence) {
        const lastWord = sentence.trim().split(" ").pop() || "";
        document.title = `ISL - ${lastWord}`;
    } else {
        document.title = "ISL to Text Converter";
    }
}

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
        case 'Escape':
            event.preventDefault();
            clearAll();
            break;
        case 's':
            if (event.ctrlKey) {
                event.preventDefault();
                saveSentence();
            }
            break;
    }
});