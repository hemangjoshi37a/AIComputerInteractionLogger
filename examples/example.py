import sys
import os
import csv
from collections import defaultdict

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.recorder import DatasetRecorder
import logging
import time

def main():
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Create a DatasetRecorder instance
    recorder = DatasetRecorder(base_output_dir="example_dataset", screenshot_freq=2)

    try:
        # Start recording for 60 seconds
        logging.info("Starting recording session for 60 seconds...")
        recorder.start_recording(duration=60)

        # Prompt user for interactions
        print("\nRecording in progress. Please perform the following actions:")
        print("1. Move your mouse around the screen")
        print("2. Click the left mouse button a few times")
        print("3. Right-click and drag the mouse")
        print("4. Type some text (e.g., 'Hello, world!')")
        print("5. Scroll up and down on a webpage or document")
        print("6. Press some keyboard shortcuts (e.g., Ctrl+C, Ctrl+V)")

        # Wait for user interactions
        for i in range(6):
            print(f"\nTime remaining: {60 - i*10} seconds")
            time.sleep(10)

    except KeyboardInterrupt:
        logging.info("Recording stopped by user.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        # Ensure the recording is stopped and data is saved
        recorder.stop_recording()
        logging.info("Recording session ended.")
        time.sleep(2)  # Allow time for final data processing

    # Display information about the recorded data
    session_dir = recorder.session_dir
    if session_dir:
        logging.info(f"\nRecorded data saved in: {session_dir}")
        logging.info("Recorded data includes:")
        logging.info(f"- Screenshots: {len([f for f in os.listdir(session_dir) if f.startswith('screenshot')])}")
        logging.info(f"- Audio file: audio.wav")

        # Count and display events from the CSV file
        csv_path = os.path.join(session_dir, 'events.csv')
        event_counts = defaultdict(int)
        with open(csv_path, 'r') as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader)  # Skip header
            for row in csv_reader:
                event_type = row[1]
                event_counts[event_type] += 1

        logging.info("\nEvent counts:")
        for event_type, count in event_counts.items():
            logging.info(f"- {event_type}: {count}")

        # Display the first few lines of the CSV file
        logging.info("\nFirst few lines of the events.csv file:")
        with open(csv_path, 'r') as csvfile:
            for i, line in enumerate(csvfile):
                if i > 10:  # Display only the first 10 lines after the header
                    break
                logging.info(line.strip())

if __name__ == "__main__":
    main()
