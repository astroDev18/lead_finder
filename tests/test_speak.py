# test_speak.py
from app.services.telnyx_service import speak_text
import os

# Replace with a valid call_control_id from your logs
call_id = "v3:2G5MDs4T03-_mRgOnwS2YXsIFBSzWVNUedXeOSRp_n-zvWaOa0Kj_A"
message = "This is a test message"

# Test the function
result = speak_text(call_id, message)
print(f"Result: {result}")