import re
import logging
import cv2
import numpy as np


class PrivacyMasker:
    """Detects and masks sensitive information in screenshots."""

    def __init__(self, config):
        self.config = config
        self.enabled = config.get('privacy_masking_enabled', False)
        self.blur_strength = config.get('blur_strength', 20)
        self.mask_patterns = self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for sensitive data."""
        patterns = {}

        if self.config.get('mask_emails', True):
            patterns['email'] = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', re.IGNORECASE)

        if self.config.get('mask_credit_cards', True):
            patterns['credit_card'] = re.compile(r'\b(?:\d[ -]*?){13,16}\b')

        if self.config.get('mask_phone_numbers', False):
            patterns['phone'] = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')

        if self.config.get('mask_ssn', False):
            patterns['ssn'] = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')

        return patterns

    def mask_screenshot(self, image_np, window_info=None):
        """Apply privacy masking to screenshot."""
        if not self.enabled:
            return image_np

        masked = image_np.copy()

        if self.config.get('mask_password_fields', True):
            masked = self._mask_password_fields(masked, window_info)

        if self.config.get('mask_sensitive_patterns', True) and self.mask_patterns:
            masked = self._mask_sensitive_patterns(masked)

        if self.config.get('mask_custom_regions', False):
            masked = self._mask_custom_regions(masked)

        return masked

    def _mask_password_fields(self, image, window_info):
        """Detect and mask password input fields based on window title."""
        if not window_info:
            return image

        title = window_info.get('title', '').lower()

        # Keywords that indicate password dialogs
        password_keywords = ['password', 'pass', 'login', 'sign in', 'authenticate', 'credential']

        if any(keyword in title for keyword in password_keywords):
            # Blur the bottom portion of the screen where password fields typically appear
            height, width = image.shape[:2]
            mask_height = int(height * 0.3)  # Bottom 30%
            y_start = height - mask_height

            return self._blur_region(image, 0, y_start, width, mask_height)

        return image

    def _mask_sensitive_patterns(self, image):
        """Use OCR to find and mask sensitive text patterns."""
        try:
            import pytesseract
        except ImportError:
            logging.warning("pytesseract not installed. Pattern-based masking disabled.")
            return image

        try:
            # Convert to grayscale for OCR
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

            # Get text data
            data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)

            # Find and mask matching text
            for i, text in enumerate(data['text']):
                if not text.strip():
                    continue

                for pattern_name, pattern in self.mask_patterns.items():
                    if pattern.search(text):
                        x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                        image = self._blur_region(image, x, y, w, h)
                        logging.debug(f"Masked {pattern_name}: {text} at ({x}, {y})")
                        break

            return image
        except Exception as e:
            logging.error(f"Error in pattern-based masking: {e}")
            return image

    def _mask_custom_regions(self, image):
        """Mask user-defined regions."""
        custom_regions = self.config.get('custom_mask_regions', [])

        for region in custom_regions:
            if len(region) >= 4:
                x, y, width, height = region[:4]
                image = self._blur_region(image, x, y, width, height)

        return image

    def _blur_region(self, image, x, y, width, height):
        """Apply Gaussian blur to a region."""
        if width <= 0 or height <= 0:
            return image

        # Ensure region is within image bounds
        img_height, img_width = image.shape[:2]
        x = max(0, min(x, img_width - 1))
        y = max(0, min(y, img_height - 1))
        width = min(width, img_width - x)
        height = min(height, img_height - y)

        if width <= 0 or height <= 0:
            return image

        roi = image[y:y+height, x:x+width]
        kernel_size = max(3, self.blur_strength | 1)  # Ensure odd number
        blurred = cv2.GaussianBlur(roi, (kernel_size, kernel_size), 0)
        image[y:y+height, x:x+width] = blurred

        return image
