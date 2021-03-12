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
import glob
import logging
import os
import urllib.parse
import xml.etree.ElementTree as ET

import re
import time #remove later

from enum import Enum
from QgisModelBaker.libili2db.ili2dbutils import get_all_modeldir_in_path
from QgisModelBaker.utils.qt_utils import download_file
from PyQt5.QtCore import (
    QObject,
    pyqtSignal,
    Qt,
    QModelIndex
)
from PyQt5.QtGui import (
    QStandardItemModel,
    QStandardItem,
    QPalette,
    QRegion
)
from PyQt5.QtWidgets import (
    QItemDelegate,
    QLabel,
    QStyle,
    QWidget,
    QGridLayout
)
from qgis.core import QgsMessageLog, Qgis


class IliCache(QObject):
    ns = {
        'ili23': 'http://www.interlis.ch/INTERLIS2.3'
    }

    new_message = pyqtSignal(int, str)

    def __init__(self, configuration, single_ili_file=None):
        QObject.__init__(self)
        self.cache_path = os.path.expanduser('~/.ilicache')
        self.information_file = 'ilimodels.xml'
        self.repositories = dict()
        self.base_configuration = configuration
        self.single_ili_file = single_ili_file
        self.model = IliModelItemModel()
        self.directories = None
        if self.base_configuration:
            self.directories = self.base_configuration.model_directories

    def refresh(self):
        if not self.directories is None:
            for directory in self.directories:
                self.process_model_directory(directory)

        if not self.single_ili_file is None:
            if os.path.exists(self.single_ili_file):
                self.process_single_ili_file()

    def process_model_directory(self, path):
        if path[0] == '%':
            pass
        elif os.path.isdir(path):
            # recursive search of ilimodels paths
            get_all_modeldir_in_path(path, self.process_local_ili_folder)
        else:
            self.download_repository(path)

    def process_single_ili_file(self):
        models = self.process_ili_file(self.single_ili_file)
        self.repositories["no_repo"] = sorted(
            models, key=lambda m: m['version'], reverse=True)
        self.model.set_repositories(self.repositories)

    def download_repository(self, url):
        """
        Downloads the informationfile (default: ilimodels.xml) and ilisite.xml files from the provided url
        and updates the local cache.
        """
        netloc = urllib.parse.urlsplit(url)[1]

        netloc_dir = os.path.join(self.cache_path, netloc)

        os.makedirs(netloc_dir, exist_ok=True)

        information_file_url = urllib.parse.urljoin(url, self.information_file)
        information_file_path = os.path.join(self.cache_path, netloc, self.information_file)
        ilisite_url = urllib.parse.urljoin(url, 'ilisite.xml')
        ilisite_path = os.path.join(self.cache_path, netloc, 'ilisite.xml')

        logger = logging.getLogger(__name__)

        # download ilimodels.xml
        download_file(information_file_url, information_file_path,
                      on_success=lambda: self._process_informationfile(
                          information_file_path, netloc),
                      on_error=lambda error, error_string: logger.warning(self.tr(
                          'Could not download {url} ({message})').format(url=information_file_url, message=error_string))
                      )

        # download ilisite.xml
        download_file(ilisite_url, ilisite_path,
                      on_success=lambda: self._process_ilisite(ilisite_path),
                      on_error=lambda error, error_string: logger.warning(self.tr(
                          'Could not download {url} ({message})').format(url=ilisite_url, message=error_string))
                      )

    def _process_ilisite(self, file):
        """
        Parses the ilisite.xml provided in ``file`` and recursively downloads any subidiary sites.
        """
        try:
            root = ET.parse(file).getroot()
        except ET.ParseError as e:
            QgsMessageLog.logMessage(self.tr('Could not parse ilisite file `{file}` ({exception})'.format(
                file=file, exception=str(e))), self.tr('QGIS Model Baker'))
            return

        for site in root.iter('{http://www.interlis.ch/INTERLIS2.3}IliSite09.SiteMetadata.Site'):
            subsite = site.find('ili23:subsidiarySite', self.ns)
            if subsite:
                for location in subsite.findall('ili23:IliSite09.RepositoryLocation_', self.ns):
                    self.download_repository(
                        location.find('ili23:value', self.ns).text)

    def _process_informationfile(self, file, netloc):
        """
        Parses ilimodels.xml provided in ``file`` and updates the local repositories cache.
        """

        try:
            root = ET.parse(file).getroot()
        except ET.ParseError as e:
            QgsMessageLog.logMessage(self.tr('Could not parse ilimodels file `{file}` ({exception})'.format(
                file=file, exception=str(e))), self.tr('QGIS Model Baker'))
            return

        self.repositories[netloc] = list()
        repo_models = list()
        for repo in root.iter('{http://www.interlis.ch/INTERLIS2.3}IliRepository09.RepositoryIndex'):
            for model_metadata in repo.findall('ili23:IliRepository09.RepositoryIndex.ModelMetadata', self.ns):
                model = dict()
                model['name'] = model_metadata.find('ili23:Name', self.ns).text
                version = model['version'] = model_metadata.find( 'ili23:Version', self.ns)
                if version:
                    model['version'] = version.text
                else:
                    model['version'] = None
                model['repository'] = netloc
                repo_models.append(model)

        for repo in root.iter('{http://www.interlis.ch/INTERLIS2.3}IliRepository20.RepositoryIndex'):
            for model_metadata in repo.findall('ili23:IliRepository20.RepositoryIndex.ModelMetadata', self.ns):
                model = dict()
                model['name'] = model_metadata.find('ili23:Name', self.ns).text
                version = model_metadata.find( 'ili23:Version', self.ns)
                if version:
                    model['version'] = version.text
                else:
                    model['version'] = None
                model['repository'] = netloc
                repo_models.append(model)

        self.repositories[netloc] = sorted(
            repo_models, key=lambda m: m['version'] if m['version'] else 0, reverse=True)

        self.model.set_repositories(self.repositories)

    def process_local_ili_folder(self, path):
        """
        Parses all .ili files in the given ``path`` (non-recursively)
        """
        models = list()
        fileModels = list()
        for ilifile in glob.iglob(os.path.join(path, '*.ili')):
            fileModels = self.process_ili_file(ilifile)
            models.extend(fileModels)

        self.repositories[path] = sorted(
            models, key=lambda m: m['version'], reverse=True)

        self.model.set_repositories(self.repositories)

    def process_ili_file(self, ilifile):
        fileModels = list()
        try:
            fileModels = self.parse_ili_file(ilifile, "utf-8")
        except UnicodeDecodeError:
            try:
                fileModels = self.parse_ili_file(ilifile, "latin1")
                self.new_message.emit(Qgis.Warning,
                                      self.tr(
                                          'Even though the ili file `{}` could be read, it is not in UTF-8. Please encode your ili models in UTF-8.'.format(
                                              os.path.basename(ilifile))))
            except UnicodeDecodeError as e:
                self.new_message.emit(Qgis.Critical,
                                      self.tr(
                                          'Could not parse ili file `{}` with UTF-8 nor Latin-1 encodings. Please encode your ili models in UTF-8.'.format(
                                              os.path.basename(ilifile))))
                QgsMessageLog.logMessage(self.tr(
                    'Could not parse ili file `{ilifile}`. We suggest you to encode it in UTF-8. ({exception})'.format(
                        ilifile=ilifile, exception=str(e))), self.tr('QGIS Model Baker'))
                fileModels = list()

        return fileModels

    def parse_ili_file(self, ilipath, encoding):
        """
        Parses an ili file returning models and version data
        """
        models = list()
        re_model = re.compile(r'\s*MODEL\s*([\w\d_-]+).*')
        re_model_version = re.compile(r'VERSION "([ \w\d\._-]+)".*')
        with open(ilipath, 'r', encoding=encoding) as file:
            model = None
            for lineno, line in enumerate(file):
                line = line.split("!!")[0]
                result = re_model.search(line)
                if result:
                    model = dict()
                    model['name'] = result.group(1)
                    model['version'] = ''
                    model['repository'] = ilipath
                    models += [model]

                result = re_model_version.search(line)
                if result:
                    if not model:
                        raise RuntimeError('VERSION tag found in file {}:{} without previous MODEL definition.'.format(ilipath, lineno))
                    model['version'] = result.group(1)
                    model = None

        return models

    @property
    def model_names(self):
        names = list()
        for repo in self.repositories.values():
            for model in repo:
                names.append(model['name'])
        return names


