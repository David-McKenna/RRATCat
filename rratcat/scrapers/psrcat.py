import copy
import psrqpy
import tqdm

import numpy as np

from collections import defaultdict
from joblib import Parallel, delayed

from ..tools.table_maker import setPosition, isSet, setReferencedKey


keysToCheck = {	'JName': None, 
				'RAJ': 'RA',
				'DECJ': "DEC",
				'P0': 'P0',
				'P1': 'P1',
				'DM': 'DM',
			}

def _psrCatPosToErrorStr(coord: str, err: float) -> str:
	splitpos = str(coord).split(':')
	if np.ma.is_masked(err) or float(splitpos[-1]) == 0.0:
		return coord
		
	if (err / float(splitpos[-1])) < 1e-3:
		err = float(f"{err:.2}")

	return ':'.join(splitpos[:-1]) + f":{float(splitpos[-1])} +/- {err}"

def __psrCatApplyUpdate(entry: dict, query: psrqpy.QueryATNF, baseKeys: dict[str, str]):
	name = entry['NAME']

	output = copy.deepcopy(entry)
	updates = {name: []}

	# Skip if there isn't an entry in psrcat
	psrEntry = query.get_pulsar(name)
	if psrEntry is None:
		return output, updates


	for key in baseKeys:
		ourKey = keysToCheck[key]
		ourValue = entry[ourKey]
		ourValue_u = entry[f"u_{ourKey}" + ('s' if 'J' in key else '')]

		catValue = psrEntry[key].value[0]
		catValue_u = psrEntry[f"{key}_ERR"].value[0]

		if key == 'P1':
			catValue *= 1e15
			catValue_u *= 1e15

		if key == 'RAJ':
			# Error is based on last component of the string, if
			# hours, minutes, seconds are all present this does nothing.
			# If only hours and minutes are present, this multiplies 
			# the valur by 60, if only hours are present, it's multiplies
			# by 60 * 60
			numParts = len(str(catValue).split(':'))
			if numParts == 2:
				catValue_u *= 60
			elif numParts == 1:
				catValue_u *= 60 * 60

		# No error, continue without modifications
		if not isSet(catValue_u) or catValue_u == 0.0:
			continue


		if isSet(ourValue_u):
			# Our error is lower than the catalogue error, continue
			if ourValue_u < catValue_u:
				continue

		updates[name].append(f"Updating {key} for {name} ({ourValue}({ourValue_u}) -> {catValue}({catValue_u}))")

		# Psrcat has a lower error, update out entry
		# Handle positions separately
		if key in ['RAJ', 'DECJ']:
			if key == 'DECj':
				continue
			# Re-call the entry to remove scaling from above
			rajStr = _psrCatPosToErrorStr(psrEntry['RAJ'].value[0], psrEntry['RAJ_ERR'].value[0])
			decjStr = _psrCatPosToErrorStr(psrEntry['DECJ'].value[0], psrEntry['DECJ_ERR'].value[0])
			output = setPosition(output, rajStr, decjStr, "PSRCAT")
			continue

		output = setReferencedKey(output, ourKey, catValue, "PSRCAT")
		output = setReferencedKey(output, f"u_{ourKey}", catValue_u, "PSRCAT")

	return output, updates

def psrCatCheckUpdates(cat: dict) -> dict:
	query = psrqpy.QueryATNF(list(keysToCheck.keys()), include_errs = True, include_refs = True)
	baseKeys = [key for key in keysToCheck if keysToCheck[key]]
	
	output = copy.deepcopy(cat)
	updates = defaultdict(lambda: [])

	results = Parallel(n_jobs = 8)(delayed(__psrCatApplyUpdate)(entry, query, baseKeys) for entry in tqdm.tqdm(cat))

	progressIter = tqdm.tqdm(enumerate(results), total = len(cat))
	for idx, (entry, entryUpdates) in progressIter:
		output[idx] = entry
		updates.update(entryUpdates)

	for key, us in sorted(updates.items(), key = lambda x: x[0]):
		if len(us):
			print(f"Updates for {key}:")
			for u in us:
				print(f"\t{u}")


	return output
