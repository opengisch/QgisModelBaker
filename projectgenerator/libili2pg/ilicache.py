# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 15/06/17
        git sha              : :%H$
        copyright            : (C) 2017 by OPENGIS.ch
        email                : info@opengis.ch
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import logging
import os
import urllib.parse
import xml.etree.ElementTree as ET

from projectgenerator.utils.qt_utils import download_file, NetworkError
from PyQt5.QtCore import QObject, pyqtSignal


class IliCache(QObject):
    ns = {
        'ili23': 'http://www.interlis.ch/INTERLIS2.3'
    }

    models_changed = pyqtSignal()

    def __init__(self):
        QObject.__init__(self)
        self.cache_path = os.path.expanduser('~/.ilicache')
        self.repositories = dict()

    def refresh(self):
        self.download_repository('http://models.interlis.ch')

    def download_repository(self, url):
        '''
        Downloads the ilimodels.xml and ilisite.xml files from the provided url
        and updates the local cache.
        '''
        netloc = urllib.parse.urlsplit(url)[1]

        modeldir = os.path.join(self.cache_path, netloc)

        os.makedirs(modeldir, exist_ok=True)

        ilimodels_url = urllib.parse.urljoin(url, 'ilimodels.xml')
        ilimodels_path = os.path.join(self.cache_path, netloc, 'ilimodels.xml')
        ilisite_url = urllib.parse.urljoin(url, 'ilisite.xml')
        ilisite_path = os.path.join(self.cache_path, netloc, 'ilisite.xml')

        logger = logging.getLogger(__name__)

        # download ilimodels.xml
        download_file(ilimodels_url, ilimodels_path,
                      on_progress=lambda received, total: print('Downloading ({}/{})'.format(received, total)),
                      on_success=lambda: self._process_ilimodels(ilimodels_path, netloc),
                      on_error=lambda error, error_string: logger.warning(self.tr('Could not download {url} ({message})').format(url=ilimodels_url, message=error_string))
                      )

        # download ilisite.xml
        download_file(ilisite_url, ilisite_path,
                      on_progress=lambda received, total: print('Downloading ({}/{})'.format(received, total)),
                      on_success=lambda: self._process_ilisite(ilisite_path),
                      on_error=lambda error, error_string: logger.warning(self.tr('Could not download {url} ({message})').format(url=ilisite_url, message=error_string))
                      )

    def _process_ilisite(self, file):
        '''
        Parses the ilisite.xml provided in ``file`` and recursively downloads any subidiary sites.
        '''
        root = ET.parse(file).getroot()
        for site in root.iter('{http://www.interlis.ch/INTERLIS2.3}IliSite09.SiteMetadata.Site'):
            subsite = site.find('ili23:subsidiarySite', self.ns)
            if subsite:
                for location in subsite.findall('ili23:IliSite09.RepositoryLocation_', self.ns):
                    self.download_repository(location.find('ili23:value', self.ns).text)

    def _process_ilimodels(self, file, netloc):
        '''
        Parses ilimodels.xml provided in ``file`` and updates the local repositories cache.
        '''
        root = ET.parse(file).getroot()
        self.repositories[netloc] = list()
        for repo in root.iter('{http://www.interlis.ch/INTERLIS2.3}IliRepository09.RepositoryIndex'):
            repo_models = list()
            for model_metadata in repo.findall('ili23:IliRepository09.RepositoryIndex.ModelMetadata', self.ns):
                model = dict()
                model['name'] = model_metadata.find('ili23:Name', self.ns).text
                model['version'] = model_metadata.find('ili23:Version', self.ns).text
                repo_models.append(model)

            self.repositories[netloc] = sorted(repo_models, key=lambda m: m['version'], reverse=True)
        self.models_changed.emit()

    @property
    def model_names(self):
        names = list()
        for repo in self.repositories.values():
            for model in repo:
                names.append(model['name'])
        return names
