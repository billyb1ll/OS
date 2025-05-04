# Music Visualizer with Performance Monitoring

A web-based music visualizer that processes audio files, visualizes audio frequencies in real-time, and monitors system performance. Built with Flask, Flask-SocketIO, and modern web technologies.

## Features

- **Advanced Audio Visualizer**: Real-time frequency visualization with customizable settings:
  - Adjustable resolution (low to ultra high)
  - Multiple color schemes (blue, red, green, rainbow, and custom)
  - Smoothing controls for visual effects
  - Adjustable bar width
  
- **Comprehensive Player Controls**:
  - Play/Pause and Stop controls
  - Volume and playback speed adjustments
  - Seek bar for navigation
  - Real-time progress display

- **Performance Monitoring**:
  - Server metrics (CPU usage, memory usage, processing time)
  - Client metrics (frame rate, rendering time, memory usage)
  - Network metrics (latency, data received, packet loss simulation)
  
- **File Management**:
  - Drag and drop file upload
  - Built-in test songs selection
  - Multiple upload areas for convenience
  
- **Network Simulation**:
  - Configurable network delay
  - Simulated packet loss for testing
  - Real-time impact visualization

- **Parallel Processing (Backend)**:
  - Configurable chunk size (small, medium, large)
  - Threaded audio processing for performance
  - Real-time status updates

## Requirements

- Python 3.8 or higher
- Flask
- Flask-SocketIO
- Pydub
- Numpy

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/billyb1ll/OS.git
   cd OS
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the server:
   ```bash
   python app.py
   ```

4. Open your browser and navigate to `http://localhost:5001` (or the configured port)

## Usage

### Basic Usage
1. Open the application in your browser
2. Either:
   - Drag and drop an audio file onto the upload area
   - Click "Upload File" to select a file from your device
   - Choose one of the available test songs

3. Use the player controls to play/pause, adjust volume, change speed, etc.
4. Watch the real-time audio visualization

### Advanced Settings

#### Visualization Settings
- **Resolution**: Adjust the frequency resolution (64px to 2048px)
- **Color Scheme**: Choose from preset themes or create a custom color
- **Smoothing**: Control the smoothness of visualization transitions (0 to 0.9)
- **Bar Width**: Change the width of visualization bars (1px to 8px)

#### Performance Settings
- **Chunk Size**: Select processing chunk size (small, medium, large)
- **Network Simulation**: Test with artificial network delays and packet loss

## Performance Monitoring

The application includes real-time monitoring of:

- **Server Performance**:
  - CPU and memory usage
  - Processing time per chunk
  - Total chunks processed
  
- **Client Performance**:
  - Frame rate (FPS)
  - Rendering time
  - Client-side memory usage
  - Visualization smoothness
  
- **Network Performance**:
  - Latency
  - Data received
  - Packet statistics

## API Endpoints

### `/`
- **Method**: GET
- **Description**: Serves the main webpage

### `/upload`
- **Method**: POST
- **Description**: Upload an audio file for processing
- **Parameters**:
  - `file`: The audio file to process
  - `chunk_size`: Size of processing chunks (small, medium, large)
- **Response**: JSON with task details

### `/stop-processing`
- **Method**: POST
- **Description**: Stops the processing of a specific task
- **Request**: JSON with `task_id` field
- **Response**: JSON with a success message

### `/test-songs`
- **Method**: GET
- **Description**: Returns a list of available test songs
- **Response**: JSON array of song objects with name and URL

## WebSocket Events

The application uses WebSockets for real-time communication:

### Server to Client
- `audio_chunk`: Sends processed audio chunk data
- `processing_complete`: Notifies when processing is complete
- `processing_stopped`: Notifies when processing is manually stopped

### Client to Server
- Connection events for managing WebSocket lifecycle

## Browser Compatibility

- Recommended: Chrome or Firefox for best performance
- Works on most modern browsers with HTML5 and WebSocket support

## Developers

Developed by Billy @ Ratatatamoth group - 2025