class IliModelItemModel(QStandardItemModel):
    class Roles(Enum):
        ILIREPO = Qt.UserRole + 1
        VERSION = Qt.UserRole + 2

        def __int__(self):
            return self.value

    def __init__(self, parent=None):
        super().__init__(0, 1, parent)

    def set_repositories(self, repositories):
        self.clear()
        row = 0
        names = list()

        for repository in repositories.values():

            for model in repository:
                # in case there is more than one version of the model with the same name, it shouldn't load it twice
                if any(model['name'] in s for s in names):
                    continue

                item = QStandardItem()
                item.setData(model['name'], int(Qt.DisplayRole))
                item.setData(model['name'], int(Qt.EditRole))
                item.setData(model['repository'], int(IliModelItemModel.Roles.ILIREPO))
                item.setData(model['version'], int(IliModelItemModel.Roles.VERSION))

                names.append(model['name'])
                self.appendRow(item)
                row += 1


class ModelCompleterDelegate(QItemDelegate):
    """
    A item delegate for the autocompleter of model dialogs.
    It shows the source repository next to the model name.
    """

    def __init__(self):
        super().__init__()
        self.widget = QWidget()
        self.widget.setLayout(QGridLayout())
        self.widget.layout().setContentsMargins(2, 0, 0, 0)
        self.model_label = QLabel()
        self.model_label.setAttribute(Qt.WA_TranslucentBackground)
        self.repository_label = QLabel()
        self.repository_label.setAlignment(Qt.AlignRight)
        self.widget.layout().addWidget(self.model_label, 0, 0)
        self.widget.layout().addWidget(self.repository_label, 0, 1)

    def paint(self, painter, option, index):
        option.index = index
        super().paint(painter, option, index)

    def drawDisplay(self, painter, option, rect, text):
        repository = option.index.data(int(IliModelItemModel.Roles.ILIREPO))
        version = option.index.data(int(IliModelItemModel.Roles.VERSION))
        self.repository_label.setText('<font color="#666666"><i>{repository}</i></font>'.format(repository=repository))
        self.model_label.setText('{model}'.format(model=text))
        self.widget.setMinimumSize(rect.size())

        model_palette = option.palette
        if option.state & QStyle.State_Selected:
            model_palette.setColor(QPalette.WindowText, model_palette.color(QPalette.Active, QPalette.HighlightedText))

        self.widget.render(painter, rect.topLeft(), QRegion(), QWidget.DrawChildren)


