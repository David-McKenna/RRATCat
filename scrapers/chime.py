import json
import copy

import numpy as np

from helpers import getPage, backupPage
from astropy.coordinates import SkyCoord


CHIME_FREQ = 600 # MHz

def _chimeParseValue(entry: dict, output: dict, entryKey: str, outputKey: str) -> dict:
    if len(entry[entryKey]):
        output[outputKey] = entry['entryKey']['value']
        if ('error_low' in entry[entryKey]) and ('error_high') in entry[entryKey]:
            output[f"e{outputKey}"] = max(entry[entryKey]['error_low'], entry[entryKey]['error_high'])
        else:
            output[f"e{outputKey}"] = np.nan
    else:
        output[outputKey] = np.nan
        output[f"e{outputKey}"] = np.nan

    return output


def __parseCHIMEJson(inputStr: str) -> list[dict]:
    chime = json.loads(inputStr)

    newRows = []
    for key, vals in chime.items():
        workingDict = getDefaultEntryDict()

        coord = SkyCoord(ra = vals['ra']['value'], dec = vals['dec']['value'], frame = 'icrs', unit = ('hourangle', 'degree'))

        workingDict.update({'JName': key, 
                            'Catalogs': 'CHIME',
                            'Right Ascension': coord.ra.rad,
                            'Declination': coord.dec.rad,
                            'SkyCoord': copy.deepcopy(coord),
                            })

        workingDict = _chimeParseValue(vals, workingDict, 'dm', 'Dispersion Measure')
        workingDict = _chimeParseValue(vals, workingDict, 'period', 'Period')
            
        newRows.append(workingDict)
    return newRows

def parseCHIME(url: str = "https://catalog.chime-frb.ca/galactic") -> list[dict]:
    pageData = getPage(url)
    backupPage(pageData, 'chime-galactic.page')

    return __parseCHIMEJson(pageData)