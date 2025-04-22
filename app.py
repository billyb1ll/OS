from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO
# Import pydub_patch before pydub to fix import errors
import pydub_patch
from pydub import AudioSegment
import numpy as np
import io
from concurrent.futures import ThreadPoolExecutor
import threading
from queue import Queue, Empty
import time
import logging
import uuid
import os
import shutil

# Configure logging for debugging - include timestamp and thread name
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(threadName)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize Flask app with static folder configuration
app = Flask(__name__, static_url_path='/static', static_folder='static')
socketio = SocketIO(app, cors_allowed_origins="*")
thread_executor = ThreadPoolExecutor(
    max_workers=4, thread_name_prefix="Worker")

# Dictionary to track active processing tasks
active_tasks = {}

# Path to the built-in test songs
TEST_SONGS_DIR = os.path.join(app.static_folder, 'audio')

# Ensure test songs directory exists
os.makedirs(TEST_SONGS_DIR, exist_ok=True)

# Check if test song exists and create a default one if needed
def initialize_test_songs():
    """Initialize a default test song if no songs exist in the folder"""
    try:
        # Create test song if the directory is empty
        if not os.listdir(TEST_SONGS_DIR):
            logger.info("No songs found in audio directory. Creating default test song...")
            
            default_test_song = os.path.join(TEST_SONGS_DIR, 'test_song.mp3')
            
            # Create a simple test tone
            sample_rate = 44100  # 44.1kHz sample rate
            duration_ms = 5000   # 5 seconds
            
            # Generate simple sine wave test tone
            sine_sample = AudioSegment.silent(duration=duration_ms)
            sine_sample = sine_sample.set_frame_rate(sample_rate)
            
            # Export as MP3
            sine_sample.export(default_test_song, format="mp3")
            
            logger.info(f"Created test song at {default_test_song}")
        else:
            logger.info(f"Found {len(os.listdir(TEST_SONGS_DIR))} songs in the test songs directory")
    except Exception as e:
        logger.error(f"Failed to initialize test song: {str(e)}")

# Initialize test songs at startup
initialize_test_songs()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/test-songs')
def get_test_songs():
    """Return list of all available audio files in the static/audio directory"""
    songs = []
    try:
        for filename in os.listdir(TEST_SONGS_DIR):
            if filename.lower().endswith(('.mp3', '.wav', '.ogg', '.aac', '.flac')):
                # Get display name by removing extension and replacing underscores with spaces
                display_name = os.path.splitext(filename)[0].replace('_', ' ')
                
                songs.append({
                    'id': filename,
                    'name': display_name,
                    'url': f'/static/audio/{filename}'
                })
        
        # Sort songs by name
        songs.sort(key=lambda x: x['name'])
        
        logger.info(f"Found {len(songs)} audio files in test songs directory")
        return jsonify(songs)
    except Exception as e:
        logger.error(f"Error listing test songs: {str(e)}")
        return jsonify([])


