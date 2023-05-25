import json
import copy

import numpy as np

from astropy.coordinates import SkyCoord

from .helpers import getPage, backupPage
from ..tools.info import CHIME_FREQ
from ..tools.table_maker import getDefaultEntryDict, setReferencedKey, setPositionSkyCoord

citation = "CHIME_FRB_CAT"
def _chimeParseValue(entry: dict, output: dict, entryKey: str, outputKey: str) -> dict:
	val, err = np.nan, np.nan
	if len(entry[entryKey]):
		if entry[entryKey]['value']:
			val = float(entry[entryKey]['value'])
			if ('error_low' in entry[entryKey]) and ('error_high') in entry[entryKey]:
				err = max(entry[entryKey]['error_low'], entry[entryKey]['error_high'])

	output = setReferencedKey(output, f"u_{outputKey}", err, citation)
	output = setReferencedKey(output, outputKey, val, citation)

	return output


def __parseCHIMEJson(inputStr: str) -> list[dict]:
	chime = json.loads(inputStr)

	newRows = []
	for key, vals in chime.items():
		workingDict = getDefaultEntryDict(CHIME_FREQ)

		coord = SkyCoord(ra = vals['ra']['value'], dec = vals['dec']['value'], frame = 'icrs', unit = ('hourangle', 'degree'))

		workingDict = setReferencedKey(workingDict, "NAME", key, citation)
		workingDict = setPositionSkyCoord(workingDict, coord, citation)


		workingDict = _chimeParseValue(vals, workingDict, 'dm', 'DM')
		workingDict = _chimeParseValue(vals, workingDict, 'period', 'P0')
			
		newRows.append(workingDict)
	return newRows

def parseCHIME(url: str = "https://catalog.chime-frb.ca/galactic") -> list[dict]:
	pageData = getPage(url)
	backupPage(pageData, 'chime-galactic.page')

	return __parseCHIMEJson(pageData)