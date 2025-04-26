"""
Author: Ankit Anand
"""


import librosa
import numpy as np
import matplotlib.pyplot as plt
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

def generate_metronome(bpm:int=120, time_sign:str='4/4', strong_beats:list=[1,2,], suppress_beats:list=[4,], scale:str='C#', duration:int=1, sr:int=22050, api_mode: bool = False):
	"""
	Generate metronome and save it as a wav file.
	Input:
		bpm: Beats per minute
		time_sign: Time signature (e.g., '4/4')
		strong_beat: Which beat should be emphasized (e.g. [1, 2])
		duration: Duration in minutes
		scale: Musical scale (e.g., 'a')
	"""

	
#	extracting values from time_sign
	top_number = int(time_sign.split("/")[0])
	bottom_number = int(time_sign.split("/")[1])
	
#	sample length of audio signal
	N = int(duration * 60 * sr)
	
#	start buffer
	start_buffer = 0.1 # sec
	
#	calculating click positions in seconds
	clicks_timings = np.arange(0+start_buffer, np.floor(N/sr)+start_buffer, (60/bpm)*(4/bottom_number))
	
	
#	calculating frequency from scale
	if scale != "None":
		if scale in ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]:
			scale_hz = librosa.note_to_hz(note=scale+"4") # octave 4
		else:
			scale_hz = librosa.note_to_hz(note=scale+"3") # octave 3
	else:
		scale_hz = librosa.note_to_hz(note="C#"+"4")
	
#	strong beat positions
	strong_beat_timings = []
	if strong_beats:
		for strong_beat in strong_beats:
			strong_beat = int(strong_beat) # list of str to list of int
			strong_beat_timings.append(clicks_timings[strong_beat-1::top_number]) # 1 is subtracted to account for python 0 indexing

#	suppress beats
	if suppress_beats:
		mask = np.ones(len(clicks_timings), dtype=bool)
		for suppress_beat in suppress_beats:
			mask[suppress_beat-1::top_number] = False
		for strong_beat in strong_beats:
			mask[strong_beat-1::top_number] = False
		clicks_timings = clicks_timings[mask,...]

		
#	creating clicks based on click positions

	
	if scale != "None":
		x = librosa.clicks(times=clicks_timings, sr=sr, click_duration=1, length=N, click_freq=scale_hz)
		x += 0.3*librosa.clicks(times=clicks_timings, sr=sr, click_duration=1, length=N, click_freq=scale_hz*(2))
	else:
		x = librosa.clicks(times=clicks_timings, sr=sr, click_duration=0.2, length=N, click_freq=scale_hz)
		
#		x = librosa.clicks(times=clicks_timings, sr=sr, click_duration=0.3, length=N, click_freq=scale_hz)
	
#	creating clicks based on strong beat positions
	X = np.zeros(N) # To hold strong beat positions in seconds
	for i in range(len(strong_beat_timings)):
		X += 0.3*librosa.clicks(times=strong_beat_timings[i], sr=sr, click_duration=0.2, length=N, click_freq=scale_hz)
		X += 0.8*librosa.clicks(times=strong_beat_timings[i], sr=sr, click_duration=0.2, length=N, click_freq=scale_hz/2)
#		X += 0.8*librosa.clicks(times=strong_beat_timings[i], sr=sr, click_duration=0.2, length=N, click_freq=scale_hz/4)
		#	adding another layer of harmonics
		#			X += 0.01 * librosa.clicks(times=strong_beat_timings[::top_number], sr=sr, click_duration=2, length=N, click_freq=scale_hz*(1/2))
		#			X += 0.005 * librosa.clicks(times=strong_beat_timings[::top_number], sr=sr, click_duration=2, length=N, click_freq=scale_hz*(1/4))
		#			X += 0.001 * librosa.clicks(times=strong_beat_timings[i], sr=sr, click_duration=2, length=N, click_freq=scale_hz*(1/8))

#		#	add emphasis on the first beat of the cycle
		if scale != "None":
			X += 0.02 * librosa.clicks(times=strong_beat_timings[::top_number], sr=sr, click_duration=2, length=N, click_freq=scale_hz*(3))
			X += 0.04 * librosa.clicks(times=strong_beat_timings[::top_number], sr=sr, click_duration=2.5, length=N, click_freq=scale_hz*(2))
			X += 0.08 * librosa.clicks(times=strong_beat_timings[::top_number], sr=sr, click_duration=3, length=N, click_freq=scale_hz*(1))

	metro_audio = 0.3*x+0.6*X # making the volume of the strong beat louder than the normal beats
		
	if api_mode:
		return metro_audio, sr
	else:
		#		saving the output file in the outputs directory
		sf.write(file=f"./outputs/{bpm}-{"by".join(time_sign.split("/"))}-{"_".join(strong_beats)}-{scale}-{int(duration)}min.wav", data=metro_audio, samplerate=sr)
		return None
	