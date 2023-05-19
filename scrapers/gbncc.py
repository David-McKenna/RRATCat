import bs4.element
import copy

from typing import Union

GNBCC_FREQ = 350 # MHz

def __parseGBNCCBS(inputBS: Union[str, bs4.element.ResultSet]) -> list[dict]:
    gbnccDf = pd.read_html(str(inputBS), header = 0, skiprows = [1])[0]
    
    #print(gbnccDf.head())
    gbnccDict = gbnccDf.to_dict('index')
    gbnccList = [gbnccDict[i] for i in range(len(gbnccDict.keys()))]
    
    newRows = []
    
    for row in gbnccList:
        # Spelling is intentional, it's wrong in the catalog
        # We'll grab it when parsing the LOTAAS sources
        #if 'LOTASS' in row['Survey']:
        #    continue
            
        coord = SkyCoord(ra = row['Position'], dec = row['Position.1'], frame = 'icrs', unit = ('hourangle', 'degree'))
        workingDict.update({'JName': 'J' + row['Name'].replace('*', ''),
                        'Right Ascension': coord.ra.rad,
                        'Declination': coord.dec.rad,
                        'SkyCoord' = copy.deepcopy(coord)
                        'Catalogs': "GBNCC_RRATs",
                        'RRATSurvey': False,
                        'Dispersion Measure': float(row['DM (pc cm^-3)']),
                        'Period': float(str(row['P (s)']).replace('~', ''))})
                    
        newRows.append(workingDict)
    
    return newRows

def parseGBNCC(url: str = "http://www.physics.mcgill.ca/~chawlap/GBNCC_RRATs.html") -> list[dict]:
    inputBS = getTables(url, 'gbncc.page')
    return __parseGBNCCBS(inputBS)
