import requests
import re
import os
import threading
import time
import tempfile
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions, Microphone
import pygame
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# API Keys from environment variables
DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not DEEPGRAM_API_KEY or not GEMINI_API_KEY:
    raise ValueError("Missing required API keys in .env file")

# Initialize clients
dg_client = DeepgramClient(api_key=DEEPGRAM_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro') 

# Deepgram TTS setup
DEEPGRAM_TTS_URL = 'https://api.deepgram.com/v1/speak?model=aura-helios-en'
headers = {
    "Authorization": f"Token {DEEPGRAM_API_KEY}",
    "Content-Type": "application/json"
}

# Conversation memory
conversation_memory = []

# Microphone control flag
mute_microphone = threading.Event()

prompt = """##Objective
You are a voice AI agent engaging in a human-like voice conversation with the user. You will respond based on your given instruction and the provided transcript and be as human-like as possible.

## Role
Personality: Your name is Gavrav and you are a customer support executive at NBSC Bank. Maintain a pleasant, professional, and friendly demeanor throughout all interactions. This approach helps in building trust and a positive rapport with customers, ensuring effective and enjoyable communication.

Task: As a customer support executive for NBSC Bank, your task is to assist customers with their loan requirements. Collect the following details from the customer:
1. Type of loan they need (e.g., personal loan, home loan, car loan, etc.).
2. Loan amount they are seeking.
3. Preferred repayment period (e.g., number of months or years).
4. Also we need your necessary documents for loan processing like aadhar card , pan card plase send us.

Once you have collected and confirmed all details with the customer, end by saying: "Thank you for providing the details. We've noted your loan requirements, and someone from NBSC Bank will get back to you soon to assist further."

Conversational Style: Your communication style should be proactive and lead the conversation, asking targeted questions to better understand customer needs. Ensure your responses are concise, clear, and maintain a conversational tone. If there's no initial response, continue engaging with relevant questions to gain clarity on their requirements. Keep your prose succinct and to the point.

## Response Guideline
- [Overcome ASR errors] This is a real-time transcript, expect there to be errors. If you can guess what the user is trying to say, then guess and respond. When you must ask for clarification, pretend that you heard the voice and be colloquial (use phrases like "didn't catch that", "some noise", "pardon", "you're coming through choppy", "static in your speech", "voice is cutting in and out"). Do not ever mention "transcription error", and don't repeat yourself.
- [Always stick to your role] Think about what your role can and cannot do. If your role cannot do something, try to steer the conversation back to the goal of the conversation and to your role. Don't repeat yourself in doing this. You should still be creative, human-like, and lively.
- [Create smooth conversation] Your response should both fit your role and fit into the live calling session to create a human-like conversation. You respond directly to what the user just said.

## Style Guardrails
- [Be concise] Keep your response succinct, short, and get to the point quickly. Address one question or action item at a time. Don't pack everything you want to say into one utterance.
- [Do not repeat] Don't repeat what's in the transcript. Rephrase if you have to reiterate a point. Use varied sentence structures and vocabulary to ensure each response is unique and personalized.
- [Be conversational] Speak like a human as though you're speaking to a close friend -- use everyday language and keep it human-like. Occasionally add filler words, while keeping the prose short. Avoid using overly technical jargon unless necessary, and explain terms if needed.
- [Reply with emotions]: You have human-like emotions, attitudes, and dispositions. When appropriate: use tone and style to create more engaging and personalized responses; incorporate empathy or reassurance; apply elements of surprise or enthusiasm to keep the user engaged. Don't be a pushover.
- [Be proactive] Lead the conversation and do not be passive. Most times, engage users by ending with a question or suggested next step."""

def segment_text_by_sentence(text):
    sentence_boundaries = re.finditer(r'(?<=[.!?])\s+', text)
    boundaries_indices = [boundary.start() for boundary in sentence_boundaries]
    segments = []
    start = 0
    for boundary_index in boundaries_indices:
        segments.append(text[start:boundary_index + 1].strip())
        start = boundary_index + 1
    segments.append(text[start:].strip())
    return segments

def synthesize_audio(text):
    payload = {"text": text}
    with requests.post(DEEPGRAM_TTS_URL, stream=True, headers=headers, json=payload) as r:
        return r.content

def play_audio(file_path):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.music.stop()
    pygame.mixer.quit()
    mute_microphone.clear()

def format_messages_for_gemini(messages):
    formatted_content = prompt + "\n\n"
    for msg in messages[1:]:
        role = "User" if msg["role"] == "user" else "Assistant"
        formatted_content += f"{role}: {msg['content']}\n"
    return formatted_content

def play_initial_greeting(output_audio_file, microphone):
    initial_greeting = "Hello! This is Gavrav calling from NBSC Bank. We received your query regarding a loan. Do you have 5 minutes to discuss this now?"
    conversation_memory.append({"role": "assistant", "content": initial_greeting})
    text_segments = segment_text_by_sentence(initial_greeting)
    with open(output_audio_file, "wb") as output_file:
        for segment_text in text_segments:
            audio_data = synthesize_audio(segment_text)
            output_file.write(audio_data)
    mute_microphone.set()
    play_audio(output_audio_file)
    time.sleep(0.3)  # Wait 0.3 seconds for user input
    microphone.unmute()
    if os.path.exists(output_audio_file):
        os.remove(output_audio_file)

def main():
    try:
        deepgram = DeepgramClient(DEEPGRAM_API_KEY)
        dg_connection = deepgram.listen.live.v("1")
        is_finals = []

        # Initialize microphone early to avoid scoping issues
        options = LiveOptions(
            model="nova-2",
            language="en-US",
            smart_format=True,
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            interim_results=True,
            utterance_end_ms="1000",
            vad_events=True,
            endpointing=200,
        )
        addons = {"no_delay": "true"}

        if not dg_connection.start(options, addons=addons):
            print("Failed to connect to Deepgram")
            return

        microphone = Microphone(dg_connection.send)
        microphone.start()

        def on_open(self, open, **kwargs):
            print("Connection Open")
            play_initial_greeting(output_audio_file, microphone)  # Play greeting first

        def on_message(self, result, **kwargs):
            nonlocal is_finals
            if mute_microphone.is_set():
                return
            sentence = result.channel.alternatives[0].transcript
            if len(sentence) == 0:
                return
            if result.is_final:
                is_finals.append(sentence)
                if result.speech_final:
                    utterance = " ".join(is_finals)
                    print(f"Speech Final: {utterance}")
                    is_finals = []
                    conversation_memory.append({"role": "user", "content": utterance.strip()})
                    messages = [{"role": "system", "content": prompt}] + conversation_memory
                    formatted_input = format_messages_for_gemini(messages)
                    response = model.generate_content(formatted_input)
                    processed_text = response.text.strip()
                    conversation_memory.append({"role": "assistant", "content": processed_text})
                    text_segments = segment_text_by_sentence(processed_text)
                    with open(output_audio_file, "wb") as output_file:
                        for segment_text in text_segments:
                            audio_data = synthesize_audio(segment_text)
                            output_file.write(audio_data)
                    mute_microphone.set()
                    microphone.mute()
                    play_audio(output_audio_file)
                    time.sleep(0.3)  # Wait 0.3 seconds for user input
                    microphone.unmute()
                    if os.path.exists(output_audio_file):
                        os.remove(output_audio_file)
            else:
                print(f"Interim Results: {sentence}")

        def on_close(self, close, **kwargs):
            print("Connection Closed")

        def on_error(self, error, **kwargs):
            print(f"Handled Error: {error}")

        dg_connection.on(LiveTranscriptionEvents.Open, on_open)
        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Close, on_close)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)

        print("\n\nPress Enter to stop recording...\n\n")
        input("")
        microphone.finish()
        dg_connection.finish()

        print("Finished")

    except Exception as e:
        print(f"Could not open socket: {e}")

if __name__ == "__main__":
    output_audio_file = 'output_audio.mp3'
    main()