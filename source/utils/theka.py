"""
Author: Ankit Anand

Objective: This will take a strong beat and suppress beat sequence to randomise it.

Steps:
1. To get the theka (a modified version of strong_beats and suppress_beats
"""

import numpy as np
from scipy.spatial.distance import jaccard

from pprint import pprint as pp
import random

# Function to convert each array to a binary vector representation
def to_binary_vector(arr, all_elements):
	return np.array([1 if beat in arr else 0 for beat in all_elements])

# Function to calculate average Jaccard similarity
def average_jaccard_similarity(arr, others, all_elements):
	arr_binary = to_binary_vector(arr, all_elements)
	return np.mean([1 - jaccard(arr_binary, to_binary_vector(other, all_elements)) for other in others])


def get_thekas_list(time_sign: str, strong_beats: list, suppress_beats: list, temperature: float = 0):
	assert 0 <= temperature <= 1, "Temperature out of range"
	max_thekas = 50  # Max thekas to consider for random variations
	
	strong_beats = np.array(strong_beats)
	suppress_beats = np.array(suppress_beats)
	len_strong_beats = len(strong_beats)
	len_suppress_beats = len(suppress_beats)
	
	strong_beats_thekas = []  # Hold all generated strong beats
	suppress_beats_thekas = []  # Hold all generated suppress beats
	
	# Insert the actual strong and suppress beats at the start
	strong_beats_thekas.append(strong_beats.copy())
	suppress_beats_thekas.append(suppress_beats.copy())
	
	unique_strong_beats = {tuple(strong_beats)}  # Track unique strong beats
	unique_suppress_beats = {tuple(suppress_beats)}  # Track unique suppress beats
	
	variation_count = int(temperature * max_thekas)
	max_possible_variations = max_thekas #min(2 ** len_strong_beats, 2 ** len_suppress_beats, variation_count)
	
	max_attempts = 100  # Number of failed attempts before stopping the process
	
	if temperature != 0:
		attempts = 0
		while len(unique_strong_beats) < max_possible_variations and attempts < max_attempts:
			# Create variations of strong beats
			modified_strong_beats = strong_beats.copy()
			modified_suppress_beats = suppress_beats.copy()
			
			# Determine the number of beats to randomly modify
			strong_modification_count = random.randint(0, len_strong_beats // 2)
			suppress_modification_count = random.randint(0, len_suppress_beats // 2)
			
			# Generate strong beat variations (deleting and inserting beats)
			for _ in range(strong_modification_count):
				if random.choice([True, False]):
					# Deletion: Remove a strong beat, excluding the first one
					if len(modified_strong_beats) > 1:
						beat_to_change = random.choice(modified_strong_beats[1:])
						modified_strong_beats = np.delete(modified_strong_beats, np.where(modified_strong_beats == beat_to_change))
				else:
					# Insertion: Add a new beat at integer positions (+1 or +2 steps)
					new_beat = random.choice(modified_strong_beats) + random.choice([1, 2])
					if new_beat <= int(time_sign.split("/")[0]):  # Adjust to valid range based on time signature
						modified_strong_beats = np.append(modified_strong_beats, new_beat)
					
			# Generate suppress beat variations (deleting and inserting beats)
			for _ in range(suppress_modification_count):
				if random.choice([True, False]):
					# Deletion: Remove a suppress beat
					if len(modified_suppress_beats) > 0:
						beat_to_change = random.choice(modified_suppress_beats)
						modified_suppress_beats = np.delete(modified_suppress_beats, np.where(modified_suppress_beats == beat_to_change))
				else:
					# Insertion: Add a new suppress beat at integer positions (+1 or +2 steps)
					new_beat = random.choice(modified_suppress_beats) + random.choice([1, 2])
					if new_beat <= 10:  # Adjust to valid range based on time signature
						modified_suppress_beats = np.append(modified_suppress_beats, new_beat)
					
			# Ensure the generated strong and suppress beats maintain a coherent rhythm
			modified_strong_beats = np.unique(modified_strong_beats)
			modified_suppress_beats = np.unique(modified_suppress_beats)
			
			# Add only if the new variation is unique
			if tuple(modified_strong_beats) not in unique_strong_beats:
				strong_beats_thekas.append(modified_strong_beats)
				unique_strong_beats.add(tuple(modified_strong_beats))
			else:
				attempts += 1  # Increment attempt counter for failed uniqueness
				
			if tuple(modified_suppress_beats) not in unique_suppress_beats:
				suppress_beats_thekas.append(modified_suppress_beats)
				unique_suppress_beats.add(tuple(modified_suppress_beats))
			else:
				attempts += 1  # Increment attempt counter for failed uniqueness
				
			if attempts >= max_attempts:
#				print(f"Max attempts ({max_attempts}) reached. Stopping further generation.")
				break			
			
			# Arranging the beats sequence in order of similarity

			all_strong_beats = sorted(set(np.concatenate(strong_beats_thekas)))
			all_suppress_beats = sorted(set(np.concatenate(suppress_beats_thekas)))
			strong_beats_thekas = sorted(strong_beats_thekas, key=lambda x: average_jaccard_similarity(x, strong_beats_thekas, all_strong_beats), reverse=True)
			suppress_beats_thekas = sorted(suppress_beats_thekas, key=lambda x: average_jaccard_similarity(x, strong_beats_thekas, all_suppress_beats), reverse=True)

			
		return strong_beats_thekas, suppress_beats_thekas
	else:
		# If temperature is 0, only use the actual strong and suppress beats
		strong_beats_thekas.append(strong_beats)
		suppress_beats_thekas.append(suppress_beats)
		
	
	return strong_beats_thekas, suppress_beats_thekas

#def get_theka(strong_beats_thekas:list, suppress_beats_thekas:list):
#	probs_strong_beats_thekas = [0.7] + [(0.3)/(len(strong_beats_thekas)-1)] * (len(strong_beats_thekas)-1)
#	probs_suppress_beats_thekas = [0.7] + [(0.3)/(len(suppress_beats_thekas)-1)] * (len(suppress_beats_thekas)-1)
#	selected_strong_theka = random.choices(strong_beats_thekas, weights=probs_strong_beats_thekas, k=1)[0]
#	selected_suppress_theka = random.choices(suppress_beats_thekas, weights=probs_suppress_beats_thekas, k=1)[0]
#	return selected_strong_theka, selected_suppress_theka

def get_theka(strong_beats_thekas: list, suppress_beats_thekas: list, last_selected_strong: np.ndarray, last_selected_suppress: np.ndarray):
	# Ensure the last selected beats are in the corresponding lists
	assert any(np.array_equal(last_selected_strong, theka) for theka in strong_beats_thekas), "Last selected strong theka must be in the list."
	assert any(np.array_equal(last_selected_suppress, theka) for theka in suppress_beats_thekas), "Last selected suppress theka must be in the list."
	
	# Calculate probabilities for strong beats
	probs_strong_beats_thekas = [0.5]  # First element has a fixed probability of 0.5
	
	# Find index of the last selected strong theka
	last_strong_index = next(i for i, theka in enumerate(strong_beats_thekas) if np.array_equal(theka, last_selected_strong))
	
	# Calculate probabilities for other strong beats based on the last selected
	for i, theka in enumerate(strong_beats_thekas):
		if i == last_strong_index:
			continue
		# Calculate the probability inversely related to its distance from the last selected
		distance = np.abs(i - last_strong_index)
		prob = max(0.1, (0.5 - 0.1 * distance))  # Ensure a minimum probability
		probs_strong_beats_thekas.append(prob)
		
	# Normalize probabilities to sum to 1
	probs_strong_beats_thekas = np.array(probs_strong_beats_thekas)
	probs_strong_beats_thekas /= probs_strong_beats_thekas.sum()
	
	# Calculate probabilities for suppress beats
	probs_suppress_beats_thekas = [0.5]  # First element has a fixed probability of 0.5
	
	# Find index of the last selected suppress theka
	last_suppress_index = next(i for i, theka in enumerate(suppress_beats_thekas) if np.array_equal(theka, last_selected_suppress))
	
	# Calculate probabilities for other suppress beats based on the last selected
	for i, theka in enumerate(suppress_beats_thekas):
		if i == last_suppress_index:
			continue
		# Calculate the probability inversely related to its distance from the last selected
		distance = np.abs(i - last_suppress_index)
		prob = max(0.1, (0.5 - 0.1 * distance))  # Ensure a minimum probability
		probs_suppress_beats_thekas.append(prob)
		
	# Normalize probabilities to sum to 1
	probs_suppress_beats_thekas = np.array(probs_suppress_beats_thekas)
	probs_suppress_beats_thekas /= probs_suppress_beats_thekas.sum()
	
	# Select a theka based on the calculated probabilities
	selected_strong_theka = random.choices(strong_beats_thekas, weights=probs_strong_beats_thekas, k=1)[0]
	selected_suppress_theka = random.choices(suppress_beats_thekas, weights=probs_suppress_beats_thekas, k=1)[0]
	
	return selected_strong_theka, selected_suppress_theka


if __name__ == "__main__":
	strong_beats_thekas, suppress_beats_thekas = get_thekas_list("5/4", [1,2,5,8,9,10], [1,2], temperature=0.50)
	selected_strong_theka, selected_suppress_theka = get_theka(strong_beats_thekas, suppress_beats_thekas)
	pp(strong_beats_thekas)
	pp(suppress_beats_thekas)
#	pp(selected_strong_theka)
#	pp(selected_suppress_theka)
#	print(random.randint(0, 10))
	