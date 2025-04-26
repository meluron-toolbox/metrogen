"""
Author: Ankit Anand

Objective: Bandpass filter

Steps:
1. 
"""

import soundfile as sf
import scipy.signal as signal

def band_pass_filter(audio, sr, lowcut, highcut, order=5):
	
	nyquist = 0.5 * sr  # Nyquist frequency is half of the sample rate
	low = lowcut / nyquist
	high = highcut / nyquist
	
	# Design the Butterworth band-pass filter
	b, a = signal.butter(order, [low, high], btype='band')
	
	# Apply the filter using filtfilt to avoid phase distortion
	filtered_audio = signal.filtfilt(b, a, audio)
	
	return filtered_audio