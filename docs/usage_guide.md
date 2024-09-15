# AI Computer Interaction Logger - Usage Guide

This guide provides detailed instructions on how to use the AI Computer Interaction Logger to capture human-computer interactions for dataset creation.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/AIComputerInteractionLogger.git
   ```
2. Navigate to the project directory:
   ```
   cd AIComputerInteractionLogger
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Basic Usage

To start recording computer interactions:

```python
from src import DatasetRecorder

# Create a DatasetRecorder instance
recorder = DatasetRecorder(base_output_dir="path/to/output", screenshot_freq=5)

# Start recording for 60 seconds
recorder.start_recording(duration=60)
```

This will capture screenshots, mouse movements, keyboard inputs, and audio for 60 seconds.

## Customization

You can customize the recording process by adjusting the following parameters:

- `base_output_dir`: The directory where the dataset will be saved
- `screenshot_freq`: The frequency of screenshot captures (in Hz)

## Output

The recorder will create a new directory for each recording session, containing:

- A CSV file with all events (screenshots, mouse movements, keyboard inputs)
- PNG files for each screenshot
- An NPY file with audio data

## Best Practices

1. Ensure you have sufficient disk space for long recording sessions.
2. Close unnecessary applications to reduce background noise and irrelevant data.
3. For privacy reasons, be mindful of the content on your screen during recording.

## Troubleshooting

If you encounter any issues:

1. Check the console output for error messages.
2. Ensure all dependencies are correctly installed.
3. Verify that you have the necessary permissions for screen capture and audio recording.

For more help, please open an issue on the GitHub repository.
