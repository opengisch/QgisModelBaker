from qgis.PyQt.QtWidgets import QDialog
from ..utils import get_ui_class

from metaproject.libqgsprojectgen.generator.ili2pg import Ili2Pg

DIALOG_UI = get_ui_class('generate_project.ui')


class GenerateProjectDialog(QDialog, DIALOG_UI):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

    def accepted(self):
        Ili2Pg