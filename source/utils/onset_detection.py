"""
Author: Ankit Anand
"""

import librosa
import numpy as np
from numba import jit

def get_ticks_position(metro_audio, sr, H):
	onsets = librosa.onset.onset_detect(y=metro_audio, sr=sr, hop_length=H, units="time")
	return onsets

