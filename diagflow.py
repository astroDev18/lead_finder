import os
from google.cloud import dialogflow_v2 as dialogflow
import uuid

# Set your Google credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/path/to/your/credentials.json"

# Project and agent parameters
project_id = "jobmax-441319"  # Your DialogFlow project ID

def detect_intent_text(text, session_id, language_code="en-US"):
    """Returns the result of detect intent with texts as inputs.

    Args:
        text: The text message from user
        session_id: A unique identifier for the session
        language_code: Language code (e.g. en-US)

    Returns:
        The detect intent response.
    """
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)
    
    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)
    
    response = session_client.detect_intent(
        request={"session": session, "query_input": query_input}
    )
    
    print("=" * 40)
    print(f"Query text: {response.query_result.query_text}")
    print(f"Intent detected: {response.query_result.intent.display_name}")
    print(f"Intent confidence: {response.query_result.intent_detection_confidence}")
    print(f"Fulfillment text: {response.query_result.fulfillment_text}")
    print("=" * 40)
    
    return response

# Generate a random session ID
session_id = str(uuid.uuid4())

# Test some sample phrases
test_phrases = [
    "yes I'm interested",
    "tell me more",
    "no thanks",
    "not interested",
    "maybe later",
    "what's the price?"
]

# Run tests
for phrase in test_phrases:
    print(f"\nTesting phrase: '{phrase}'")
    detect_intent_text(phrase, session_id)