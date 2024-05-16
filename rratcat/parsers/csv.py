import copy
import csv
import os

import numpy as np

from collections import defaultdict
from pathlib import Path

from ..tools.info import *
from ..tools.table_maker import getDefaultEntryDict, setReferencedKey, wrapped_ufloat_fromstr, setPosition, freqVarDefaultDict

UNKOWN_VARIABLE_FREQ = np.nan
defaultInformation = {
	'Cui2017.csv': (UNKOWN_VARIABLE_FREQ, "Cui et al. 2017"),
	'Deneva2016.csv': (ARECIBO_DRIFT_FREQ, "Deneva et al. 2016"),
	'Deneva2024_manual.csv': (ARECIBO_DRIFT_FREQ, "Deneva et al. (2024+)"),
	'DongCHIMEDetections.csv': (CHIME_FREQ, "Dong et al. 2023"),
	'DongCHIMENoLocalisation.csv': (CHIME_FREQ, "Dong et al. 2023"),
	'DongCHIMETimed.csv': (CHIME_FREQ, "Dong et al. 2023"),
	'GoodCHIME2021.csv': (CHIME_FREQ, "Good et al. 2021"),
	'RanePH.csv': (PARKES_FREQ, "Rane et al. 2015"),
	'ZhouGPPS.csv': (FAST_FREQ, "Zhou et al. 2023"),
	'PatelPALFA2.csv': (ARECIBO_FREQ, "Patel et al. 2018"),
	'McKenna2023.csv': (ILOFAR_FREQ, "McKenna et al. 2023"),
	'McKennaTiming2023.csv': (ILOFAR_FREQ, "McKenna et al. 2023"),
	'UNKNOWN': (np.nan, 'UNKNOWN')
}


def getCSVFrequency(csvName: str) -> float:
	if csvName in defaultInformation:
		return defaultInformation[csvName][0]

	print (f"Unknown input CSV {csvName}.")
	return np.nan

def getCSVCitation(csvName: str) -> float:
	if csvName in defaultInformation:
		return defaultInformation[csvName][1]

	print (f"Unknown input CSV {csvName}.")
	return f"UNNOWN-{csvName}"

def defaultCsvReader(path: str) -> list[dict]:
	loadedDicts = []
	with open(path, 'r') as ref:
		reader = csv.DictReader(ref)
		for row in reader:
			loadedDicts.append(row)

	return loadedDicts


def getNumSavedCsvs(additional: list[str] = [], loadDefaults: bool = True):
	counter = len(additional)

	if loadDefaults:
		for csvPath in os.listdir(os.path.join(Path(__file__).parents[1], "data")):
			if csvPath.endswith(".csv"):
				counter += 1

	return counter

def getSavedCsvs(additional: list[str] = [], loadDefaults: bool = True) -> list[dict]:
	working = []
	for csvPath in additional:
		working.append(csvPath, defaultCsvReader(csvPath))

	if loadDefaults:
		basePath = os.path.join(Path(__file__).parents[1], "data")
		for csvPath in os.listdir(basePath):
			if csvPath.endswith(".csv"):
				workingPath = os.path.join(basePath, csvPath)
				working.append((csvPath, defaultCsvReader(workingPath)))

	output = []
	for csvsource, entries in working:
		freq = getCSVFrequency(csvsource)
		cite = getCSVCitation(csvsource)
		defaultFreqDict = getDefaultEntryDict(freq)
		if np.isnan(freq) and 'Frequency' in entries[0]:
			frequencies = set([int(e['Frequency']) for e in entries])
			for f in frequencies:
				defaultFreqDict.update(getDefaultEntryDict(f))

		source = csvsource.rstrip('.csv')
		working = defaultdict(lambda: {})
		for entry in entries:
			workingDict = copy.deepcopy(defaultFreqDict)
			positionParsed = False
			if 'Frequency' in entry:
				freq = entry['Frequency']
			for (key, val) in entry.items():
				if key in ['RA', 'DEC']:
					if not positionParsed:
						positionParsed = True
						workingDict = setPosition(workingDict, entry['RA'], entry['DEC'], cite)
				elif key in workingDict or key in freqVarDefaultDict:
					if key in freqVarDefaultDict:
						key = f'{key}_{freq}'
					if isinstance(val, str):
						if val == '--' or key == 'Notes':
							continue
						else:
							if '(' in val:
								val = wrapped_ufloat_fromstr(val)
								workingDict = setReferencedKey(workingDict, f"u_{key}", val.std_dev, cite)
								val = val.n
						if isinstance(workingDict[key], float) and not isinstance(val, float):
							if len(val):
								val = float(val)
					
					workingDict = setReferencedKey(workingDict, key, val, cite)
			working[entry['NAME']].update(workingDict)
		output += [val for val in working.values()]
	
	return output