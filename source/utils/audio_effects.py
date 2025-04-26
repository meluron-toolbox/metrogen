"""
Author: Ankit Anand
"""

import numpy as np
import librosa
import scipy.signal as signal
import soundfile as sf

#EQUALIZER
# Peaking EQ filter (bell-shaped)
def peaking_eq_filter(data, center_freq, fs, gain_db, q_factor):
	# Convert gain from dB
	gain = 10**(gain_db / 20.0)
	
	# Design the filter using the biquad peak filter formula
	b, a = signal.iirpeak(center_freq / (0.5 * fs), q_factor)
	
	# Apply gain to the filter coefficients
	b *= gain
	
	# Apply the filter
	y = signal.lfilter(b, a, data)
	return y

# Apply equalizer to a metronome sound
def apply_equalizer(audio, fs, low_gain, mid_gain, high_gain):
	# Apply bell-shaped EQs to different frequency bands
	low_band = peaking_eq_filter(audio, 100, fs, low_gain, q_factor=1)
	mid_band = peaking_eq_filter(audio, 2000, fs, mid_gain, q_factor=1)
	high_band = peaking_eq_filter(audio, 7000, fs, high_gain, q_factor=1)
	
	# Combine all bands back together
	equalized_audio = low_band + mid_band + high_band
	return equalized_audio

#COMPRESSION
def apply_compressor(audio, sr, threshold=-20.0, ratio=4.0, attack=5.0, release=50.0):
	# Convert threshold from dB to linear scale
	threshold_linear = 10 ** (threshold / 20.0)
	
	# Calculate attack and release in samples
	attack_samples = int(attack * sr / 1000)  # Convert ms to samples
	release_samples = int(release * sr / 1000)  # Convert ms to samples
	
	# Create an array to hold the compressed audio
	compressed_audio = np.zeros(len(audio))
	
	# Initialize variables for gain
	gain = 1.0
	envelope = 0.0
	
	for i in range(len(audio)):
		# Calculate the current sample's amplitude
		sample_amplitude = np.abs(audio[i])
		
		# Check if the amplitude exceeds the threshold
		if sample_amplitude > threshold_linear:
			# Calculate the gain reduction
			gain_reduction = 1 - (1 / ratio) * (threshold_linear / sample_amplitude)
			gain = 1 - gain_reduction
			# Attack
			envelope = max(envelope - 1.0 / attack_samples, gain)
		else:
			# Release
			envelope = min(envelope + 1.0 / release_samples, 1.0)
			
		# Apply the current gain to the sample
		compressed_audio[i] = audio[i] * envelope
		
	return compressed_audio

#REVERB
def add_reverb(audio, sr, decay_time=2.0, mix_level=50, damping_freq=5000, pre_delay=20):
	"""
	Add reverb to an audio signal.

	Parameters:
	- audio: Input audio signal (1D numpy array).
	- sr: Sample rate of the audio.
	- decay_time: Duration of the reverb tail in seconds.
	- mix_level: Level of reverb effect in the mix (0 to 100).
	- damping_freq: Frequency at which the reverb tail is damped in Hz.
	- pre_delay: Time before the reverb effect starts in milliseconds.

	Returns:
	- Reverb audio signal.
	"""
	# Convert pre_delay from milliseconds to seconds
	pre_delay_seconds = pre_delay / 1000.0
	
	# Create an impulse response (IR) for a simple room reverb
	num_samples = int(sr * decay_time)  # Length of IR based on decay time
	ir = np.zeros(num_samples)
	
	# Fill the IR with an exponential decay and damping
	t = np.linspace(0, decay_time, num_samples)
	decay = np.exp(-t * (1.0 / decay_time))  # Exponential decay
	# Damping
	damping = np.exp(-damping_freq * t)  # Simple damping
	ir = decay * damping
	
	# Apply pre-delay
	ir = np.pad(ir, (int(pre_delay_seconds * sr), 0), 'constant')
	
	# Apply convolution with the impulse response
	reverb_audio = np.convolve(audio, ir, mode='full')[:len(audio)]
	
	# Normalize mix level to 0-1
	mix_level_normalized = mix_level / 100.0
	
	# Mix the original audio and reverb audio
	output_audio = (1 - mix_level_normalized) * audio + mix_level_normalized * reverb_audio[:len(audio)]
	
	return output_audio