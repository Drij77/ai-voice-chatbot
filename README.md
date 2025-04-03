# Voice AI Agent

## Features

- Real-time voice conversation
- Speech-to-text transcription using Deepgram
- Text-to-speech synthesis using Deepgram
- Natural language processing using Google's Gemini AI
- Conversation memory to maintain context
- Professional customer support personality

## Prerequisites

- Python 3.8 or higher
- A microphone connected to your computer
- Speakers or headphones
- API keys for:
  - Deepgram
  - Google Gemini

## Installation

1. Clone this repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Copy the `.env.template` file to create your own `.env` file:
   ```bash
   cp .env.template .env
   ```
2. Edit the `.env` file and replace the placeholder values with your actual API keys:
   ```
   DEEPGRAM_API_KEY=your_deepgram_api_key
   GEMINI_API_KEY=your_gemini_api_key
   ```
3. Make sure your microphone is properly connected and set as the default input device

## Usage

1. Activate your virtual environment if not already activated:
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Run the application:
   ```bash
   python app.py
   ```




## Troubleshooting

- If you encounter microphone issues, check your system's audio settings
- Ensure your API keys are correctly set in the `.env` file
- Make sure all dependencies are properly installed
- Check your internet connection as the application requires API access 