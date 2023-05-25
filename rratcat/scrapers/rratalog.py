import bs4.element
import copy
import pandas

import numpy as np

from astropy.coordinates import SkyCoord
from typing import Union

from .helpers import getTables
from ..tools.info import *
from ..tools.table_maker import getDefaultEntryDict, setReferencedKey, setPositionSkyCoord

# RRatalog
rratalogMap = {
	"Name": None,
	"P": "P0",
	"Pdot": "P1",
	"DM": "DM",
	"RA": None,
	"Dec": None,
	'l': None,
	'b': None,
	'Burst Rate': None,
	'log[B]': None,
	'Age log[t]': None,
	'Distance': None,
	#"S_140 MHz": "S140",
	#"S_350 MHz": "S350",
	#"S_1400 MHz": "S1400",
	#"Pulse Width 140 MHz": "W140",
	#"Pulse Width 350 MHz": "W350",
	#"Pulse Width 1400 MHz": "W1400",
	"S_140 MHz": "S_peak_140",
	"S_350 MHz": "S_peak_350",
	"S_1400 MHz": "S_peak_1400",
	"Pulse Width 140 MHz": "W_140",
	"Pulse Width 350 MHz": "W_350",
	"Pulse Width 1400 MHz": "W_1400",
	'RM': None,
	'Linear Polarzation': None,
	"Survey": None
}

surveyFrequencyMap = {
	"GBTNGP": GBNCC_FREQ,
	"GBNCC": GBNCC_FREQ,
	"BS10": PARKES_FREQ,
	"BS11": PARKES_FREQ,
	"AODrift": ARECIBO_DRIFT_FREQ,
	"PALFA2": ARECIBO_FREQ,
	"PALFA": ARECIBO_FREQ,
	"K11": PARKES_FREQ,
	"PM1": 1400,
	"PM2": 1400,
	"GBT350": GBNCC_FREQ,
	"SK": BSA_FREQ,
	"BB": np.nan,
}


citation = 'RRATALOG'
def __parseRRATalogBS(inputBS: Union[str, bs4.element.ResultSet]) -> list[dict]:
	rratalogTables = pandas.read_html(str(inputBS), header = 0, skiprows = [1])
	# archiv.org sometimes picks up the date picker as a table
	for table in rratalogTables:
		if len(table) < 100:
			continue
		rratalogDf = table
		break

	rratalogDict = rratalogDf.to_dict('index')
	rratalogList = [rratalogDict[i] for i in range(len(rratalogDict.keys()))]
	newRows = []
	
	for row in rratalogList:
		# Spelling is intentional, it's wrong in the catalog
		# We'll grab it when parsing the LOTAAS sources
		#if 'LOTASS' in row['Survey']:
		#    continue
		workingDict = getDefaultEntryDict()

		surveyForFreq = row['Survey'].replace(' ', '').split('/')[0].replace(' ', '')
		catalogCitation = ','.join(row['Survey'].replace(' ', '').split('/') + [citation])
		coord = SkyCoord(ra = row['RA'], dec = row['Dec'], frame = 'icrs', unit = ('hourangle', 'degree'))

		workingDict = setReferencedKey(workingDict, 'NAME', row['Name'].replace('*', ''), catalogCitation)
		workingDict = setPositionSkyCoord(workingDict, coord, catalogCitation)

		if row['Burst Rate'] != '--':
			rateFreq = surveyFrequencyMap[surveyForFreq]
			if not np.isnan(rateFreq):
				workingDict = setReferencedKey(workingDict, f"Rate_{rateFreq}", float(row['Burst Rate']), ','.join([surveyForFreq, citation]))

		for key, val in row.items():
			if val != '--':
				if rratalogMap[key] != None:
					workingDict = setReferencedKey(workingDict, rratalogMap[key], float(row[key]), catalogCitation)

		newRows.append(workingDict)
	return newRows

def parseRRATalog(url: str = "https://web.archive.org/web/20230210010446/http://astro.phys.wvu.edu/rratalog/") -> list[dict]:
	inputBS = getTables(url, 'rratalog.page')
	return __parseRRATalogBS(inputBS)
