import cdspyreadme
import copy
import pygedm

import astropy.units as u
import astropy.units.cds as u_cds
import numpy as np

from astropy.coordinates import SkyCoord
from astropy.io import ascii
from astropy.table import Table
from uncertainties import ufloat, ufloat_fromstr


baseDefaultDict = {
	'NAME': '',
	'u_NAME': [],
	'RA': None,
	'u_RAs': None,
	'DEC': None,
	'u_DECs': None,
	'GLON': np.nan,
	'GLAT': np.nan,
	'DM': np.nan,
	'u_DM': np.nan,
	'DIST': np.nan,
	'P0': np.nan,
	'u_P0': np.nan,
	'P1': np.nan,
	'u_P1': np.nan,
	'AGE': np.nan,
	'B': np.nan,
}

freqVarDefaultDict = {
	"S_peak": np.nan,
	"S_mean": np.nan,
	"Rate": np.nan,
	"Width": np.nan,
	"NTOA": np.nan
}

def isSet(value):
	if isinstance(value, str):
		if len(value):
			if value == '--':
				return False
		else:
			return False
	elif isinstance(value, list):
		if not len(value):
			return False
	elif isinstance(value, float):
		if np.isnan(value):
			return False
	elif isinstance(value, (type(None), type(np.ma.masked))):
		return False

	return True

def wrapped_ufloat_fromstr(inp):
	if inp == '--':
			return FakeError(np.nan)
	if inp[0] == '(':
			inp = f"{inp[1:-1]}{inp}"
	working = ufloat_fromstr(inp)
	if '(' not in inp:
			working.std_dev = np.nan
	return working

def getDefaultEntryDict(freq: float = -1.0):
	base = copy.deepcopy(baseDefaultDict)
	if np.isnan(freq):
		return base

	if not np.isnan(freq) and freq > 0:
		freqInt = int(freq)
		for key, val in freqVarDefaultDict.items():
			base[f"{key}_{freqInt}"] = val
	
	for key in list(base.keys()):
		base[f"{key}_ref"] = 'UNSET'

	return base

def parsePosError(val: str) -> tuple[float, float]:
	precision = len(val.split(':'))
	err = ufloat_fromstr(val.split(':')[-1])
	if precision == 2:
		err.std_dev *= 60.0 # Scale from minutes to seconds
	elif precision == 3:
		err.std_dev *= 1.0
	else:
		print(val)
		raise RuntimeError(f"Unexpected precision. {precision}")

	if '(' in val:
		cleanval = val.split('(')[0]
	elif '+/-' in val:
		cleanval = val.split('+/-')[0]
	else:
		raise RuntimeError()
	return (cleanval, err.s)


def setPositionSkyCoord(working: dict, coord: SkyCoord, ref: str, precision: int = 4) -> dict:
	raStr, decStr = coord.to_string('hmsdms', sep = ':', precision = precision).split()

	return setPosition(working, raStr, decStr, ref)

def setPosition(working: dict, ra: str, dec: str, ref: str) -> dict:
	if '(' in ra or '+/-' in ra:
		val = parsePosError(ra)
		ra = val[0]
		err = val[1] #* u.hourangle / 24 / 60 # 15 sec = 1 arcsec # Commenting out due to table building issues
		working = setReferencedKey(working, 'u_RAs', err, ref)
	if '(' in dec or '+/-' in dec:
		val = parsePosError(dec) 
		dec = val[0]
		err = val[1] #* u.arcsecond # Commenting out due to table building issues
		working = setReferencedKey(working, 'u_DECs', err, ref)

	for coord in ['RA', 'DEC']:
		refKey = f'u_{coord}_ref'
		if refKey in working:
			if working[refKey] != ref and not np.isnan(working[f'{coord}']):
				print(f"Warning: replacing {coord} for {working['Name']} that previously had an error ({working[refKey]}, with an entry that does not have an error ({ref}).")
				working = setReferencedKey(working, f'u_{coord}', np.nan, 'UNSET')

	coord = SkyCoord(ra = ra, dec = dec, unit = 'hourangle,degree')
	working = setReferencedKey(working, 'RA', ra, ref)
	working = setReferencedKey(working, 'DEC', dec, ref)
	working = setReferencedKey(working, 'GLON', coord.galactic.l.deg, '')
	working = setReferencedKey(working, 'GLAT', coord.galactic.b.deg, '')

	return working