class IliMetaConfigCache(IliCache):

    file_download_succeeded = pyqtSignal(str, str, str)
    file_download_failed = pyqtSignal(str, str, str)

    def __init__(self, configuration, models=None):
        IliCache.__init__(self, configuration)
        self.cache_path = os.path.expanduser('~/.ilimetaconfigcache')
        self.information_file = 'ilidata.xml'
        self.model = IliMetaConfigItemModel()
        if models:
            self.filter_models = models.split(';')
        if self.base_configuration:
            self.directories = self.base_configuration.metaconfig_directories

        self.file_directory_name = 'metaconfig'

    def _process_informationfile(self, file, netloc):
        """
        Parses ilidata.xml provided in ``file`` and updates the local repositories cache.
        """
        try:
            root = ET.parse(file).getroot()
        except ET.ParseError as e:
            QgsMessageLog.logMessage(self.tr('Could not parse ilidata file `{file}` ({exception})'.format(
                file=file, exception=str(e))), self.tr('QGIS Model Baker'))
            return

        model_code_regex = re.compile('http://codes.interlis.ch/model/(.*)')
        type_code_regex = re.compile('http://codes.interlis.ch/type/(.*)')
        tool_code_regex = re.compile('http://codes.opengis.ch/(.*)')

        self.repositories[netloc] = list()
        repo_metaconfigs = list()
        for repo in root.iter('{http://www.interlis.ch/INTERLIS2.3}DatasetIdx16.DataIndex'):
            for metaconfig_metadata in repo.findall('ili23:DatasetIdx16.DataIndex.DatasetMetadata', self.ns):
                categories_element = metaconfig_metadata.find('ili23:categories', self.ns)
                if categories_element:
                    model=''
                    type=''
                    tool=''
                    for category in categories_element.findall('ili23:DatasetIdx16.Code_', self.ns):
                        category_value = category.find('ili23:value', self.ns).text
                        if model_code_regex.search(category_value):
                            model = model_code_regex.search(category_value).group(1)
                        if type_code_regex.search(category_value):
                            type = type_code_regex.search(category_value).group(1)
                        if tool_code_regex.search(category_value):
                            tool = tool_code_regex.search(category_value).group(1)
                    if model not in self.filter_models or type != 'metaconfig' or tool != 'modelbaker':
                        continue

                    for files_element in metaconfig_metadata.findall('ili23:files', self.ns):
                        for data_file in files_element.findall('ili23:DatasetIdx16.DataFile', self.ns):
                            for file_element in data_file.findall('ili23:file', self.ns):
                                for file in file_element.findall('ili23:DatasetIdx16.File', self.ns):
                                    path = file.find('ili23:path', self.ns).text

                                    metaconfig = dict()
                                    metaconfig['id'] = metaconfig_metadata.find('ili23:id', self.ns).text

                                    version = metaconfig_metadata.find('ili23:version', self.ns)
                                    if version:
                                        metaconfig['version'] = version.text
                                    else:
                                        metaconfig['version'] = None

                                    owner = metaconfig_metadata.find('ili23:owner', self.ns)
                                    if owner:
                                        metaconfig['owner'] = owner.text
                                    else:
                                        metaconfig['owner'] = None

                                    metaconfig['repository'] = netloc
                                    metaconfig['model'] = model
                                    metaconfig['relative_file_path'] = path
                                    repo_metaconfigs.append(metaconfig)

        self.repositories[netloc] = sorted(
            repo_metaconfigs, key=lambda m: m['version'] if m['version'] else 0, reverse=True)

        self.model.set_repositories(self.repositories)

    def download_file(self, netloc, file, dataset_id=None):
        """
        Downloads the given file from the given url to the local cache.
        passes the local file path or the id (for information) to signals.
        Returns the file path immediately (might not be downloaded yet)
        """
        file_dir = os.path.join(self.cache_path, netloc, self.file_directory_name)
        os.makedirs(file_dir, exist_ok=True)

        file_url = urllib.parse.urlunsplit(('https',netloc, file, None, None))
        file_path = os.path.join(self.cache_path, netloc, file)

        print( f"file_dir: {file_dir} file_url:{file_url} file_path:{file_path}")
        logger = logging.getLogger(__name__)

        # download file
        download_file(file_url, file_path,
                      on_success=lambda: self.file_download_succeeded.emit(netloc, dataset_id, file_path),
                      on_error=lambda error, error_string: self.file_download_failed.emit(netloc, dataset_id, self.tr('Could not download file {url} ({message})').format(url=file_url, message=error_string))
                      )
        return file_path


