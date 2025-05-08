import os

# Application settings
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
PORT = int(os.environ.get('PORT', 5001))

# Twilio settings
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

# Dialogflow settings
DIALOGFLOW_PROJECT_ID = os.environ.get('DIALOGFLOW_PROJECT_ID')

# Server settings
SERVER_BASE_URL = os.environ.get('SERVER_BASE_URL')

# Voice settings
VOICE_NAME = os.environ.get('VOICE_NAME', 'Polly.Matthew')
VOICE_RATE = os.environ.get('VOICE_RATE', '92%')
VOICE_PITCH = os.environ.get('VOICE_PITCH', '0%')

# Call settings
SPEECH_TIMEOUT = int(os.environ.get('SPEECH_TIMEOUT', 3))
GATHER_TIMEOUT = int(os.environ.get('GATHER_TIMEOUT', 5))