def mergeReferencedKey(input: dict, working: dict, key: str, value) -> dict:
	if isSet(value):
		if key not in ['Cat', 'u_NAME']:
			reference = mappedDict[inputSrc][f"{ref}_ref"]
			working = setReferencedKey(working, key, value, reference)
		else:
			working[key] += value

	return working

def setReferencedKey(working: dict, key: str, value, ref: str) -> dict:
	if not isSet(value):
		return working
	if key not in ['Cat', 'u_NAME']:
		working[key] = value
		working[f"{key}_ref"] = ref
	else:
		value = [(value, ref)]
		working[key] += value
	return working

def deriveParameters(catalogue: list[dict]) -> dict:
	
	def characteristicAge(p, pdot):
		if pdot == 0:
				return 0
		return p / (2 * pdot) / (365 * 24 * 60 * 60)
	
	def magneticField(p, pdot):
		if pdot <= 0:
				return np.nan
		return 3.2e19 * np.sqrt(p * pdot)

	for idx, entry in enumerate(catalogue):
		if not np.isnan([entry['P0'], entry['P1']]).sum():
			age = characteristicAge(entry['P0'], entry['P1'] * 1e-15)
			bfield = magneticField(entry['P0'], entry['P1'] * 1e-15)

			entry = setReferencedKey(entry, 'AGE', age / 1e9, entry['P1_ref'])
			entry = setReferencedKey(entry, 'B', bfield / 1e12, entry['P1_ref'])

		if not np.isnan([entry['DM'], entry['GLAT'], entry['GLON']]).sum():
			dist = pygedm.dm_to_dist(entry['GLAT'], entry['GLON'], entry['DM'])[0]
			# Model failures are capped at 25k
			if dist.value < 24999:
				entry = setReferencedKey(entry, 'DIST', dist.value / 1000.0, ','.join([entry['DM_ref'], entry['GLAT_ref'], 'YMW16']))

		catalogue[idx] = entry

	return catalogue

def getFreqsInCatalogue(cat: dict, subset: list = ['ALL']):
	returnAll = False
	if 'ALL' in subset:
		returnAll = True

	freqs = set()
	for entry in cat:
		breakNow = False
		for key in entry:
			
			if 'NTOA' in key:
				freq = int(key.split('_')[1])
				if (freq in subset or returnAll):
					freqs.add(freq)
					breakNow = True
		if breakNow:
			continue

	for freq in subset:
		if not freq in freqs and freq != 'ALL':
			print(f"WARNING: Requested frequency {freq} was not found in the catalogue.")
	return freqs

