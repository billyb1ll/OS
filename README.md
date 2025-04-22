# Audio Processing Server & Music Visualizer

This project is a Flask-based server for processing audio files in parallel using worker threads. It provides a web interface for uploading audio files, playing them with a YouTube-like player, and visualizing the audio frequencies in real-time. Flask-SocketIO is used for real-time communication.

## Features

- **File Upload**: Drag and drop MP3 files for processing and playback.
- **Web Player**: A YouTube-styled player interface with:
    - Play/Pause and Stop controls.
    - Volume and Playback Speed adjustments.
    - Seek bar for navigating the audio track.
    - Real-time time display (current / total).
    - Displays the name of the currently playing file.
- **Audio Visualizer**: Real-time frequency bar visualization of the playing audio.
- **Parallel Processing (Backend)**: Splits audio into chunks and processes them in parallel using a thread pool (though this backend processing might not be directly visible in the current UI focus).
- **Real-Time Updates (Backend)**: Uses WebSockets to potentially emit updates about backend processing status.
- **Stop Processing (Backend)**: Allows stopping backend processing tasks.

## Project Structure

```
app.py          # Main Flask server application
templates/
    index.html  # Web interface (Player & Visualizer)
# ... other files (requirements.txt, etc.)
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

## Usage

1. Run the server:
   ```bash
   python app.py
   ```
2. Open your browser and navigate to `http://localhost:5001`.
3. Drag and drop an MP3 file onto the designated area.
4. The file will load, and you can use the player controls to play, pause, seek, adjust volume, and change speed while viewing the visualization.

## API Endpoints (Backend)

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

## WebSocket Events (Backend)

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