class IliMetaConfigItemModel(QStandardItemModel):
    class Roles(Enum):
        ILIREPO = Qt.UserRole + 1
        VERSION = Qt.UserRole + 2
        MODEL = Qt.UserRole + 3
        RELATIVEFILEPATH = Qt.UserRole + 4
        OWNER = Qt.UserRole + 5

        def __int__(self):
            return self.value

    def __init__(self, parent=None):
        super().__init__(0, 1, parent)

    def set_repositories(self, repositories):
        self.clear()
        row = 0
        ids = list()

        for repository in repositories.values():

            for metaconfig in repository:
                if any(metaconfig['id'] in s for s in ids):
                    continue

                item = QStandardItem()
                item.setData(metaconfig['id'], int(Qt.DisplayRole))
                item.setData(metaconfig['id'], int(Qt.EditRole))
                item.setData(metaconfig['repository'], int(IliMetaConfigItemModel.Roles.ILIREPO))
                item.setData(metaconfig['version'], int(IliMetaConfigItemModel.Roles.VERSION))
                item.setData(metaconfig['model'], int(IliMetaConfigItemModel.Roles.MODEL))
                item.setData(metaconfig['relative_file_path'], int(IliMetaConfigItemModel.Roles.RELATIVEFILEPATH))
                item.setData(metaconfig['owner'], int(IliMetaConfigItemModel.Roles.OWNER))

                ids.append(metaconfig['id'])
                self.appendRow(item)
                row += 1


