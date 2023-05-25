import copy
import sys

from tqdm import tqdm

from .scrapers.chime import parseCHIME
from .scrapers.gbncc import parseGBNCC
#from .scrapers.lotaas import parseLOTAAS
from .scrapers.psrcat import psrCatCheckUpdates
from .scrapers.pushchino import  parsePushchinoRRAT
from .scrapers.rratalog import parseRRATalog
from .parsers.csv import getNumSavedCsvs, getSavedCsvs

from .tools.fixers import mergeEntries
from .tools.table_maker import isSet, setReferencedKey, generateTable, getFreqsInCatalogue


class wrappedTqdm:

	def __init__(self, count: int, desc: str = ""):
		self.bar = tqdm(range(count), desc = desc)

	def update(self, amount: int = 1, desc: str = ""):
		self.bar.update(amount)
		self.setDesc(desc)


	def setDesc(self, desc: str = ""):
		if desc:
			self.bar.set_description(desc)
		self.bar.refresh()

	def finish(self):
		self.bar.close()


def main():


	combinedData = []
	# Decreasing priority
	parseData = [
		(getSavedCsvs, getNumSavedCsvs(), "CSVs"),
		(parseCHIME, 1, "CHIME"),
		(parseGBNCC, 1, "GBNCC"),
		#(parseLOTAAS, 1, "LOTAAS"),
		(parsePushchinoRRAT, 1, "BSA LPI"),
		(parseRRATalog, 1, "RRATALOG"),
	]
	progress = wrappedTqdm(sum([entry[1] for entry in parseData]))
	for func, num, desc in parseData:
		progress.setDesc(desc)
		combinedData += func()
		progress.update(num)
	progress.finish()

	mergedData = {}
	for entry in reversed(combinedData):
		if entry['NAME'] in mergedData:
			for key, val in entry.items():
				if '_ref' in key:
					continue
				if isSet(val):
					mergedData[entry['NAME']] = setReferencedKey(mergedData[entry['NAME']], key, val, entry[f'{key}_ref'])

		else:
			mergedData[entry['NAME']] = copy.deepcopy(entry)


	combinedData = mergeEntries(mergedData)

	if len(sys.argv) > 1:
		if sys.argv[1].upper() == 'LIST':
			print(f"Known frequencies [MHz]: {', '.join(sorted([str(val) for val in getFreqsInCatalogue(combinedData, ['ALL'])]))}")
			exit(0)


	combinedData = psrCatCheckUpdates(combinedData)

	freqs = [int(val) if val != 'ALL' else str(val) for val in sys.argv[1:]]
	generateTable(combinedData, freqs if len(freqs) else ['ALL'])

	"""
	from astropy.coordinates import SkyCoord
	for idx, e1 in enumerate(combinedData):
		coord1 = SkyCoord(e1['RA'], e1['DEC'], unit = 'hourangle,degree')
		for e2 in combinedData[idx + 1:]:
			coord2 = SkyCoord(e2['RA'], e2['DEC'], unit = 'hourangle,degree')

			if coord1.separation(coord2).deg < 2:
				try:
					if abs(e1['DM'] - e2['DM']) < max(0.1 * sum([e1['DM'], e2['DM']]), 10):

						print(coord1.separation(coord2))
						print(e1)
						print()
						print(e2)
						print("\n\n\n")
				except:
					print(e1, e2)
	"""


if __name__ == '__main__':
	main()