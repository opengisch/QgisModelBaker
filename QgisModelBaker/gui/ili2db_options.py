"""
/***************************************************************************
                              -------------------
        begin                : 03/04/17
        git sha              : :%H$
        copyright            : (C) 2017 by Germán Carrillo (BSF-Swissphoto)
        email                : gcarrillo@linuxmail.org
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
from qgis.gui import QgsGui, QgsMessageBar
from qgis.PyQt.QtCore import QSettings, Qt
from qgis.PyQt.QtGui import QValidator
from qgis.PyQt.QtWidgets import QDialog, QSizePolicy

from QgisModelBaker.libs.modelbaker.utils.qt_utils import (
    FileValidator,
    Validators,
    make_file_selector,
)
from QgisModelBaker.utils import gui_utils
from QgisModelBaker.utils.gui_utils import LogColor

DIALOG_UI = gui_utils.get_ui_class("ili2db_options.ui")


class Ili2dbOptionsDialog(QDialog, DIALOG_UI):

    ValidExtensions = ["toml", "TOML", "ini", "INI"]
    SQLValidExtensions = ["sql", "SQL"]

    def __init__(self, parent=None, remove_create_tid_group=True):
        """
        remove_create_tid_group is to remove the "Create Import Tid" setting because on Schema Import it does nothing (legacy issues).
        After removing the single dialog for data import, this setting can be removed completely from the GUI.
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        QgsGui.instance().enableAutoGeometryRestore(self)
        self.toml_file_key = None
        self.current_metaconfig_ili2db = None
        self.current_metaconfig_pre_script_path = None
        self.current_metaconfig_post_script_path = None
        self.current_metaconfig_toml_file_path = None

        self.buttonBox.accepted.disconnect()
        self.buttonBox.accepted.connect(self.accepted)
        self.buttonBox.rejected.disconnect()
        self.buttonBox.rejected.connect(self.rejected)
        self.toml_file_browse_button.clicked.connect(
            make_file_selector(
                self.toml_file_line_edit,
                title=self.tr("Open Extra Meta Attribute File (*.toml *.ini)"),
                file_filter=self.tr(
                    "Extra Model Info File (*.toml *.TOML *.ini *.INI)"
                ),
            )
        )
        self.pre_script_file_browse_button.clicked.connect(
            make_file_selector(
                self.pre_script_file_line_edit,
                title=self.tr("SQL script to run before (*.sql)"),
                file_filter=self.tr("SQL script to run before (*.sql *.SQL)"),
            )
        )
        self.post_script_file_browse_button.clicked.connect(
            make_file_selector(
                self.post_script_file_line_edit,
                title=self.tr("SQL script to run after (*.sql)"),
                file_filter=self.tr("SQL script to run after (*.sql *.SQL)"),
            )
        )

        self.validators = Validators()
        self.file_validator = FileValidator(
            pattern=["*." + ext for ext in self.ValidExtensions], allow_empty=True
        )
        self.toml_file_line_edit.setValidator(self.file_validator)

        self.sql_file_validator = FileValidator(
            pattern=["*." + ext for ext in self.SQLValidExtensions], allow_empty=True
        )
        self.pre_script_file_line_edit.setValidator(self.sql_file_validator)
        self.post_script_file_line_edit.setValidator(self.sql_file_validator)

        self.restore_configuration()

        self.toml_file_line_edit.textChanged.connect(
            self.validators.validate_line_edits
        )
        self.toml_file_line_edit.textChanged.emit(self.toml_file_line_edit.text())
        self.pre_script_file_line_edit.textChanged.connect(
            self.validators.validate_line_edits
        )
        self.pre_script_file_line_edit.textChanged.emit(
            self.pre_script_file_line_edit.text()
        )
        self.post_script_file_line_edit.textChanged.connect(
            self.validators.validate_line_edits
        )
        self.post_script_file_line_edit.textChanged.emit(
            self.post_script_file_line_edit.text()
        )

        # connect to the metaconfig check function
        self.smart1_radio_button.toggled.connect(
            lambda: self._restyle_concerning_metaconfig()
        )
        self.smart2_radio_button.toggled.connect(
            lambda: self._restyle_concerning_metaconfig()
        )
        self.create_import_tid_checkbox.toggled.connect(
            lambda: self._restyle_concerning_metaconfig()
        )
        self.create_basket_col_checkbox.toggled.connect(
            lambda: self._restyle_concerning_metaconfig()
        )

        self.toml_file_line_edit.textChanged.connect(
            lambda: self._restyle_concerning_metaconfig()
        )
        self.pre_script_file_line_edit.textChanged.connect(
            lambda: self._restyle_concerning_metaconfig()
        )
        self.post_script_file_line_edit.textChanged.connect(
            lambda: self._restyle_concerning_metaconfig()
        )

        self.metaconfig_info_label.setVisible(False)

        self.create_import_tid_groupbox.setHidden(remove_create_tid_group)

        self.bar = QgsMessageBar()
        self.bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.layout().addWidget(self.bar, 0, 0, Qt.AlignTop)

    def accepted(self):
        """Save settings before accepting the dialog"""
        for line_edit in [
            self.pre_script_file_line_edit,
            self.post_script_file_line_edit,
            self.toml_file_line_edit,
        ]:
            if (
                line_edit.validator().validate(line_edit.text().strip(), 0)[0]
                != QValidator.Acceptable
            ):
                self.bar.pushWarning(
                    self.tr("Warning"),
                    self.tr(
                        "Please fix the '{}' value before saving the options."
                    ).format(
                        line_edit.objectName()
                        .split("_file_line_edit")[0]
                        .replace("_", " ")
                    ),
                )
                return

        self.save_configuration()
        self.done(1)

    def rejected(self):
        self.restore_configuration()
        self.done(1)

    def create_import_tid(self):
        return self.create_import_tid_checkbox.isChecked()

    def create_basket_col(self):
        return self.create_basket_col_checkbox.isChecked()

    def inheritance_type(self):
        if self.smart1_radio_button.isChecked():
            return "smart1"
        else:
            return "smart2"

    def set_toml_file_key(self, key_postfix):
        if key_postfix:
            self.toml_file_key = "QgisModelBaker/ili2db/tomlfile/" + key_postfix
        else:
            self.toml_file_key = None
        self.restore_configuration()

    def toml_file(self):
        return self.toml_file_line_edit.text().strip()

    def pre_script(self):
        return self.pre_script_file_line_edit.text().strip()

    def post_script(self):
        return self.post_script_file_line_edit.text().strip()

    def stroke_arcs(self):
        return self.stroke_arcs_checkbox.isChecked()

    def save_configuration(self):
        settings = QSettings()
        settings.setValue("QgisModelBaker/ili2db/inheritance", self.inheritance_type())
        settings.setValue(self.toml_file_key, self.toml_file())
        settings.setValue(
            "QgisModelBaker/ili2db/create_basket_col", self.create_basket_col()
        )
        settings.setValue(
            "QgisModelBaker/ili2db/create_import_tid", self.create_import_tid()
        )
        settings.setValue("QgisModelBaker/ili2db/stroke_arcs", self.stroke_arcs())

    def restore_configuration(self):
        settings = QSettings()
        inheritance = settings.value("QgisModelBaker/ili2db/inheritance", "smart2")
        if inheritance == "smart1":
            self.smart1_radio_button.setChecked(True)
        else:
            self.smart2_radio_button.setChecked(True)
        create_basket_col = settings.value(
            "QgisModelBaker/ili2db/create_basket_col", defaultValue=True, type=bool
        )
        create_import_tid = settings.value(
            "QgisModelBaker/ili2db/create_import_tid", defaultValue=True, type=bool
        )
        stroke_arcs = settings.value(
            "QgisModelBaker/ili2db/stroke_arcs", defaultValue=True, type=bool
        )

        self.create_basket_col_checkbox.setChecked(create_basket_col)
        self.create_import_tid_checkbox.setChecked(create_import_tid)
        self.stroke_arcs_checkbox.setChecked(stroke_arcs)
        self.toml_file_line_edit.setText(settings.value(self.toml_file_key))

    def load_metaconfig(self, metaconfig_ili2db):
        self.current_metaconfig_ili2db = metaconfig_ili2db
        if self.current_metaconfig_ili2db:
            if "smart1Inheritance" in self.current_metaconfig_ili2db:
                self.smart1_radio_button.setChecked(
                    self.current_metaconfig_ili2db.getboolean("smart1Inheritance")
                )
            if "smart2Inheritance" in self.current_metaconfig_ili2db:
                self.smart2_radio_button.setChecked(
                    self.current_metaconfig_ili2db.getboolean("smart2Inheritance")
                )
            if "createBasketCol" in self.current_metaconfig_ili2db:
                self.create_basket_col_checkbox.setChecked(
                    self.current_metaconfig_ili2db.getboolean("createBasketCol")
                )
            if "importTid" in self.current_metaconfig_ili2db:
                self.create_import_tid_checkbox.setChecked(
                    self.current_metaconfig_ili2db.getboolean("importTid")
                )
            if "strokeArcs" in self.current_metaconfig_ili2db:
                self.stroke_arcs_checkbox.setChecked(
                    self.current_metaconfig_ili2db.getboolean("strokeArcs")
                )
            self.save_configuration()
        self._restyle_concerning_metaconfig()

    def load_toml_file_path(self, key_postfix, toml_file_path):
        self.current_metaconfig_toml_file_path = toml_file_path
        self.set_toml_file_key(key_postfix)
        self.toml_file_line_edit.setText(toml_file_path)
        self.save_configuration()

    def load_post_script_path(self, post_script_path):
        self.current_metaconfig_post_script_path = post_script_path
        self.post_script_file_line_edit.setText(post_script_path)

    def load_pre_script_path(self, pre_script_path):
        self.current_metaconfig_pre_script_path = pre_script_path
        self.pre_script_file_line_edit.setText(pre_script_path)

    def _restyle_concerning_metaconfig(self):
        """
        Compares the values of the changed object to make visual color indication.
        """
        if self.current_metaconfig_ili2db:

            if "smart1Inheritance" in self.current_metaconfig_ili2db:
                if (
                    self.current_metaconfig_ili2db.getboolean("smart1Inheritance")
                    == self.smart1_radio_button.isChecked()
                ):
                    self.smart1_radio_button.setStyleSheet(
                        f"color:{LogColor.COLOR_TOPPING}"
                    )
                else:
                    self.smart1_radio_button.setStyleSheet(
                        f"color:{LogColor.COLOR_WARNING}"
                    )
            if "smart2Inheritance" in self.current_metaconfig_ili2db:
                if (
                    self.current_metaconfig_ili2db.getboolean("smart2Inheritance")
                    == self.smart2_radio_button.isChecked()
                ):
                    self.smart2_radio_button.setStyleSheet(
                        f"color:{LogColor.COLOR_TOPPING}"
                    )
                else:
                    self.smart2_radio_button.setStyleSheet(
                        f"color:{LogColor.COLOR_WARNING}"
                    )
            if "createBasketCol" in self.current_metaconfig_ili2db:
                if (
                    self.current_metaconfig_ili2db.getboolean("createBasketCol")
                    == self.create_basket_col_checkbox.isChecked()
                ):
                    self.create_basket_col_checkbox.setStyleSheet(
                        f"color:{LogColor.COLOR_TOPPING}"
                    )
                else:
                    self.create_basket_col_checkbox.setStyleSheet(
                        f"color:{LogColor.COLOR_WARNING}"
                    )
            if "importTid" in self.current_metaconfig_ili2db:
                if (
                    self.current_metaconfig_ili2db.getboolean("importTid")
                    == self.create_import_tid_checkbox.isChecked()
                ):
                    self.create_import_tid_checkbox.setStyleSheet(
                        f"color:{LogColor.COLOR_TOPPING}"
                    )
                else:
                    self.create_import_tid_checkbox.setStyleSheet(
                        f"color:{LogColor.COLOR_WARNING}"
                    )
            if "strokeArcs" in self.current_metaconfig_ili2db:
                if (
                    self.current_metaconfig_ili2db.getboolean("strokeArcs")
                    == self.stroke_arcs_checkbox.isChecked()
                ):
                    self.stroke_arcs_checkbox.setStyleSheet(
                        f"color:{LogColor.COLOR_TOPPING}"
                    )
                else:
                    self.stroke_arcs_checkbox.setStyleSheet(
                        f"color:{LogColor.COLOR_WARNING}"
                    )

            if self.current_metaconfig_toml_file_path:
                if (
                    self.current_metaconfig_toml_file_path
                    == self.toml_file_line_edit.text()
                ):
                    self.toml_file_browse_button.setStyleSheet(
                        f"color:{LogColor.COLOR_TOPPING}"
                    )
                    self.toml_file_label.setStyleSheet(
                        f"color:{LogColor.COLOR_TOPPING}"
                    )
                else:
                    self.toml_file_browse_button.setStyleSheet(
                        f"color:{LogColor.COLOR_WARNING}"
                    )
                    self.toml_file_label.setStyleSheet(
                        f"color:{LogColor.COLOR_WARNING}"
                    )

            if self.current_metaconfig_post_script_path:
                if (
                    self.current_metaconfig_post_script_path
                    == self.post_script_file_line_edit.text()
                ):
                    self.post_script_file_browse_button.setStyleSheet(
                        f"color:{LogColor.COLOR_TOPPING}"
                    )
                    self.post_script_file_label.setStyleSheet(
                        f"color:{LogColor.COLOR_TOPPING}"
                    )
                else:
                    self.post_script_file_browse_button.setStyleSheet(
                        f"color:{LogColor.COLOR_WARNING}"
                    )
                    self.post_script_file_label.setStyleSheet(
                        f"color:{LogColor.COLOR_WARNING}"
                    )
            if self.current_metaconfig_pre_script_path:
                if (
                    self.current_metaconfig_pre_script_path
                    == self.pre_script_file_line_edit.text()
                ):
                    self.pre_script_file_browse_button.setStyleSheet(
                        f"color:{LogColor.COLOR_TOPPING}"
                    )
                    self.pre_script_file_label.setStyleSheet(
                        f"color:{LogColor.COLOR_TOPPING}"
                    )
                else:
                    self.pre_script_file_browse_button.setStyleSheet(
                        f"color:{LogColor.COLOR_WARNING}"
                    )
                    self.pre_script_file_label.setStyleSheet(
                        f"color:{LogColor.COLOR_WARNING}"
                    )

            self.metaconfig_info_label.setVisible(True)
        else:
            # reset all
            self.smart1_radio_button.setStyleSheet(f"color:{LogColor.COLOR_INFO}")
            self.smart2_radio_button.setStyleSheet(f"color:{LogColor.COLOR_INFO}")
            self.create_basket_col_checkbox.setStyleSheet(
                f"color:{LogColor.COLOR_INFO}"
            )
            self.create_import_tid_checkbox.setStyleSheet(
                f"color:{LogColor.COLOR_INFO}"
            )
            self.stroke_arcs_checkbox.setStyleSheet(f"color:{LogColor.COLOR_INFO}")
            self.toml_file_browse_button.setStyleSheet(f"color:{LogColor.COLOR_INFO}")
            self.toml_file_label.setStyleSheet(f"color:{LogColor.COLOR_INFO}")
            self.post_script_file_browse_button.setStyleSheet(
                f"color:{LogColor.COLOR_INFO}"
            )
            self.post_script_file_label.setStyleSheet(f"color:{LogColor.COLOR_INFO}")
            self.pre_script_file_browse_button.setStyleSheet(
                f"color:{LogColor.COLOR_INFO}"
            )
            self.pre_script_file_label.setStyleSheet(f"color:{LogColor.COLOR_INFO}")

            self.metaconfig_info_label.setVisible(False)