class MetaConfigCompleterDelegate(QItemDelegate):
    """
    A item delegate for the autocompleter of metaconfig / topping dialogs.
    It shows the source repository (including model) next to the metaconfig id and the owner.
    """

    def __init__(self):
        super().__init__()
        self.widget = QWidget()
        self.widget.setLayout(QGridLayout())
        self.widget.layout().setContentsMargins(2, 0, 0, 0)
        self.metaconfig_label = QLabel()
        self.metaconfig_label.setAttribute(Qt.WA_TranslucentBackground)
        self.repository_label = QLabel()
        self.repository_label.setAlignment(Qt.AlignRight)
        self.widget.layout().addWidget(self.metaconfig_label, 0, 0)
        self.widget.layout().addWidget(self.repository_label, 0, 2)

    def paint(self, painter, option, index):
        option.index = index
        super().paint(painter, option, index)

    def drawDisplay(self, painter, option, rect, text):
        repository = option.index.data(int(IliMetaConfigItemModel.Roles.ILIREPO))
        model = option.index.data(int(IliMetaConfigItemModel.Roles.MODEL))
        owner = option.index.data(int(IliMetaConfigItemModel.Roles.OWNER))
        self.repository_label.setText('<font color="#666666"><i>{model} at {repository}</i></font>'.format(model=model,repository=repository))
        self.metaconfig_label.setText('{metaconfig_id} of {owner}'.format(metaconfig_id=text, owner=owner))
        self.widget.setMinimumSize(rect.size())

        model_palette = option.palette
        if option.state & QStyle.State_Selected:
            model_palette.setColor(QPalette.WindowText, model_palette.color(QPalette.Active, QPalette.HighlightedText))

        self.widget.render(painter, rect.topLeft(), QRegion(), QWidget.DrawChildren)


