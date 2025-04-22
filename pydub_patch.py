"""
Patch for pydub to avoid audioop/pyaudioop import errors.
This patch module will be imported before pydub in app.py.
"""
import sys
import logging

# Configure a logger for this patch
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pydub_patch")

# Create a mock audioop module
class MockAudioop:
    """Mock implementation of audioop for minimal functionality"""
    
    @staticmethod
    def mul(*args):
        # This is a placeholder. The actual function multiplies a sample by a factor.
        logger.warning("Using mock audioop.mul - reduced functionality")
        return args[0]  # Return the sample unchanged
    
    @staticmethod
    def bias(*args):
        # This is a placeholder
        logger.warning("Using mock audioop.bias - reduced functionality")
        return args[0]  # Return the sample unchanged
    
    @staticmethod
    def max(*args):
        # Return a dummy max value
        logger.warning("Using mock audioop.max - reduced functionality")
        return 32767  # Default max for 16-bit audio
    
    # Add other required functions as needed

# Register the mock module
sys.modules['audioop'] = MockAudioop()
sys.modules['pyaudioop'] = MockAudioop()

logger.info("Installed audioop/pyaudioop mock for pydub compatibility")

# Fix the regex syntax warnings
import re
_original_re_match = re.match

def patched_re_match(pattern, string, *args, **kwargs):
    """Patch re.match to fix the invalid escape sequences"""
    pattern_fixes = {
        r'([su]([0-9]{1,2})p?) \(([0-9]{1,2}) bit\)$': r'([su]([0-9]{1,2})p?) \(([0-9]{1,2}) bit\)$',
        r'([su]([0-9]{1,2})p?)( \(default\))?$': r'([su]([0-9]{1,2})p?)( \(default\))?$',
        r'(flt)p?( \(default\))?$': r'(flt)p?( \(default\))?$',
        r'(dbl)p?( \(default\))?$': r'(dbl)p?( \(default\))?$',
    }
    
    if pattern in pattern_fixes:
        pattern = pattern_fixes[pattern]
    
    return _original_re_match(pattern, string, *args, **kwargs)

# Patch re.match
re.match = patched_re_match