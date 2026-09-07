#AI Chatbot for Customer Support

from tkinter import *
from tkinter import scrolledtext, messagebox
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import random
import threading
from datetime import datetime

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import pyttsx3     #Text → Speech
except ImportError:
    pyttsx3 = None

try:
    from deep_translator import GoogleTranslator     # For Translation
    print("Translation library loaded successfully")
except ImportError as e:
    GoogleTranslator = None
    print("Translation library error:", e)

#FAQ KNOWLEDGE BASE
knowledge_base = [
{"tag":"greeting",
"patterns":["hi","hello","hey","good morning","good evening","is anyone there"],
"responses": ["Hello! Welcome to our support chat."
" How can I help you today?", "Hi there! What can I do for you?"]},

{"tag": "goodbye",
"patterns": ["bye", "goodbye", "see you later", "talk to you later","exit", "quit"],
"responses": ["Goodbye! Have a great day.", "Bye! Feel free to come back anytime."]},

{"tag": "thanks",
"patterns": ["thanks", "thank you", "that helps", "appreciate it"],
"responses": ["You're welcome!", "Happy to help!"]},

{"tag": "hours",
"patterns": ["what are your working hours", "when are you open", "business hours",
"opening time", "closing time"],
"responses": ["We are open Monday to Saturday, 9 AM to 9 PM."]},

{"tag": "location",
"patterns": ["where are you located", "what is your address", "store location",
"where is your office"],
"responses": ["We are located in Karachi, Pakistan. You can also reach us online 24/7."]},

{"tag": "shipping",
"patterns": ["how long does shipping take", "delivery time", "when will my order arrive",
"shipping cost"],
"responses": ["Standard delivery takes 3-5 business days. Shipping cost depends on your location."] },

{"tag": "returns",
"patterns": ["how do I return an item", "return policy", "can I get a refund", "exchange product"],
"responses": ["You can return any item within 7 days of delivery for a full refund."] },

{"tag": "payment",
"patterns": ["what payment methods do you accept", "can I pay with card","cash on delivery available"],
"responses": ["We accept credit/debit cards, bank transfer, and cash on delivery."] },

{"tag": "track_order",
"patterns": ["how do I track my order", "where is my order", "track my package", "order status"],
"responses": ["You can track your order using the tracking link sent to your email after purchase."] },

{"tag": "contact_support",
"patterns": ["how can I contact support", "talk to a human", "customer service number",
"connect me to an agent"],
"responses": ["You can reach our human support team at support@example.com or call 0300-1234567."] },

{"tag": "product_info",
"patterns": ["tell me about your products", "what do you sell", "product details", "product catalog"],
"responses": ["We offer a wide range of electronics, accessories, and home appliances. "
"Ask me about any specific product!"] },

{"tag": "price",
"patterns": ["how much does it cost", "what is the price", "pricing details"],
"responses": ["Prices vary by product. Could you tell me which product you're asking about?"] },

{"tag": "bot_name",
"patterns": ["what is your name", "who are you", "what should I call you"],
"responses": ["I'm SupportBot, your virtual customer support assistant!"] },

{"tag": "capabilities",
"patterns": ["what can you do", "how can you help me", "what are your features"],
"responses": ["I can answer questions about orders, shipping, returns, payments, and more!"] },
]

FALLBACK_RESPONSES = [
    "I'm sorry, I didn't quite understand that. Could you rephrase?",
    "I'm not sure I follow. Can you ask that in a different way?",
    "Hmm, that's outside what I know. Try asking about orders, shipping, returns, or payments."
]

CONFIDENCE_THRESHOLD = 0.3

LANGUAGES = {
    "English": "en",
    "Urdu": "ur",
    "Arabic": "ar",
    "Spanish": "es",
    "French": "fr",
}


all_patterns = []
pattern_tags = []
for item in knowledge_base:
    for pattern in item["patterns"]:
        all_patterns.append(pattern)
        pattern_tags.append(item["tag"])

vectorizer = TfidfVectorizer(stop_words="english")
pattern_vectors = vectorizer.fit_transform(all_patterns)


conversation_history = []
user_name = None
last_tag = None

def get_response(user_input):
    global user_name , last_tag
    user_input_clean = user_input.lower().strip()

    # special case: user is introducing their name
    if "my name is" in user_input_clean or "call me" in user_input_clean:
        words = (user_input_clean.replace("my name is", "")
                                 .replace("call me", "")
                                 .replace("i am", "")
                                  .strip())

        if words:
            user_name = words.split()[0].capitalize()
            last_tag = "user_name"
            return f"Nice to meet you, {user_name}! How can I help you today?", 1.0, "user_name"

    # turn the user's sentence into a vector (list of numbers)
    input_vector = vectorizer.transform([user_input_clean])

    # compare it with every stored pattern
    similarity_scores = cosine_similarity(input_vector , pattern_vectors)
    best_index = similarity_scores.argmax()
    confidence = similarity_scores[0][best_index]

    if confidence < CONFIDENCE_THRESHOLD:
        last_tag = "fallback"
        return random.choice(FALLBACK_RESPONSES) , confidence, "fallback"

    matched_tag = pattern_tags[best_index]
    matched_item = None
    for item in knowledge_base:
        if item["tag"] == matched_tag:
            matched_item = item
            break

    response = random.choice(matched_item["responses"])

    if user_name and matched_tag=="greeting":
        response =  f"Hi {user_name}!" +response

    last_tag = matched_tag
    return response, confidence, matched_tag


