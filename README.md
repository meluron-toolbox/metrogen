# Metrogen

Metrogen is a python-based tool designed to create customized metronome for musicians and educators. It enables users to specify parameters such as beats per minute (BPM), time signature, emphasized beats, **scale**, and duration to generate metronome tracks tailored to specific needs. Since we take inputs from a text file (see below), one can generate any number of metronome in a single function call. One can write script to populate the text file and get the metronome. Feel free to raise an issue to request for more features.

[Try it out](https://metrogen.streamlit.app/) <br><br>

## I/O 
### Input
<table border="1" width="600">
	<tr>
		<th>Variable</th>
		<th>Description</th>
	</tr>
	<tr>
		<td>BPM</td>
		<td>Beats per minute [default: 120]</td>
	</tr>
	<tr>
		<td>Time Signature</td>
		<td>Time signature of the metronome [default: 4/4]</td>
	</tr>
	<tr>
		<td>Strong Beat</td>
		<td>Which beats (comma separated) should be emphasized [default: 1,2]</td>
	</tr>
	<tr>
		<td>Suppress Beat</td>
		<td>Which beats (comma separated) should be removed [default: 4]</td>
	</tr>
	<tr>
		<td>Scale</td>
		<td>Tuning of the metronome [default: c#]</td>
	</tr>
	<tr>
		<td>Duration</td>
		<td>Total duration of the metronome in minutes [default: 1]</td>
	</tr>
	
</table>

### Output
<table border="1" width="600">
	<tr>
		<th>Variable</th>
		<th>Description</th>
	</tr>
	<tr>
		<td>Rendered audio file</td>
		<td>Based on the inputs, an audio file will get rendered and saved in <b>./outputs</b> folder</td>
	</tr>
</table>

<b>Output file naming convention:</b> BPM-TimeSignature-StrongBeat-Scale-Duration.wav

## Setup

### Clone the repository
```
git clone git@github.com:meluron-toolbox/metrogen.git
```

### Create a virtual environment and install dependencies
```
python3 -m venv venv
```
```
source ./venv/bin/activate
```
```
pip install -r requirements.txt
```
## Run web application 
### Run the python webapp module
```
python -m streamlit run ./source/webapp.py
```

## Run the code

### Provide input variables
Add input variables (space separated) to the ./inputs/input_vars.txt file in same order as mentioned in the input table above. <br>
-- Example: 120 4/4 1,2 D# 5 <br>
-- Example: 140 3/4 1,3 F 7 <br>
Save the text file. <br>

**Note:** Each line of the text file will be considered as a separate input to the metronome generator and will result in mutiple audio renders.

### Run the python main module
```
python ./source/main.py
```

### Run the command line module
Coming soon!

### Contact Me
Incase of any query or request:<br>
Email: ankit0[dot]anand0[at]gmail[dot]com <br>


### Credits
<a href="https://www.flaticon.com/free-icons/tempo" title="Tempo icons">Tempo icons created by Freepik - Flaticon</a>
