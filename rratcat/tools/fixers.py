import copy
import os
import psrqpy

from collections import defaultdict
from pathlib import Path

from .table_maker import isSet, getDefaultEntryDict, mergeReferencedKey, setReferencedKey

global sourceMapping
sourceMapping = {}
def buildSourceMapDict():
	with open(os.path.join(Path(__file__).parents[1], "data", "sourcePairs.txt"), 'r') as ref:
		dupeData = ref.readlines()

	dupeData = [line for line in dupeData if len(line)]
	dupeData = [line.split('#')[0] for line in dupeData]
	dupeData = [line.split() for line in dupeData]

	seenSources = {}
	for priority, entry in enumerate(dupeData):
		if not isinstance(entry, list):
			raise RuntimeError(f"Parsed item {priority} does not seem to have a corresponding pair ({entry}), exiting.")

		mappedSrc = ""
		mappedPriority = 0
		for linePriority, src in enumerate(filter(None, entry)):
			# First source on the current line
			if not linePriority:
				# Case: Source previously parsed, and leads the current line
				if src in seenSources:
					mappedPriority, mappedSrc = seenSources[src]

				# Case: Source leads the current line, but hasn't appeared before, make it the priority mapping
				else:
					mappedSrc = src
					seenSources[src] = (mappedPriority, mappedSrc)
			else:
				# Source is not leading on the line, tie it back to the main source
				seenSources[src] = (mappedPriority, mappedSrc)
			
			mappedPriority += 1

	global sourceMapping
	sourceMapping = copy.copy(seenSources)

def mergeEntries(inputDict: list[dict]) -> dict:
	global sourceMapping
	if not len(sourceMapping):
		buildSourceMapDict()

	mappedSources = [key for key in sourceMapping]
	workToPerform = defaultdict(lambda: [])
	for key in inputDict:
		if key in mappedSources:
			workToPerform[sourceMapping[key][1]].append((sourceMapping[key][0], inputDict[key]))

	mappedDict = {entry['NAME']: copy.copy(entry) for entry in inputDict.values() if entry['NAME'] not in mappedSources}
	for mainSrc, work in workToPerform.items():
		if len(work) == 1 or mainSrc == 'FLAGGED':
			continue
		newEntry = getDefaultEntryDict()
		for __, toMergeEntry in sorted(work, key = lambda x: x[0], reverse = True):
			for key, value in toMergeEntry.items():
				if '_ref' not in key:
					newEntry = setReferencedKey(newEntry, key, value, toMergeEntry[f'{key}_ref'])

		mappedDict[mainSrc] = copy.deepcopy(newEntry)

	listDict = [val for val in mappedDict.values()]
	return listDict


def checkErr(baseErr, newErr):
	if not isSet(baseErr) and not np.isnan(newErr):
		return True
	if np.isnan(newErr):
		return False
	if baseErr < newErr:
		return False

	return True

def checkPsrCat(srcName):
	psrQuery = psrqpy.Pulsar(srcName)	
	basicDict = {}
	try:
		name = psrQuery['NAME']
	except Exception:
		return basicDict


	for key, utputKey in [  ('RAJ', 'RA'),
							('DecJ', 'DEC'),
							('P0', 'P0'),
							('P1', 'P1'),
							('DM', 'DM')]:
		if key in psrQuery and (checkErr(basicDict[f'u_{key}'], psrQuery[f"{key}_ERR"])):
			basicDict = setReferencedKey(basicDict, key, psrQuery[key], psrQuery[f"{key}_REF"] or "UNKNOWN")
			basicDict = setReferencedKey(basicDict, f"u_{key}", psrQuery[f"{key}_ERR"], psrQuery[f"{key}_REF"] or "UNKNOWN")

	return basicDict

	