def translate_text(text, language_name):
    if language_name == "English":
        return text
    if GoogleTranslator is None:
        return text

    try:
        target_code = LANGUAGES[language_name]
        return GoogleTranslator(source = "auto", target=target_code).translate(text)
    except Exception as e:
        print("Translation error:", e)
        return text

def speak_text(text):
    if pyttsx3 is None or not tts_enabled.get():
        return text

    def _speak():
      engine = pyttsx3.init()
      engine.say(text)
      engine.runAndWait()

    threading.Thread(target=_speak, daemon=True).start()

window = Tk()
window.title("SupportBot - AI Customer Support Chatbot")
window.geometry("600x700")
window.configure(bg="#f0f2f5")

title_label = Label(window, text = "SupportBot", font =("Helvetica", 18, "bold"),
                     bg="#075E54", fg="white")
title_label.place(x=0, y=0, width= 600, height= 50)

chat_area = scrolledtext.ScrolledText(window, wrap = WORD, font =("Helvetica",11),
                                      state = DISABLED, bg ="white")
chat_area.place(x=10, y=60, width=580, height=400)

confidence_label = Label(window, text="Confidence: -", font=("Helvetica", 9),
                          bg="#f0f2f5", fg="#555", anchor="w")
confidence_label.place(x=10, y=465, width=580, height=20)

def display_message(sender, message):
    chat_area.config(state = NORMAL)
    timestamp = datetime.now().strftime("%H:%M")
    chat_area.insert(END,f" [{timestamp}] {sender} : {message} \n\n")
    chat_area.config(state = DISABLED)
    chat_area.see(END)

def send_message(event=None):
    user_text = user_entry.get()
    if user_text == "":
        return
    display_message("You", user_text)
    conversation_history.append({"sender":"You" , "message":user_text})

    bot_reply, confidence, tag = get_response(user_text)
    translated_reply = translate_text(bot_reply, selected_language.get())

    display_message("SupportBot", translated_reply)
    conversation_history.append({"sender":"SupportBot", "message":translated_reply, "tag": tag})

    confidence_label.config(text=f"Confidence: {confidence * 100:.1f}%   |   Intent detected: {tag}")

    speak_text(translated_reply)

    user_entry.delete(0,END)

    if user_text.lower() in ["bye", "goodbye", "exit", "quit"]:
        window.after(1500, window.destroy)

# --- text entry + mic button + send button ---
user_entry = Entry(window, font=("Helvetica", 12))
user_entry.place(x=10, y=495, width=350, height=35)

def listen_voice():
    if sr is None:
        messagebox.showerror("Missing library",
                             "Please install these first:\n\npip install SpeechRecognition pyaudio")
        return
    threading.Thread(target=_listen_thread, daemon=True).start()

def _listen_thread():
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            mic_button.config(text="🎤 Listening...")
            recognizer.adjust_for_ambient_noise(source,duration =0.5)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)

        mic_button.config(text="🎤 Speak")
        spoken_text = recognizer.recognize_google(audio)
        user_entry.delete(0, END)
        user_entry.insert(0, spoken_text)
        send_message()

    except sr.WaitTimeoutError:
        mic_button.config(text="🎤 Speak")
        messagebox.showinfo("No speech detected", "I didn't hear anything. Please try again.")
    except sr.UnknownValueError:
        mic_button.config(text="🎤 Speak")
        messagebox.showinfo("Not understood", "Sorry, I couldn't understand that audio.")
    except Exception as e:
        mic_button.config(text="🎤 Speak")
        messagebox.showerror("Microphone error", str(e))

mic_button = Button(window, text="🎤 Speak", font=("Helvetica", 10), command=listen_voice)
mic_button.place(x=365, y=495, width=100, height=35)

send_button = Button(window, text="Send", font=("Helvetica", 11, "bold"),
                             bg="#075E54", fg="white", command=send_message)
send_button.place(x=470, y=495, width=120, height=35)
user_entry.bind("<Return>", send_message)

lang_label = Label(window, text="Reply language:", font=("Helvetica", 9), bg="#f0f2f5")
lang_label.place(x=10, y=540, width=100, height=25)

selected_language = StringVar(value="English")
language_menu = OptionMenu(window, selected_language, *LANGUAGES.keys())
language_menu.place(x=115, y=537, width=120, height=28)

tts_enabled = BooleanVar(value=False)
tts_checkbox = Checkbutton(window, text="🔊 Read replies aloud", variable=tts_enabled,
                                   bg="#f0f2f5", font=("Helvetica", 9))
tts_checkbox.place(x=250, y=537, width=200, height=28)


def save_history():
    if not conversation_history:
        messagebox.showinfo("No history", "There is no conversation to save yet.")
        return
    filename = f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        for entry in conversation_history:
            f.write(f"{entry['sender']}: {entry['message']}\n")
    messagebox.showinfo("Saved", f"Chat history saved as {filename}")

save_button = Button(window, text="Save Chat History", font=("Helvetica", 10), command=save_history)
save_button.place(x=10, y=580, width=200, height=30)

def clear_chat():
    chat_area.config(state=NORMAL)
    chat_area.delete(1.0, END)
    chat_area.config(state=DISABLED)
    conversation_history.clear()

clear_button = Button(window, text="Clear Chat", font=("Helvetica", 10), command=clear_chat)
clear_button.place(x=220, y=580, width=150, height=30)

display_message("SupportBot", "Hello! I'm SupportBot. Ask me about orders, shipping, "
                              "returns, payments, or anything else. You can type or click "
                              "🎤 Speak to talk to me. Type 'bye' to exit.")

window.mainloop()





