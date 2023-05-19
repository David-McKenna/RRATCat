import pandas as pd
import copy

from datetime import datetime
from astropy.coordinates import SkyCoord
from typing import Union


BSA_FREQ = 110 # MHz

def __parsePushchinoBS(inputBS: Union[str, bs4.element.ResultSet]) -> list[dict]:
    pushchinoDf = pd.read_html(str(inputBS), header = 0, index_col = 0, skiprows = [1])[2]

    for col in ['Paper', 'The number of detections']:
        if col in pushchinoDf.columns:
            pushchinoDf = pushchinoDf.drop([col], axis = 1)
            
    pushchinoDf = pushchinoDf.rename({'RRAT': 'JName', 'Pulsar': 'JName',
                        'Right ascension': 'Right Ascension', 
                        'Dispersion measure': 'Dispersion Measure', 
                        'Flux density': 'S110', 
                        'Half-width of the average profile': 'W110'}, axis = 1)
    
    pushchinoDict = pushchinoDf.to_dict('index')
    pushchinoList = [pushchinoDict[i + 1 * (1 - backup)] for i in range(len(pushchinoDict.keys()))]
    
    newRows = []
    for row in pushchinoList:
    	workingDict = getDefaultEntryDict()
        workingDict.update({'JName': row['JName'].replace('−', '-'),
							'Catalogs': 'Pushchino',
        					})
        
        # Some sources don't have RA/Dec provided....
        if row['Declination'] is np.nan:
            row['Right Ascension'] = row['JName'].replace('J', '')[:4]
            row['Right Ascension'] = f"{row['Right Ascension'][:2]}h{row['Right Ascension'][2:]}m"
            row['Declination'] = row['JName'][-4:]
            row['Declination'] = f"{row['Declination'][:2]}d{row['Declination'][2:]}m"
            
        coord = SkyCoord(ra = row['Right Ascension'], 
                         dec = row['Declination'].replace('o', 'd').replace('\'', 'm'), 
                         frame = 'icrs', unit = ('hourangle', 'degree'))
        
        workingDict.update({'Right Ascension': coord.ra.rad,
        					'Declination': coord.dec.rad,
        					'SkyCoord': copy.deepcopy(coord),
        				})
                
        # Some DMs are not provided either
        if row['Dispersion Measure'] is not np.nan:
            if isinstance(row['Dispersion Measure'], str):
                if ' - ' in row['Dispersion Measure']:
                    dm = [float(d) for d in row['Dispersion Measure'].split(' - ')]
                    workingDict['dDispersion Measure'] = np.diff(dm)[0] / 2
                    workingDict['Dispersion Measure'] = np.mean((dm))
                else:
                    workingDict['Dispersion Measure'] = float(row['Dispersion Measure'])
                    workingDict['eDispersion Measure'] = np.nan

        
        workingDict['Catalogs'] = 'Pushchino'
        newRows.append(workingDict)
    
    return newRows

def parsePuschinoRRAT(url: str = "https://bsa-analytics.prao.ru/en/transients/rrat/") -> list[dict]:
    inputBS = getTables(url, 'pushchinorrat.page')
    return __parsePushchinoBS(inputBS)

def parsePuschinoPulsar(url: str = "https://bsa-analytics.prao.ru/en/pulsars/new/") -> list[dict]:
    inputBS = getTables(url, 'pushchinopulsar.page')
    return __parsePushchinoBS(inputBS)

def parsePushchinoOldPulsar(url: str = "https://bsa-analytics.prao.ru/en/pulsars/known/") -> list[dict]:
    inputBS = getTables(url, 'pushchinooldpulsar.page')
    return __parsePushchinoBS(inputBS)