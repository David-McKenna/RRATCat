import bs4.element 
import copy

import numpy as np
import pandas as pd

from datetime import datetime
from astropy.coordinates import SkyCoord
from typing import Union

from .helpers import getTables
from ..tools.info import BSA_FREQ
from ..tools.table_maker import getDefaultEntryDict, setPositionSkyCoord, isSet, setReferencedKey

citation = 'BSA LPI RRATs'

def __fixup(inp: str, patterns: list[str] = [''], replacement: str = ''):
	if isinstance(inp, str):
		if not isinstance(patterns, list):
			patterns = [patterns]
		for pattern in patterns:
			inpNew = inp.replace(pattern, replacement)

		inp = float(inpNew)
	return inp

def __parsePushchinoBS(inputBS: Union[str, bs4.element.ResultSet]) -> list[dict]:
	pushchinoDf = pd.read_html(str(inputBS), header = 0, index_col = 0, skiprows = [1])[2]

	for col in ['Paper', ]:
		if col in pushchinoDf.columns:
			pushchinoDf = pushchinoDf.drop([col], axis = 1)
	
	pushchinoDf = pushchinoDf.rename({'RRAT': 'NAME', 'Pulsar': 'NAME',
						'Right ascension': 'RA',
						'Declination': 'DEC',						
						'Dispersion measure': 'DM', 
						'Flux density': 'S_peak',
						'Half-width of the average profile': 'Width',
						'The number of detections': "NTOA"}, axis = 1)
	
	pushchinoDict = pushchinoDf.to_dict('index')
	pushchinoList = [pushchinoDict[i + 1] for i in range(len(pushchinoDict.keys()))]
	
	newRows = []
	for row in pushchinoList:
		workingDict = getDefaultEntryDict(BSA_FREQ)
		workingDict = setReferencedKey(workingDict, 'NAME', row['NAME'].replace('−', '-'), citation)
		workingDict = setReferencedKey(workingDict, f'S_peak_{BSA_FREQ}', __fixup(row['S_peak']), citation)
		workingDict = setReferencedKey(workingDict, f'Width_{BSA_FREQ}', __fixup(row['Width'], ['>', '<']), citation)
		workingDict = setReferencedKey(workingDict, f'NTOA_{BSA_FREQ}', __fixup(row['NTOA'], '>'), citation)

		
		# Some sources don't have RA/Dec provided....
		if row['DEC'] is np.nan:
			row['RA'] = row['JName'].replace('J', '')[:4]
			row['RA'] = f"{row['RA'][:2]}h{row['RA'][2:]}m"
			row['DEC'] = row['JName'][-4:]
			row['DEC'] = f"{row['DEC'][:2]}d{row['DEC'][2:]}m"
			
		coord = SkyCoord(ra = row['RA'], 
						 dec = row['DEC'].replace('o', 'd').replace('\'', 'm'), 
						 frame = 'icrs', unit = ('hourangle', 'degree'))
		workingDict = setPositionSkyCoord(workingDict, coord, citation)
		
		# Some DMs are not provided either
		if row['DM'] is not np.nan:
			if isinstance(row['DM'], str):
				dm = [float(d) for d in row['DM'].split(' - ')]
				workingDict = setReferencedKey(workingDict, 'DM', np.mean(dm), citation)
				if ' - ' in row['DM']:
					workingDict = setReferencedKey(workingDict, 'u_DM', np.diff(dm) / 2, citation)

		newRows.append(workingDict)
	
	return newRows

def parsePushchinoRRAT(url: str = "https://bsa-analytics.prao.ru/en/transients/rrat/") -> list[dict]:
	inputBS = getTables(url, 'pushchinorrat.page')
	return __parsePushchinoBS(inputBS)

#def parsePuschinoPulsar(url: str = "https://bsa-analytics.prao.ru/en/pulsars/new/") -> list[dict]:
#    inputBS = getTables(url, 'pushchinopulsar.page')
#    return __parsePushchinoBS(inputBS)

#def parsePushchinoOldPulsar(url: str = "https://bsa-analytics.prao.ru/en/pulsars/known/") -> list[dict]:
#    inputBS = getTables(url, 'pushchinooldpulsar.page')
#    return __parsePushchinoBS(inputBS)