@app.route('/test-song/<song_id>')
def get_test_song(song_id):
    """Serve a specific test song by ID (filename)"""
    try:
        song_path = os.path.join(TEST_SONGS_DIR, song_id)
        if os.path.exists(song_path) and os.path.isfile(song_path):
            return send_from_directory(TEST_SONGS_DIR, song_id)
        else:
            return jsonify({"error": "Test song not found"}), 404
    except Exception as e:
        logger.error(f"Error serving test song {song_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500


def process_chunk(chunk_index, chunk, result_queue, task_id):
    """Process a single audio chunk in a separate thread"""
    thread_id = threading.current_thread().name
    start_time = time.time()

    # Check if task was cancelled before processing
    if task_id not in active_tasks or active_tasks[task_id]['stop_requested']:
        logger.info(
            f"Skipping chunk {chunk_index} as task {task_id} was stopped")
        return

    logger.info(
        f"Thread {thread_id} starting to process chunk {chunk_index} of size {len(chunk)}")

    # Normalize chunk (main processing logic)
    processed_chunk = chunk.tolist()

    processing_time = (time.time() - start_time) * 1000  # ms
    
    # Check if task was cancelled during processing
    if task_id not in active_tasks or active_tasks[task_id]['stop_requested']:
        logger.info(
            f"Discarding chunk {chunk_index} as task {task_id} was stopped during processing")
        return

    # Queue the result for ordered emission
    result_queue.put((chunk_index, processed_chunk))
    logger.info(
        f"Thread {thread_id} finished processing chunk {chunk_index} in {processing_time:.2f}ms")


@app.route('/stop-processing', methods=['POST'])
def stop_processing():
    try:
        data = request.json
        task_id = data.get('task_id')

        if not task_id or task_id not in active_tasks:
            return jsonify({"error": "Invalid task ID"}), 400

        active_tasks[task_id]['stop_requested'] = True
        logger.info(f"Stop requested for task {task_id}")

        # Notify client via websocket
        socketio.emit('processing_stopped')

        return jsonify({"message": "Processing stopped"}), 200

    except Exception as e:
        logger.error(f"Error stopping processing: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            logger.error("No file part in the request")
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']
        if file.filename == '':
            logger.error("No file selected")
            return jsonify({"error": "No file selected"}), 400

        # Generate a unique task ID
        task_id = str(uuid.uuid4())
        logger.info(f"Processing file: {file.filename}, Task ID: {task_id}")

        # Track task metadata
        active_tasks[task_id] = {
            'filename': file.filename,
            'start_time': time.time(),
            'stop_requested': False
        }

        overall_start = time.time()

        # Load and preprocess audio file
        audio = AudioSegment.from_file(file)
        samples = np.array(audio.get_array_of_samples())

        if len(samples) == 0:
            return jsonify({"error": "Empty audio file"}), 400

        # Normalize to range -1.0 to 1.0 for consistent processing
        samples = samples.astype(float) / np.max(np.abs(samples))

        # Split into chunks for parallel processing
        chunks = list(enumerate(np.array_split(samples, 100)))
        result_queue = Queue()

        logger.info(
            f"Starting parallel processing with {len(chunks)} chunks using {thread_executor._max_workers} worker threads")

        # Submit all chunks to thread pool
        futures = []
        submission_start = time.time()
        for i, chunk in chunks:
            future = thread_executor.submit(
                process_chunk, i, chunk, result_queue, task_id)
            futures.append(future)

        submission_time = time.time() - submission_start
        logger.info(
            f"Submitted {len(chunks)} chunks for processing in {submission_time:.2f}s")

        # Thread function for emitting processed chunks in correct order
        def emit_chunks_in_order():
            next_chunk_index = 0
            pending = {}  # Store out-of-order chunks
            emission_start = time.time()
            emitted_count = 0

            logger.info(
                f"Emission thread started, waiting for processed chunks for task {task_id}")

            # Process until all chunks emitted or task stopped
            while next_chunk_index < len(chunks) and task_id in active_tasks:
                if active_tasks[task_id]['stop_requested']:
                    logger.info(
                        f"Emission thread stopping as task {task_id} was stopped")
                    break

                try:
                    # Non-blocking queue get with timeout
                    idx, chunk_data = result_queue.get(timeout=0.1)

                    # If this is the next chunk in sequence, emit immediately
                    if idx == next_chunk_index:
                        socketio.emit('audio_chunk', chunk_data)
                        emitted_count += 1

                        # Log periodically to reduce console spam
                        if emitted_count % 10 == 0:  
                            logger.info(
                                f"Emitted chunk {idx} (In order) - {emitted_count}/{len(chunks)}")

                        next_chunk_index += 1

                        # Emit any subsequent chunks we already have
                        while next_chunk_index in pending:
                            socketio.emit(
                                'audio_chunk', pending[next_chunk_index])
                            logger.info(
                                f"Emitted chunk {next_chunk_index} (From pending)")
                            emitted_count += 1
                            del pending[next_chunk_index]
                            next_chunk_index += 1
                    else:
                        # Store out-of-order chunk for later
                        pending[idx] = chunk_data
                        logger.info(
                            f"Received out-of-order chunk {idx}, storing for later (waiting for {next_chunk_index})")

                except Empty:
                    # Queue was empty, just continue
                    continue

            # Calculate final timings
            emission_time = time.time() - emission_start
            overall_time = time.time() - overall_start

            # Signal completion status to client
            if task_id in active_tasks and active_tasks[task_id]['stop_requested']:
                socketio.emit('processing_stopped')
                logger.info(f"Audio processing stopped for task {task_id}")
            else:
                socketio.emit('processing_complete')
                logger.info(
                    f"Audio processing complete! Emission took {emission_time:.2f}s, Total processing time: {overall_time:.2f}s")

            # Debug info for out-of-order chunks
            logger.info(
                f"Pending chunks at completion: {len(pending)}, Out of order: {sum(1 for k in pending if k < next_chunk_index)}")

            # Cleanup task data
            if task_id in active_tasks:
                del active_tasks[task_id]

        # Start the emission thread
        emission_thread = threading.Thread(
            target=emit_chunks_in_order, name=f"EmissionThread-{task_id}")
        emission_thread.daemon = True
        emission_thread.start()
        logger.info(f"Started emission thread {emission_thread.name}")

        # Return immediately - processing continues asynchronously
        return jsonify({
            "message": "Processing started",
            "chunks": len(chunks),
            "threads": thread_executor._max_workers,
            "task_id": task_id
        }), 202

    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        return jsonify({"error": str(e)}), 500


@socketio.on('connect')
def handle_connect():
    logger.info(
        f'Client connected - Thread: {threading.current_thread().name}')


@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f'Client disconnected - Thread: {threading.current_thread().name}')


if __name__ == "__main__":
    logger.info(
        f"Starting server with {thread_executor._max_workers} worker threads")
    try:
        port = int(os.environ.get("PORT", 5000))  # Default port if not specified
        logger.info(f"Server starting on port {port}")
        socketio.run(app, debug=True, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True)
    except ValueError as e:
        logger.error(f"Invalid port configuration: {e}")
        port = 5000
        logger.info(f"Falling back to default port {port}")
        socketio.run(app, debug=True, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True)
    
    # Clean up resources 
    thread_executor.shutdown()
    logger.info("Server shutting down, cleaning up thread pool")