citationMap = {
	'BS10': ('BS10', 'Burke-Spolaor, S. & Bailes, M., The millisecond radio sky: transients from a blind single-pulse search (10.1111/j.1365-2966.2009.15965.x, RRATalog)'),
	'BS11': ('BS11', 'Burke-Spolaor et al., The High Time Resolution Universe Pulsar Survey - III. Single-pulse searches and preliminary analysis (10.1111/j.1365-2966.2011.18521.x, RRATalog)'),
	'K11': ('K11', 'Keane et al., Rotating Radio Transients: new discoveries, timing solutions and musings (10.1111/j.1365-2966.2011.18917.x, RRATalog)'),
	'RRATALOG': ('RTLG', 'Cui et al., The RRATalog (2016), (http://astro.phys.wvu.edu/rratalog/)'),
	'PALFA': ('PLFA', 'Pulsar ALFA Survey Project (http://www.naic.edu/~palfa/ , RRATalog)'),
	'PALFA2': ('PLF2', 'Pulsar ALFA Survey Project (http://www.naic.edu/~palfa/ , RRATalog)'),
	'PM1': ('PM1', 'McLaughlin et al., Transient radio bursts from rotating neutron stars (10.1038/nature04440, RRATalog)'),
	'C16':  ('C16', 'Cui et al., Timing Solution and Single-pulse Properties for Eight Rotating Radio Transients (10.3847/1538-4357/aa6aa9, RRATalog)'),
	'GBNCC': ('GCC', 'Karako-Argaman et al., Offline Webpage, Parsed by RRATalog'),
	'GBNCCSite': ('GCCS', 'GBNCC Discoveries (http://astro.phys.wvu.edu/GBNCC/)'),
	'Deneva et al. 2016': ('D16', 'Deneva et al., New Discoveries from the Arecibo 327 MHz Drift Pulsar Survey Radio Transient Search (10.3847/0004-637X/821/1/10)'),
	'McKenna et al. 2023': ('M23', 'McKenna et al., A Census of Rotating Radio Transients at 150 MHz with the Irish LOFAR Station (10.48550/arXiv.2302.12661)'),
	'GBTNGP': ('GNCP', "Hessels et al., The GBT350 Survey of the Northern Galactic Plane for Radio Pulsars and Transients (10.1063/1.2900310, RRATalog)"),
	'GBT350': ('G350', 'GBT 350-MHz Driftscan Survey Processing, (http://astro.phys.wvu.edu/GBTdrift350/ , RRATalog)'),
	'PM2': ('PM2', 'Keane et al., Further searches for Rotating Radio Transients in the Parkes Multi-beam Pulsar Survey (10.1111/j.1365-2966.2009.15693.x, RRATalog)'),
	'Good et al. 2021': ('G21', 'Good et al, First discovery of new pulsars and RRATs with CHIME/FRB (10.3847/1538-4357/ac1da6)'),
	'Patel et al. 2018': ('P18', 'Patel et al., PALFA Single-pulse Pipeline: New Pulsars, Rotating Radio Transients, and a Candidate Fast Radio Burst (10.3847/1538-4357/aaee65)'),
	'CHIME_FRB_CAT': ('CGS', 'CHIME Galactic Sources Catalogue, (https://www.chime-frb.ca/galactic)'),
	'Rane et al. 2015': ('R15', 'Rane et al, A search for rotating radio transients and fast radio bursts in the Parkes high-latitude pulsar survey (10.1093/mnras/stv2404)'),
	'Zhou et al. 2023': ('Z23', 'Zhou et al, The FAST Galactic Plane Pulsar Snapshot Survey: II. Discovery of 76 Galactic rotating radio transients and their enigma (10.1088/1674-4527/accc76)'),
	'Cui et al. 2017': ('C17', 'Cui et al., Timing Solution and Single-pulse Properties for Eight Rotating Radio Transients (10.3847/1538-4357/aa6aa9'),
	'SK': ('SK', 'Shitov et al, Detection of the new rotating radio transient pulsar PSR J2225+35 (10.1134/S1063772909060080, RRATalog)'),
	'LOTASS': ('LTS', 'LOTAAS (https://www.astron.nl/lotaas/index-full.html , RRATalog)'),
	'BSA LPI RRATs': ('BSA', 'BSA Analytics Transients (https://bsa-analytics.prao.ru/en/transients/rrat/)'),
	'BB': ('BB', 'Unknown, RRATalog'),
	'SUPERB': ('SPRB', 'SUPERB Survey, (https://web.archive.org/web/20220626134940/https://sites.google.com/site/publicsuperb/discoveries/ , RRATalog)'),
	'Dong et al. 2023': ('D23', 'Dong et al., The second set of pulsar discoveries by CHIME/FRB/Pulsar: 14 Rotating Radio Transients and 7 pulsars ()'),
	'AODrift': ('AOD', 'Discoveries from the AO 327 MHz Drift Survey (http://www.naic.edu/~deneva/drift-search/ , RRATalog)'),
	'PSRCAT': ('PSCT', 'The ATNF Pulsar Catalogue (https://www.atnf.csiro.au/research/pulsar/psrcat/)')

}

def citationShorthand(citation):
	citations = []
	for idx, cite in enumerate(citation.split(',')):
		if idx and 'RRATALOG' == cite:
			continue
		shorthand, longhand = citationMap[cite]
		citations.append((shorthand, f"{shorthand}: {longhand}"))

	return citations

