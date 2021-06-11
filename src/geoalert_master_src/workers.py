import requests
from PyQt5.QtCore import QObject, pyqtSignal
from qgis.core import QgsMessageLog


class ProcessingFetcher(QObject):
    """"""
    fetched = pyqtSignal(list)
    finished = pyqtSignal()

    def __init__(self, url, auth):
        super().__init__()
        self.url = url
        self.auth = auth

    def fetch_processings(self):
        while True:
            try:
                QgsMessageLog.logMessage('FETCHING', 'Mapflow')
                r = requests.get(self.url, auth=self.auth)
                r.raise_for_status()
                processings = r.json()
                self.fetched.emit(processings)
                # If there are ongoing processings, spin up a thread again to fetch their state
                if not [p for p in processings if p['status'] in ("IN_PROGRESS", "UNPROCESSED")]:
                    break
                else:
                    self.thread().sleep(5)
            except Exception as e:
                QgsMessageLog.logMessage(e, 'Mapflow')
