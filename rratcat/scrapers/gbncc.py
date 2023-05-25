import bs4.element
import copy
import pandas

from astropy.coordinates import SkyCoord
from typing import Union

from .helpers import getTables
from ..tools.info import GBNCC_FREQ
from ..tools.table_maker import getDefaultEntryDict, setPositionSkyCoord, setReferencedKey


citation = 'GBNCCSite'
def __parseGBNCCBS(inputBS: Union[str, bs4.element.ResultSet]) -> list[dict]:
	gbnccDf = pandas.read_html(str(inputBS), header = 0, skiprows = [1])[0]
	
	#print(gbnccDf.head())
	gbnccDict = gbnccDf.to_dict('index')
	gbnccList = [gbnccDict[i] for i in range(len(gbnccDict.keys()))]
	
	newRows = []
	
	for row in gbnccList:
		# Spelling is intentional, it's wrong in the catalog
		# We'll grab it when parsing the LOTAAS sources
		#if 'LOTASS' in row['Survey']:
		#    continue
		workingDict = getDefaultEntryDict(GBNCC_FREQ)
		workingDict = setReferencedKey(workingDict, 'NAME', 'J' + row['Name'].replace('*', ''), citation)

			
		coord = SkyCoord(ra = row['Position'], dec = row['Position.1'], frame = 'icrs', unit = ('hourangle', 'degree'))
		workingDict = setPositionSkyCoord(workingDict, coord, citation)

		workingDict = setReferencedKey(workingDict, 'DM', float(row['DM (pc cm^-3)']), citation)
		val = row['P (s)']
		workingDict = setReferencedKey(workingDict, 'P0', float(val.replace('~', '')) if isinstance(val, str) else val, citation)
					
		newRows.append(workingDict)

	
	return newRows

def parseGBNCC(url: str = "http://www.physics.mcgill.ca/~chawlap/GBNCC_RRATs.html") -> list[dict]:
	inputBS = getTables(url, 'gbncc.page')
	return __parseGBNCCBS(inputBS)
