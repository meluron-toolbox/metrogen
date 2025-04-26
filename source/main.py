"""
Author: Ankit Anand
"""


from utils.input_vars_parser import input_vars_parser
from utils.generate_metronome import generate_metronome

#global params
inputs_dp = "./inputs/" #inputs directory path
outputs_dp = "./outputs/" #outputs directory path


def main(input_vars_fp):

#	input variables parser
	input_vars = input_vars_parser(input_vars_fp, vars_type=[int, str, list, str, float]) # for list you need to manage the element dtype explicitely
	
#	generate metronome
	for i in range(len(input_vars)):
		print(f"> Rendering: {input_vars[0]}")
		generate_metronome(*input_vars[i])

if __name__ == "__main__":
	main("./inputs/input_vars.txt")