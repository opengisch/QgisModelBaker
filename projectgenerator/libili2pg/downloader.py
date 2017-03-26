from qgis.PyQt.QtCore import QObject, QFile, QIODevice, QEventLoop
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.core import QgsNetworkAccessManager

class Downloader(QObject):
    def __init__(self):
        QObject.__init__(self)
        self.filename = ''
        self.url = ''

    def download(self, url, filename):
        networkAccessManager = QgsNetworkAccessManager.instance()

        print('Starting download {}'.format(url))
        req = QNetworkRequest(QUrl(url))
        reply = networkAccessManager.get(req)

        def finished():
            print('Download finished {} ({})'.format(filename, reply.error()))
            file = QFile(filename)
            file.open(QIODevice.WriteOnly)
            file.write(reply.readAll())
            file.close()
            reply.deleteLater()

        reply.finished.connect(finished)

        loop = QEventLoop()
        reply.finished.connect(loop.quit)
        loop.exec()
