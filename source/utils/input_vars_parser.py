"""
Author: Ankit Anand
"""

import os

def input_vars_parser(input_vars_fp, vars_type=None):
	assert input_vars_fp.endswith(".txt"), ".txt file only supported"
	
	with open(input_vars_fp, "r") as f:
		content = f.read()
	
	multiline_args = [args.split(" ") for args in content.split("\n")]
	
	for args in multiline_args:
		assert len(args) == len(vars_type), "length of arguments do not match with length of variable type"
		for i in range(len(vars_type)):
			if vars_type[i] == list:
				args[i] = args[i].split(",")
			else:
				args[i] = vars_type[i](args[i])
				
	return multiline_args
