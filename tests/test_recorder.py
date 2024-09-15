import unittest
from unittest.mock import MagicMock, patch
from src import DatasetRecorder

class TestDatasetRecorder(unittest.TestCase):
    @patch('src.recorder.ScreenshotRecorder')
    @patch('src.recorder.MouseKeyboardRecorder')
    @patch('src.recorder.AudioRecorder')
    def setUp(self, mock_audio, mock_mouse_keyboard, mock_screenshot):
        self.mock_audio = mock_audio
        self.mock_mouse_keyboard = mock_mouse_keyboard
        self.mock_screenshot = mock_screenshot
        self.recorder = DatasetRecorder(base_output_dir="test_output", screenshot_freq=1)

    def test_start_recording(self):
        with patch('src.recorder.time.sleep'):
            self.recorder.start_recording(duration=1)

        self.mock_screenshot.return_value.start.assert_called_once()
        self.mock_mouse_keyboard.return_value.start.assert_called_once()
        self.mock_audio.return_value.start.assert_called_once()

    def test_stop_recording(self):
        self.recorder.start_recording(duration=1)
        self.recorder.stop_recording()

        self.mock_screenshot.return_value.stop.assert_called_once()
        self.mock_mouse_keyboard.return_value.stop.assert_called_once()
        self.mock_audio.return_value.stop.assert_called_once()

    def test_flush_data(self):
        mock_queue = MagicMock()
        mock_queue.empty.side_effect = [False, False, True]
        mock_queue.get.side_effect = [
            ('screenshot', 1000, 'mock_screenshot_data'),
            ('mouse_move', 1001, (100, 200)),
        ]
        self.recorder.data_queue = mock_queue

        self.recorder.flush_data()

        self.assertEqual(mock_queue.get.call_count, 2)

if __name__ == '__main__':
    unittest.main()
