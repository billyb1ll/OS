from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
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

# Configure logging with more detail - include timestamp
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(threadName)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
thread_executor = ThreadPoolExecutor(
    max_workers=4, thread_name_prefix="Worker")

# Track active processing tasks
active_tasks = {}

# Route for the main webpage


@app.route('/')
def index():
    return render_template('index.html')


def process_chunk(chunk_index, chunk, result_queue, task_id):
    """Process a single audio chunk in a separate thread"""
    thread_id = threading.current_thread().name
    start_time = time.time()

    # Check if processing is still active before processing
    if task_id not in active_tasks or active_tasks[task_id]['stop_requested']:
        logger.info(
            f"Skipping chunk {chunk_index} as task {task_id} was stopped")
        return

    # Log the start of processing
    logger.info(
        f"Thread {thread_id} starting to process chunk {chunk_index} of size {len(chunk)}")

    # Normalize chunk
    processed_chunk = chunk.tolist()

    # Calculate processing time
    processing_time = (time.time() - start_time) * \
        1000  # Convert to milliseconds

    # Check again if the task has been stopped
    if task_id not in active_tasks or active_tasks[task_id]['stop_requested']:
        logger.info(
            f"Discarding chunk {chunk_index} as task {task_id} was stopped during processing")
        return

    # Put the processed chunk with its index in the queue for ordered emission
    result_queue.put((chunk_index, processed_chunk))

    # Log the completion of processing
    logger.info(
        f"Thread {thread_id} finished processing chunk {chunk_index} in {processing_time:.2f}ms")

# Route to handle stop requests


@app.route('/stop-processing', methods=['POST'])
def stop_processing():
    try:
        data = request.json
        task_id = data.get('task_id')

        if not task_id or task_id not in active_tasks:
            return jsonify({"error": "Invalid task ID"}), 400

        # Mark the task as stopped
        active_tasks[task_id]['stop_requested'] = True
        logger.info(f"Stop requested for task {task_id}")

        # Notify client that processing has been stopped
        socketio.emit('processing_stopped')

        return jsonify({"message": "Processing stopped"}), 200

    except Exception as e:
        logger.error(f"Error stopping processing: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Route to handle file uploads


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

        # Generate a unique ID for this processing task
        task_id = str(uuid.uuid4())
        logger.info(f"Processing file: {file.filename}, Task ID: {task_id}")

        # Initialize task tracking
        active_tasks[task_id] = {
            'filename': file.filename,
            'start_time': time.time(),
            'stop_requested': False
        }

        # Track overall processing time
        overall_start = time.time()

        audio = AudioSegment.from_file(file)
        samples = np.array(audio.get_array_of_samples())

        if len(samples) == 0:
            return jsonify({"error": "Empty audio file"}), 400

        # Normalize samples to a standard JSON-friendly format
        # Normalize to range -1.0 to 1.0
        samples = samples.astype(float) / np.max(np.abs(samples))

        # Split into chunks for parallel processing
        chunks = list(enumerate(np.array_split(samples, 100)))
        result_queue = Queue()

        logger.info(
            f"Starting parallel processing with {len(chunks)} chunks using {thread_executor._max_workers} worker threads")

        # Submit all chunks for processing in parallel
        futures = []
        submission_start = time.time()
        for i, chunk in chunks:
            future = thread_executor.submit(
                process_chunk, i, chunk, result_queue, task_id)
            futures.append(future)

        submission_time = time.time() - submission_start
        logger.info(
            f"Submitted {len(chunks)} chunks for processing in {submission_time:.2f}s")

        # Create a separate thread to emit processed chunks in order
        def emit_chunks_in_order():
            next_chunk_index = 0
            pending = {}
            emission_start = time.time()
            emitted_count = 0

            logger.info(
                f"Emission thread started, waiting for processed chunks for task {task_id}")

            # Wait until all chunks have been processed and emitted or task is stopped
            while next_chunk_index < len(chunks) and task_id in active_tasks:
                # Check if processing has been stopped
                if active_tasks[task_id]['stop_requested']:
                    logger.info(
                        f"Emission thread stopping as task {task_id} was stopped")
                    break

                try:
                    # Try to get a processed chunk (timeout to prevent blocking forever)
                    idx, chunk_data = result_queue.get(timeout=0.1)

                    # If this is the next chunk in sequence, emit it immediately
                    if idx == next_chunk_index:
                        socketio.emit('audio_chunk', chunk_data)
                        emitted_count += 1

                        if emitted_count % 10 == 0:  # Log every 10 chunks to avoid console flooding
                            logger.info(
                                f"Emitted chunk {idx} (In order) - {emitted_count}/{len(chunks)}")

                        next_chunk_index += 1

                        # Check if we have any subsequent chunks already processed
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

            emission_time = time.time() - emission_start
            overall_time = time.time() - overall_start

            # Signal that processing is complete or was stopped
            if task_id in active_tasks and active_tasks[task_id]['stop_requested']:
                socketio.emit('processing_stopped')
                logger.info(f"Audio processing stopped for task {task_id}")
            else:
                socketio.emit('processing_complete')
                logger.info(
                    f"Audio processing complete! Emission took {emission_time:.2f}s, Total processing time: {overall_time:.2f}s")

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

        # Don't wait for the thread - return immediately
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
    port = int(os.environ.get("PORT", 8080))  # Default to 8080 if PORT is not set
    socketio.run(app, debug=True, host="0.0.0.0", port=port)
    # Clean up threads when the application exits
    thread_executor.shutdown()
    logger.info("Server shutting down, cleaning up thread pool")
