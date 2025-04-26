"""
Author: Ankit Anand
"""

import pandas as pd

#def get_settings(selected_ID):
#	df = pd.read_csv("../../assets/rhythm_db.csv")
#	
#	rhythm_list = list(zip(df["RhythmName"].values, df['ID'].values))
#	
#	return rhythm_list,

def get_rhythm_list(rhythm_fp):
	df = pd.read_csv(rhythm_fp)
	rhythm_dict = {}
	for i in range(len(df)):
		rhythm_dict[df.loc[i, "RhythmName"]] =  df.loc[i, "ID"]
	return rhythm_dict


def get_setting(rhythm_fp, rhythm_id):
	df = pd.read_csv(rhythm_fp)
	df = df.where(pd.notnull(df), "None")
	filtered_df = df[df["ID"] == rhythm_id]
	
	#getting the variables
	bpm = filtered_df["BPM"].values[0]
	time_sign = filtered_df["TimeSignature"].values[0]
	strong_beats = filtered_df["StrongBeats"].values[0]
	suppress_beats = filtered_df["SuppressBeats"].values[0]
	scale = filtered_df["Scale"].values[0]
	duration = filtered_df["Duration"].values[0]
	creator = filtered_df["Creator"].values[0]
	
	return bpm, str(time_sign), str(strong_beats), str(suppress_beats), str(scale), duration, str(creator)


#print(get_setting("../../assets/rhythm_db.csv", "R00"))