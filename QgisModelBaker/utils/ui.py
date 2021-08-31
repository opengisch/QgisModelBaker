import os
from enum import Enum
import warnings

from qgis.PyQt.uic import loadUiType

class LogColor():
    COLOR_INFO = '#000000'
    COLOR_SUCCESS = '#004905'
    COLOR_FAIL = '#aa2222'
    COLOR_TOPPING = '#341d5c'

def get_ui_class(ui_file):
    """Get UI Python class from .ui file.
       Can be filename.ui or subdirectory/filename.ui
    :param ui_file: The file of the ui in svir.ui
    :type ui_file: str
    """
    os.path.sep.join(ui_file.split('/'))
    ui_file_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            os.pardir,
            'ui',
            ui_file
        )
    )

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return loadUiType(ui_file_path)[0]
