# Audio Processing Server

This project is a Flask-based server for processing audio files in parallel using worker threads. It provides a web interface for uploading audio files and uses Flask-SocketIO for real-time communication with clients.

## Features

- **File Upload**: Upload audio files for processing.
- **Parallel Processing**: Splits audio into chunks and processes them in parallel using a thread pool.
- **Real-Time Updates**: Uses WebSockets to emit real-time updates about the processing status.
- **Stop Processing**: Allows stopping the processing of a task at any time.

## Project Structure

```
app.py          # Main server application
templates/
    index.html  # Web interface for the application
```

## Requirements

- Python 3.8 or higher
- Flask
- Flask-SocketIO
- Pydub
- Numpy

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the server:
   ```bash
   python app.py
   ```

4. Open your browser and navigate to `http://localhost:5001`.

## API Endpoints

### `/`
- **Method**: GET
- **Description**: Serves the main webpage.

### `/upload`
- **Method**: POST
- **Description**: Upload an audio file for processing.
- **Request**: Multipart form-data with a `file` field.
- **Response**: JSON with task details.

### `/stop-processing`
- **Method**: POST
- **Description**: Stops the processing of a specific task.
- **Request**: JSON with `task_id` field.
- **Response**: JSON with a success message.

## WebSocket Events

### `connect`
- Triggered when a client connects.

### `disconnect`
- Triggered when a client disconnects.

### `audio_chunk`
- Emitted for each processed audio chunk.

### `processing_complete`
- Emitted when processing is complete.

### `processing_stopped`
- Emitted when processing is stopped.

## Logging

Logs are written to the console with timestamps and thread details for easier debugging.

## License

This project is licensed under the MIT License.