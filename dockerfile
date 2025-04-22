# Use the official Python image
FROM python:3.9-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Set the working directory
WORKDIR /app

# Copy the application code
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set default port if not provided
ENV PORT=8080

# Expose the port the app runs on
EXPOSE ${PORT}

# Command to run the application - use sh -c to handle environment variable expansion
CMD ["sh", "-c", "gunicorn --workers=2 --bind=0.0.0.0:$PORT app:app"]