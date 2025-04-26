"""
Author: Ankit Anand
"""


import librosa
import numpy as np
import matplotlib.pyplot as plt
import soundfile as sf
import scipy.signal as signal
from pprint import pprint as pp
import sys
sys.path.append(".")
from utils.theka import get_theka, get_thekas_list
from utils.filters import band_pass_filter
import random

def generate_metronome(bpm: int = 120, time_sign: str = '4/4', strong_beats: list = [1, 2], suppress_beats: list = [4], scale: str = 'C#', duration: int = 1, sr: int = 22050, temperature:float=0., api_mode: bool = False):
	"""
	Generate metronome and save it as a wav file, with changing strong and suppress beats every measure.
	"""
	
	# Extract values from time signature
	top_number = int(time_sign.split("/")[0])  # Number of beats in a measure
	bottom_number = int(time_sign.split("/")[1])  # Note value representing one beat
	
	# Total number of samples in the audio signal
	N = int(duration * 60 * sr)
	
	# Sample length of a measure
	N_measure = int((60 / bpm) * top_number * sr)
	
	# Get theka list
	strong_beats_thekas, suppress_beats_thekas = get_thekas_list(time_sign, strong_beats, suppress_beats, temperature=temperature)
	
	# Calculate click positions in seconds
	clicks_timings = np.arange(0, np.floor(N / sr), (60 / bpm) * (4 / bottom_number))
	
	# Calculating frequency from scale
	if scale != "None":
		scale_hz = librosa.note_to_hz(note=f"{scale}4") if scale in ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"] else librosa.note_to_hz(note=f"{scale}3")
	else:
		scale_hz = librosa.note_to_hz(note="C#4")
		
	# Initialize arrays to hold metronome sound
	x = np.zeros(N)
	X = np.zeros(N)
	
	# Lists to hold all click timings
	clicks_timings_full = []  # For normal clicks
	strong_beat_timings_full = []  # For strong beats
	
	# Iterate over each measure
	num_measures = len(clicks_timings) // top_number
	theka_counter = 0
	start_theka = False
	main_sequence_repeat_prob = 1-temperature
	theka_probs = [(1-main_sequence_repeat_prob)/2, (1-main_sequence_repeat_prob)/2, main_sequence_repeat_prob]
	first_strong_beat_indices = []
	
	for i in range(num_measures):  # i is measure number
		start_idx = i * top_number
		end_idx = (i + 1) * top_number
	
		# Change strong and suppress beats per measure
		if i % top_number == 0:
			current_strong_beats, current_suppress_beats = strong_beats, suppress_beats
		else:
			if theka_counter == 0:
				start_theka = random.choices(["True", "False", "Original"], theka_probs, k=1)[0]
			if start_theka == "Original":
				current_strong_beats, current_suppress_beats = strong_beats, suppress_beats
			elif start_theka == "True":
				current_strong_beats, current_suppress_beats = get_theka(strong_beats_thekas, suppress_beats_thekas, current_strong_beats, current_suppress_beats)
				theka_counter += 1
				if theka_counter == top_number:
					theka_counter = 0
					start_theka = False

		# Calculate strong beat timings for this measure
		strong_beat_timings = [clicks_timings[start_idx + strong_beat - 1] for strong_beat in current_strong_beats]
#		print(current_strong_beats, current_suppress_beats)
		# Append the index of the first strong beat of the current measure
		if len(current_strong_beats) > 0:
			first_strong_beat_indices.append(len(strong_beat_timings_full))  # Capture the index before extending
			
		# Mask out suppress beats/strong beats for this measure
		mask = np.ones(end_idx - start_idx, dtype=bool)
		for suppress_beat in current_suppress_beats:
			mask[suppress_beat - 1] = False
		for strong_beat in current_strong_beats:
			mask[strong_beat - 1] = False
			
		clicks_in_measure = clicks_timings[start_idx:end_idx][mask]
	
		# Append timings to the full lists
		clicks_timings_full.extend(clicks_in_measure)
		strong_beat_timings_full.extend(strong_beat_timings)
	
	strong_beat_timings_full = np.array(strong_beat_timings_full)
	# Generate clicks for normal beats
	if scale != "None":
		x = librosa.clicks(times=clicks_timings_full, sr=sr, click_duration=1, length=N, click_freq=scale_hz)
		x += 0.3*librosa.clicks(times=clicks_timings_full, sr=sr, click_duration=1, length=N, click_freq=scale_hz*(2))
	else:
		x = librosa.clicks(times=clicks_timings_full, sr=sr, click_duration=0.2, length=N, click_freq=scale_hz)
		
	# Generate strong beat clicks

	X += 0.3*librosa.clicks(times=strong_beat_timings_full, sr=sr, click_duration=0.2, length=N, click_freq=scale_hz)
	X += 0.8*librosa.clicks(times=strong_beat_timings_full, sr=sr, click_duration=0.2, length=N, click_freq=scale_hz/2)
	
		# Add emphasis on the first beat of the cycle
	if scale != "None":
		alpha = 4
		X += alpha*0.02 * librosa.clicks(times=strong_beat_timings_full[first_strong_beat_indices], sr=sr, click_duration=2, length=N, click_freq=scale_hz*(3))
		X += alpha*0.04 * librosa.clicks(times=strong_beat_timings_full[first_strong_beat_indices], sr=sr, click_duration=2.5, length=N, click_freq=scale_hz*(2))
		X += alpha*0.08 * librosa.clicks(times=strong_beat_timings_full[first_strong_beat_indices], sr=sr, click_duration=3, length=N, click_freq=scale_hz*(1))
	
	metro_audio = 0.3*x+0.6*X # making the volume of the strong beat louder than the normal beats
	metro_audio = np.concatenate([np.zeros(int(0.1 * sr)), 0.3 * x + 0.6 * X]) # adding 0.1 sec of start pause
	# Return audio for API mode or save as WAV
	if api_mode:
		return metro_audio, sr
	else:
		# Save the output file
		sf.write(file=f"../../outputs/{bpm}-{time_sign.replace('/', 'by')}-{scale}-{duration}min.wav", data=metro_audio, samplerate=sr)
		return None
	

if __name__ == "__main__":
	generate_metronome(300, "10/4", [1,2,3,6], [5,6,7], "C", 3, 22050, 0.6, False)