class IliToppingFileCache(IliMetaConfigCache):

    download_finished = pyqtSignal()
    """
    meta_netloc is the repository (netloc) of the metaconfiguration file used for file paths in the file_ids
    file_ids can contain ilidata: or file: information
    """

    def __init__(self, configuration, metaconfig_netloc=None, file_ids=None, file_directory_name=None):
        IliMetaConfigCache.__init__(self, configuration)
        self.cache_path = os.path.expanduser('~/.ilitoppingfilescache')
        self.model = IliToppingFileItemModel()
        self.metaconfig_netloc = metaconfig_netloc
        self.file_directory_name = file_directory_name
        self.file_ids = file_ids
        #this could be done maybe nicer dave - it's not reliable with the list, since it might not find qml (but we have atimeout in the waiting loop)
        self.downloaded_files = list()
        self.file_download_succeeded.connect(lambda netloc, dataset_id, path: self.on_download_status(dataset_id, path, True))
        self.file_download_failed.connect(lambda netloc, dataset_id, path: self.on_download_status(dataset_id, path, False))

    def refresh(self):
        if not self.directories is None:
            for directory in self.directories:
                self.process_model_directory(directory)
        #used here?
        if not self.single_ili_file is None:
            if os.path.exists(self.single_ili_file):
                self.process_single_ili_file()

        #download local files
        repo_files = list()
        for file_path_id in [file_id for file_id in self.file_ids if file_id[0:5] == 'file:']:
            toppingfile = dict()
            toppingfile['id'] = file_path_id
            toppingfile['version'] = None
            toppingfile['owner'] = None
            toppingfile['repository'] = self.metaconfig_netloc
            toppingfile['relative_file_path'] = file_path_id[5:]
            toppingfile['local_file_path'] = self.download_file(self.metaconfig_netloc, file_path_id[5:],  file_path_id)
            repo_files.append(toppingfile)

        self.repositories[f'files_{self.metaconfig_netloc}'] = repo_files
        self.model.set_repositories(self.repositories)

    def on_download_status(self, dataset_id, path, success ):
        # here we could add some more logic
        print(f"downloaded {dataset_id} with {success}")
        self.downloaded_files.append(dataset_id)

        if len(self.downloaded_files) == len(self.file_ids):
            print(f"downloaded FINISHED")
            time.sleep(1)
            self.download_finished.emit()

    def _process_informationfile(self, file, netloc):
        """
        Parses ilidata.xml provided in ``file`` and updates the local repositories cache.
        """
        try:
            root = ET.parse(file).getroot()
        except ET.ParseError as e:
            QgsMessageLog.logMessage(self.tr('Could not parse ilidata file `{file}` ({exception})'.format(
                file=file, exception=str(e))), self.tr('QGIS Model Baker'))
            return

        self.repositories[netloc] = list()
        repo_files = list()
        for repo in root.iter('{http://www.interlis.ch/INTERLIS2.3}DatasetIdx16.DataIndex'):
            for topping_metadata in repo.findall('ili23:DatasetIdx16.DataIndex.DatasetMetadata', self.ns):
                dataset_id = 'ilidata:{}'.format(topping_metadata.find('ili23:id', self.ns).text)
                if dataset_id in self.file_ids:
                    for files_element in topping_metadata.findall('ili23:files', self.ns):
                        for data_file in files_element.findall('ili23:DatasetIdx16.DataFile', self.ns):
                            for file_element in data_file.findall('ili23:file', self.ns):
                                for file in file_element.findall('ili23:DatasetIdx16.File', self.ns):
                                    path = file.find('ili23:path', self.ns).text

                                    toppingfile = dict()
                                    toppingfile['id'] = dataset_id

                                    version = topping_metadata.find('ili23:version', self.ns)
                                    if version:
                                        toppingfile['version'] = version.text
                                    else:
                                        toppingfile['version'] = None

                                    owner = topping_metadata.find('ili23:owner', self.ns)
                                    if owner:
                                        toppingfile['owner'] = owner.text
                                    else:
                                        toppingfile['owner'] = None

                                    toppingfile['repository'] = netloc
                                    toppingfile['relative_file_path'] = path
                                    toppingfile['local_file_path'] = self.download_file(netloc, path, dataset_id)
                                    repo_files.append(toppingfile)

        self.repositories[netloc] = sorted(
            repo_files, key=lambda m: m['version'] if m['version'] else 0, reverse=True)

        self.model.set_repositories(self.repositories)


class IliToppingFileItemModel(QStandardItemModel):
    class Roles(Enum):
        ILIREPO = Qt.UserRole + 1
        VERSION = Qt.UserRole + 2
        RELATIVEFILEPATH = Qt.UserRole + 3
        LOCALFILEPATH = Qt.UserRole + 4
        OWNER = Qt.UserRole + 5

        def __int__(self):
            return self.value

    def __init__(self, parent=None):
        super().__init__(0, 1, parent)

    def set_repositories(self, repositories):
        self.clear()
        row = 0
        ids = list()

        for repository in repositories.values():

            for toppingfile in repository:
                if any(toppingfile['id'] in s for s in ids):
                    continue
                item = QStandardItem()
                item.setData(toppingfile['id'], int(Qt.DisplayRole))
                item.setData(toppingfile['id'], int(Qt.EditRole))
                item.setData(toppingfile['repository'], int(IliToppingFileItemModel.Roles.ILIREPO))
                item.setData(toppingfile['version'], int(IliToppingFileItemModel.Roles.VERSION))
                item.setData(toppingfile['relative_file_path'], int(IliToppingFileItemModel.Roles.RELATIVEFILEPATH))
                item.setData(toppingfile['local_file_path'], int(IliToppingFileItemModel.Roles.LOCALFILEPATH))
                item.setData(toppingfile['owner'], int(IliToppingFileItemModel.Roles.OWNER))

                ids.append(toppingfile['id'])
                self.appendRow(item)
                row += 1
