# lead_finder/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies needed for TTS and other libraries
# Ensure these are actually required by your dependencies.
# ffmpeg and libsndfile1 are common for audio processing.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements.txt first to leverage Docker cache
COPY requirements.txt ./

# Install Python dependencies
# Ensure your requirements.txt is up-to-date and correct
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create directory for temporary audio files if your app writes here
# The volume mount in docker-compose.yml will handle this,
# but it's good practice if the app expects the dir to exist.
RUN mkdir -p /app/temp_audio

# Expose the port the app runs on (for documentation and potential direct access)
EXPOSE 5001
# Command to run the application
# Ensure app.py is the correct entry point and runs on 0.0.0.0
CMD ["python", "app.py"]