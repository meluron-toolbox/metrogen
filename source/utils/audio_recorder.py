"""
Author: Ankit Anand
"""

import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt
import io
from scipy.io import wavfile
import librosa
import numpy as np
from numba import jit
import warnings

# Suppress the WavFileWarning
warnings.filterwarnings("ignore", message="Reached EOF prematurely")


@jit(nopython=True)
def compute_local_average(x, M):
	L = len(x)
	local_average = np.zeros(L)
	for m in range(L):
		a = max(m - M, 0)
		b = min(m + M + 1, L)
		local_average[m] = (1 / (2 * M + 1)) * np.sum(x[a:b])
	return local_average

def get_spectral_novelty(x, sr):
	N, H = 512, 160
	gamma = 10
	M = 0
	norm = True
	X = librosa.stft(x, n_fft=N, hop_length=H, win_length=N, window='hann')
	
	sr_X = sr / H
	Y = np.log(1 + gamma * np.abs(X))
	Y_diff = np.diff(Y)
	Y_diff[Y_diff < 0] = 0
	novelty_spectrum = np.sum(Y_diff, axis=0)
	novelty_spectrum = np.concatenate((novelty_spectrum, np.array([0.0])))
	if M > 0:
		local_average = compute_local_average(novelty_spectrum, M)
		novelty_spectrum = novelty_spectrum - local_average
		novelty_spectrum[novelty_spectrum < 0] = 0.0
	if norm:
		max_value = max(novelty_spectrum)
		if max_value > 0:
			novelty_spectrum = novelty_spectrum / max_value
	return novelty_spectrum, sr_X, Y

# Parameters
def get_settings_from_clap(audio):

	# Convert audio_data into a NumPy array
	audio_bytes = io.BytesIO(audio)  # Convert bytes to a BytesIO object
	SR, audio = wavfile.read(audio_bytes)  # Read as a NumPy array
	
	if audio.ndim == 2:
		audio = np.mean(audio, axis=1)
		
	# Normalize the NumPy array to the range [-1, 1]
	audio = audio.astype(np.float32) / np.max(np.abs(audio))
	audio = np.array(audio)
	
	# Get the novelty function
	nov, sr_nov, Y = get_spectral_novelty(audio, SR)
	
	# Peak finder
	peaks, props = signal.find_peaks(nov, prominence=0.1, distance=int(0.05*sr_nov)) # 0.1 sec
	peaks = peaks / sr_nov
	proms = props["prominences"]
	avg_proms = np.mean(proms)
	
	# Find time differences between events
	time_differences = peaks[1:] - peaks[:-1]
	
	# Calculate the minimum time difference
	min_time_diff = np.min(time_differences)
	
	# Round to a resolution of half the minimum time difference
#	beat_rel_lengths = np.round(time_differences / (min_time_diff / 2)).astype("int")
#	beat_rel_lengths = np.round(time_differences / (min_time_diff)).astype("int")
	beat_rel_lengths = np.ones_like(time_differences)
#	tol = 0.1 #0.1 to 0.2
#	tol = np.random.choice([0.1, 0.2], p=[0.3, 0.7])
	tol = 0.15
	resolution = 1
	for i in range(len(time_differences)):
		ratio = time_differences[i]/min_time_diff
		remainder = ratio%1
#		print(time_differences[i], ratio, remainder)
		if np.abs(remainder - 0.5) < tol:
			beat_rel_lengths[i] = np.floor(ratio) + 0.5
			resolution = 0.5 #setting the resolution to 0.5 for later stages
		else:
			beat_rel_lengths[i] = np.round(ratio)
	
#	beat_rel_lengths = custom_round(time_differences / min_time_diff)
	
	# Calculate BPM and time signature
	bpm = np.round(60. / min_time_diff)
	
	if resolution == 0.5:
		time_sign = str(int(np.sum(beat_rel_lengths))*2) + "/8"
		beat_rel_lengths *= 2
	else:
		time_sign = str(int(np.sum(beat_rel_lengths))) + "/4"
	
	
	#we will use relative prominences as opposed to absolute
	rel_proms = proms[1:] - proms[0:-1]
	rel_proms = np.concatenate((np.atleast_1d(proms[0]), rel_proms))
	
	# Define thresholds
	initial_threshold = 0.4
	weak_threshold = -0.1
	strong_threshold = 0.1
	
	# Initialize an empty list for strong beat indices
	strong_beats_idx = []
	
	# Check the first beat using absolute prominence
	if proms[0] > initial_threshold:
		strong_beats_idx.append(0)  # The first beat is strong
		previous_strong = True
	else:
		previous_strong = False
		
	# Iterate through the rest of the relative prominences
	for i in range(1, len(rel_proms)):
		if rel_proms[i] < weak_threshold:
			previous_strong = False  # Mark as weak if prominence is less than -0.2
		elif rel_proms[i] > strong_threshold:
			strong_beats_idx.append(i)  # Mark as strong if prominence change is greater than +0.2
			previous_strong = True
		else:
			if previous_strong:
				strong_beats_idx.append(i)  # Keep the previous state (strong) if no threshold crossed
	
#	strong_beats_idx = np.where(proms > 0.6)[0]
#	print("\n", proms, rel_proms, strong_beats_idx)
	

	all_beat_numbers = np.arange(1, (int(time_sign.split("/")[0]) + 1))
		
	clapped_beat_numbers = np.cumsum(np.insert(beat_rel_lengths, 0, 1)).astype("int")
	
	strong_beats = clapped_beat_numbers[strong_beats_idx]
	strong_beats = strong_beats[strong_beats < int(time_sign.split("/")[0])]
	
	suppress_beats = np.array([], dtype="int")
	for a in all_beat_numbers:
		if a not in clapped_beat_numbers:
			suppress_beats = np.append(suppress_beats, a)
	
#	if resolution == 0.5:
#		strong_beats *= 2
#		suppress_beats *= 2
	
	strong_beats = ",".join(strong_beats.astype("str"))
	suppress_beats = ",".join(suppress_beats.astype("str"))
	
	
#	print("bpm", bpm, "time_sign", time_sign, "beat_rel_lengths", beat_rel_lengths, "all_beat_numbers", all_beat_numbers, "clapped_beat_numbers", clapped_beat_numbers, "strong_beats", strong_beats, "suppress_beats", suppress_beats)
	
#	Plotting the audio signal
#	ts = np.arange(Y.shape[1]) * (1/sr_nov)
#	fs = np.arange(Y.shape[0]) * (SR/512)
#	plt.figure()
#	#plt.plot(np.arange(len(recorded_audio)) / SR, recorded_audio)
#	plt.imshow(Y, aspect="auto", cmap="gray_r", origin="lower", extent=[ts[0], ts[-1], fs[0], fs[-1]])
#	plt.plot(np.arange(len(nov))/sr_nov, nov*1000, 'b')
#	plt.vlines(peaks, 0, 1000, 'r')
#	plt.title("Recorded Audio Signal")
#	plt.xlabel("Time (s)")
#	plt.ylabel("Amplitude")
#	plt.grid()
#	plt.show()
#	plt.save_fig("../../../../../Desktop/test.png", format="png")

	return int(bpm), str(time_sign), str(strong_beats), str(suppress_beats)

	
#get_settings_from_clap(duration_sec=3)