def generateTable(cat: dict, freqSubset: list = ['ALL']):

	cat = copy.deepcopy(deriveParameters(cat))
	for entry in cat:
		entry['u_NAME'] = ','.join(entry['u_NAME'])

	columnsUnits = [
			('NAME', None, str, "Source Name"),
			#('u_NAME', None, str, "Comma separated alternative names of the source"),
			("RA", u.hourangle, str, "Right Ascension (J2000)"),
			("u_RAs", u.hourangle / 24 / 60, float, "Uncertainty of Right Ascension (second)"),
			("DEC", u.degree, str, "Declination (J2000)"),
			("u_DECs", u.arcsecond, float, "Uncertainty of Declination (arcseconds)"),
			("GLON", u.degree, float, "Galactic Longitude"),
			("GLAT", u.degree, float, "Galatic Latitude"),
			("DM", u.parsec / (u.cm ** 3), float, "Dispersion measure"),
			("u_DM", u.parsec / (u.cm ** 3), float, "Uncertainty of Dispersion measure"),
			('DIST', u.parsec * 1000, float, "Source distance (as per YWM16)"),
			('P0', u.second, float, "Rotation Period"),
			('u_P0', u.second, float, "Uncertainty of rotation period"),
			('P1', u.second * 1e-15 / u.second, float, "Spin-down Rate (seconds per second)"),
			('u_P1', u.second * 1e-15 / u.second, float, "Uncertainty of spin down rate (seconds per second)"),
			('AGE', u.megayear, float, "Characteristic Age"),
			('B', u.gauss * 1e12, float, "Surface Magnetic Field"),
			("RA_ref", None, str, "Key ref"),
			("DEC_ref",None, str, "Key ref"),
			("DM_ref", None, str, "Key ref"),
			('P0_ref', None, str, "Key ref"),
			('P1_ref', None, str, "Key ref"),
	]

	freqs = getFreqsInCatalogue(cat, freqSubset)

	for freq in freqs:
		columnsUnits += [
			(f'S_peak_{freq}', u.jansky, float, f"Brightest pulse flux density at {freq}MHz"),
			(f'S_mean_{freq}', u.jansky, float, f"Mean pulse flux density at {freq}MHz"),
			(f'Rate_{freq}', 1. / u.hour, float, f"Typical hourly pulse rate at {freq}MHz"),
			(f'Width_{freq}', u.second / 1000, float, f"Typical pulse width at {freq}MHz"),
			(f'NTOA_{freq}', u.dimensionless_unscaled, float, f"Number of observed pulses at {freq}MHz"),
			(f'S_peak_{freq}_ref', None, str, "Key ref"),
			(f'S_mean_{freq}_ref', None, str, "Key ref"),
			(f'Rate_{freq}_ref', None, str, "Key ref"),
			(f'Width_{freq}_ref', None, str, "Key ref"),
			(f'NTOA_{freq}_ref', None, str, "Key ref"),
		]

	citations = set()
	toTable = []
	for entry in sorted(cat, key = lambda x: x['NAME']):
		listEntry = []
		for (key, __, outType, __) in columnsUnits:
			if key in entry:
				if not ('_ref' in key and entry[key] in ['UNSET', 'UNKNOWN']):
					if 'ref' in key:
						citation = citationShorthand(entry[key])
						__ = [citations.add(key[1]) for key in citation]
						listEntry.append(','.join([key[0] for key in citation]))
					else:
						listEntry.append(entry[key])
					continue
			listEntry.append(np.nan if outType is float else "--")

		toTable.append(listEntry)

	for i, row in enumerate(toTable):
		for j, col in enumerate(row):
			if not isSet(col):
				toTable[i][j] = np.ma.masked
				if columnsUnits[j][1] is not None:
					toTable[i][j] *= columnsUnits[j][1]


	table = Table(list(map(list, zip(*toTable))),
		names = [row[0] for row in columnsUnits],
		units = [row[1] for row in columnsUnits],
		dtype = [row[2] for row in columnsUnits],
		descriptions = [row[3] for row in columnsUnits]
	)
	precisions = [
		('GLON', '%.3f'),
		('GLAT', '%.3f'),
		('P1', '%.3e'),
		('DM', '%.3f'),
		('DIST', '%.3e'),
		('AGE', '%.2e'),
		('B', '%.2e'),
	]
	for (column, precision) in precisions:
		table[column].format = precision
	print(table)
	maker = cdspyreadme.CDSTablesMaker()
	cdstab = maker.addTable(table, name = "RRATCat")
	cdstab.get_column("RA").setSexaRa()
	cdstab.get_column("DEC").setSexaDe()
	maker.add_author("McKenna D. J.")
	for ref in citations:
		maker.putRef("RRATCat", ref)
	maker.writeCDSTables()
	maker.makeReadMe()
	with open('rratCat.readme', 'w') as ref:
			maker.makeReadMe(out = ref)