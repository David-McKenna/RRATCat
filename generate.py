
from requests.exceptions import SSLError

from .scrapers.helpers import *
from .scrapers.chime import parseCHIME
from .scrapers.gbncc import parseGBNCC
from .scrapers.lotaas import parseLOTAAS
from .scrapers.puschino import  parsePushchinoRRAT,  parsePushchinoPulsar,  parsePushchinoOldPulsar
from .scrapers.rratalog import parseRRATalog

CHIMERows = parseCHIME()
gbnccRows = parseGBNCC()
lotaasRows = parseLOTAAS()
pushchinoRows = parsePushchinoRRAT()
pushchinoPulsarRows = parsePushchinoPulsar()
pushchinoOldPulsarRows = parsePushchinoOldPulsar()
rratalogRows = parseRRATalog()

combinedDict = CHIMERows + pushchinoRows + pushchinoPulsarRows +  rratalogRows + gbnccRows + lotaasRows