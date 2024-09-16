<div align="center">
  <img src="https://github.com/user-attachments/assets/67f2d1b0-7e77-4b5b-85bc-3e9100dc2ff4" alt="AI Computer Interaction Logger Logo" width="384px" height="300px">

  # AI Computer Interaction Logger 🖥️🤖

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
  [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

  Generate comprehensive datasets for training multi-modal LLMs in autonomous computer control
</div>

## 📋 Table of Contents
- [About](#about)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Data Structure](#data-structure)
- [Privacy and Security](#privacy-and-security)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Roadmap](#roadmap)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## 🔍 About

AI Computer Interaction Logger is a powerful tool designed to capture and log human-computer interactions, creating rich datasets for training multi-modal Language Learning Models (LLMs). By recording various aspects of user interactions, including screen content, mouse movements, keyboard inputs, and audio, this tool enables the development of AI systems capable of understanding and replicating complex computer operations.

Our goal is to provide researchers and developers with high-quality, diverse datasets that can be used to train AI models for tasks such as:
- Automated software testing
- User experience analysis
- Assistive technologies for computer usage
- AI-driven task automation

## ✨ Features

- 🖼️ High-frequency screenshot capture
  - Configurable capture rate (default: 10 fps)
  - Supports multiple monitors
  - Images saved in PNG format for high quality and compression
- 🖱️ Precise mouse movement and click logging
  - Tracks mouse coordinates (x, y)
  - Records left, right, and middle button clicks
  - Captures scroll wheel movements
- ⌨️ Keyboard input recording
  - Logs all key presses and releases
  - Supports special keys and modifiers (Ctrl, Alt, Shift, etc.)
  - Option to mask sensitive data (e.g., passwords)
- 🎤 Audio environment capture
  - Records system audio and microphone input
  - Configurable sample rate and bit depth
- 💾 Efficient data storage and organization
  - Structured file hierarchy for easy navigation
  - Compressed storage formats to minimize disk usage
- 🔄 Real-time processing and logging
  - Minimal impact on system performance
  - Live monitoring of recording status
- 📊 Structured output for easy ML model ingestion
  - CSV logs for events and metadata
  - Synchronized timestamps across all data types

## 🚀 Installation

### System Requirements
- Python 3.8 or higher
- 4GB RAM (minimum)
- 1GB free disk space for the application
- Additional disk space for recorded data (varies based on recording duration and quality)

### Steps
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

## 🖥️ Usage

### Basic Usage
To start recording computer interactions:

```python
from src.recorder import DatasetRecorder

recorder = DatasetRecorder(screenshot_freq=5)
recorder.start_recording(duration=60)  # Record for 60 seconds
```

### Advanced Configuration
You can customize various aspects of the recording process:

```python
recorder = DatasetRecorder(
    base_output_dir="custom_dataset",
    screenshot_freq=10,
    audio_channels=2,
    audio_samplerate=48000
)
recorder.start_recording(duration=300)  # Record for 5 minutes
```

For more detailed usage instructions, please refer to our [Usage Guide](docs/usage_guide.md).

## 📁 Data Structure

Recorded data is organized in the following structure:

```
dataset/
└── session_YYYYMMDD_HHMMSS/
    ├── events.csv
    ├── audio.wav
    └── screenshots/
        ├── screenshot_timestamp1.png
        ├── screenshot_timestamp2.png
        └── ...
```

- `events.csv`: Contains timestamped logs of mouse and keyboard events
- `audio.wav`: Audio recording of the session
- `screenshots/`: Directory containing all captured screenshots

## 🔒 Privacy and Security

- All data is stored locally on your machine
- No data is transmitted over the network
- Consider implementing additional encryption for sensitive data
- Be cautious when recording in environments with confidential information

## 🛠 Troubleshooting

Common issues and their solutions:

1. **Recording not starting**: Ensure you have the necessary permissions for screen capture and audio recording.
2. **High CPU usage**: Try lowering the screenshot frequency or reducing the number of monitored events.
3. **Missing events in CSV**: Check if any antivirus software is blocking the event hooks.

For more troubleshooting tips, see our [FAQ](docs/faq.md).

## 🤝 Contributing

We welcome contributions to the AI Computer Interaction Logger! Please see our [Contributing Guidelines](CONTRIBUTING.md) for more details on how to get started.

To report bugs or request features, please open an issue on our [GitHub Issues page](https://github.com/yourusername/AIComputerInteractionLogger/issues).

## 🗺 Roadmap

Future development plans include:

- [ ] Support for video capture of specific screen regions
- [ ] Integration with popular machine learning frameworks
- [ ] Web browser extension for capturing in-browser events
- [ ] Multi-language support for broader accessibility

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Open source AI community for inspiration on multi-modal AI systems
- The open-source community for various tools and libraries used in this project


## 📫 Connect with the Author

[<img height="36" src="https://cdn.simpleicons.org/WhatsApp"/>](https://wa.me/917016525813) &nbsp;
[<img height="36" src="https://cdn.simpleicons.org/telegram"/>](https://t.me/hjlabs) &nbsp;
[<img height="36" src="https://cdn.simpleicons.org/Gmail"/>](mailto:hemangjoshi37a@gmail.com) &nbsp;
[<img height="36" src="https://cdn.simpleicons.org/LinkedIn"/>](https://www.linkedin.com/in/hemang-joshi-046746aa) &nbsp;
[<img height="36" src="https://cdn.simpleicons.org/facebook"/>](https://www.facebook.com/hemangjoshi37) &nbsp;
[<img height="36" src="https://cdn.simpleicons.org/Twitter"/>](https://twitter.com/HemangJ81509525) &nbsp;
[<img height="36" src="https://cdn.simpleicons.org/tumblr"/>](https://www.tumblr.com/blog/hemangjoshi37a-blog) &nbsp;
[<img height="36" src="https://cdn.simpleicons.org/StackOverflow"/>](https://stackoverflow.com/users/8090050/hemang-joshi) &nbsp;
[<img height="36" src="https://cdn.simpleicons.org/Instagram"/>](https://www.instagram.com/hemangjoshi37) &nbsp;
[<img height="36" src="https://cdn.simpleicons.org/Pinterest"/>](https://in.pinterest.com/hemangjoshi37a) &nbsp;
[<img height="36" src="https://cdn.simpleicons.org/Blogger"/>](http://hemangjoshi.blogspot.com) &nbsp;
[<img height="36" src="https://cdn.simpleicons.org/similarweb"/>](https://hjlabs.in/) &nbsp;
[<img height="36" src="https://cdn.simpleicons.org/gitlab"/>](https://gitlab.com/hemangjoshi37a) &nbsp;

## 🚀 Dive into a World of Innovation

Explore more groundbreaking projects that are shaping the future of technology:

- [pyPortMan](https://github.com/hemangjoshi37a/pyPortMan): Revolutionizing port management
- [transformers_stock_prediction](https://github.com/hemangjoshi37a/transformers_stock_prediction): AI-powered stock market insights
- [TrendMaster](https://github.com/hemangjoshi37a/TrendMaster): Stay ahead of market trends
- [hjAlgos_notebooks](https://github.com/hemangjoshi37a/hjAlgos_notebooks): A treasure trove of algorithmic wisdom
- [AutoCut](https://github.com/hemangjoshi37a/AutoCut): Streamlining video editing workflows
- [My_Projects](https://github.com/hemangjoshi37a/My_Projects): A showcase of diverse tech innovations
- [Arduino and ESP8266 Wonders](https://github.com/hemangjoshi37a/my_Arduino): Pushing the boundaries of IoT
- [TelegramTradeMsgBacktestML](https://github.com/hemangjoshi37a/TelegramTradeMsgBacktestML): Where finance meets machine learning


---

<div align="center">
  Made with ❤️ for the AI and HCI research community
</div>

