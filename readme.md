<div align="center">
  <img src="https://via.placeholder.com/150" alt="AI Computer Interaction Logger Logo" width="150px" height="150px">

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
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## 🔍 About

AI Computer Interaction Logger is a powerful tool designed to capture and log human-computer interactions, creating rich datasets for training multi-modal Language Learning Models (LLMs). These datasets enable the development of AI systems capable of autonomous computer control operations.

## ✨ Features

- 🖼️ High-frequency screenshot capture
- 🖱️ Precise mouse movement and click logging
- ⌨️ Keyboard input recording
- 🎤 Audio environment capture
- 💾 Efficient data storage and organization
- 🔄 Real-time processing and logging
- 📊 Structured output for easy ML model ingestion

## 🚀 Installation

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

To start recording computer interactions:

```python
from src.recorder import DatasetRecorder

recorder = DatasetRecorder(screenshot_freq=5)
recorder.start_recording(duration=60)  # Record for 60 seconds
```

For more detailed usage instructions, please refer to our [Usage Guide](docs/usage_guide.md).

## 🤝 Contributing

We welcome contributions to the AI Computer Interaction Logger! Please see our [Contributing Guidelines](CONTRIBUTING.md) for more details on how to get started.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Open seource AI for inspiration on multi-modal AI systems
- The open-source community for various tools and libraries used in this project

---

<div align="center">
  Made with ❤️ for the AI and HCI research community
</div>
