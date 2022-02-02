import re


URL_PATTERN = r'https?://(www\.)?([-\w]{1,256}\.)+[a-zA-Z0-9]{1,6}'  # schema + domains
URL = re.compile(URL_PATTERN)
XYZ = re.compile(URL_PATTERN + r'(.*\{[xyz]\}){3}.*', re.I)
QUAD_KEY = re.compile(URL_PATTERN + r'(.*\{q\}).*', re.I)
SENTINEL_DATETIME = re.compile(r'\d{8}T\d{6}', re.I)
SENTINEL_COORDINATE = re.compile(r'T\d{2}[A-Z]{3}', re.I)
UUID = re.compile(r'[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}\Z')
