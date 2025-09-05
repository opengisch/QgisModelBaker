from qgis.core import QgsMapLayer
from qgis.gui import QgsAbstractProcessingParameterWidgetWrapper, QgsProcessingGui
from qgis.PyQt.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

DIALOG_STANDARD = QgsProcessingGui.WidgetType.Standard
DIALOG_BATCH = QgsProcessingGui.WidgetType.Batch
DIALOG_MODELER = QgsProcessingGui.WidgetType.Modeler

dialogTypes = {
    "AlgorithmDialog": DIALOG_STANDARD,
    "ModelerParametersDialog": DIALOG_MODELER,
    "BatchAlgorithmDialog": DIALOG_BATCH,
}

# class ConnectionSettingsWidget(QWidget):


from qgis.PyQt.QtWidgets import QLabel, QLineEdit, QVBoxLayout, QWidget


class CharacterCountWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Erstelle die UI-Elemente
        self.line_edit = QLineEdit()
        self.label = QLabel("Anzahl Zeichen: 0")

        # Layout erstellen und Widgets hinzufügen
        layout = QVBoxLayout()
        layout.addWidget(self.line_edit)
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Signal für Textänderung verbinden
        self.line_edit.textChanged.connect(self.update_char_count)

    def update_char_count(self, text):
        # Aktualisiere das Label mit der Anzahl der Zeichen
        self.label.setText(f"Anzahl Zeichen: {len(text)}")


class CharacterCountDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Zeichenzähler-Dialog")

        # CharacterCountWidget erstellen
        self.widget = CharacterCountWidget()

        # Optional: Schließen-Button hinzufügen
        self.close_button = QPushButton("Schließen")
        self.close_button.clicked.connect(self.close)

        # Layout für den Dialog erstellen
        layout = QVBoxLayout()
        layout.addWidget(self.widget)
        layout.addWidget(self.close_button)
        self.setLayout(layout)


class MainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Button erstellen
        self.open_dialog_button = QPushButton("Zeichenzähler öffnen")
        self.open_dialog_button.clicked.connect(self.open_dialog)

        # Layout für das Widget erstellen
        layout = QHBoxLayout()
        layout.addWidget(self.open_dialog_button)
        self.setLayout(layout)

    def open_dialog(self):
        print("open")
        # Dialog erstellen und anzeigen
        dialog = CharacterCountDialog(self)
        dialog.exec_()


class ConnectionSettingsWidgetWrapper(QgsAbstractProcessingParameterWidgetWrapper):
    def __init__(self, param, dialog, row=0, col=0, **kwargs):
        self.dialogType = dialogTypes.get(
            dialog.__class__.__name__, QgsProcessingGui.WidgetType.Standard
        )
        super().__init__(param, self.dialogType)
        self.dialog = dialog
        self.row = row
        self.col = col

        self.widget = self.createWidget(**kwargs)
        # self.label = self.createLabel()
        if param.defaultValue() is not None:
            self.setValue(param.defaultValue())

    def createWidget(self):
        return MainWidget()  # PgConfigPanel(None, DbActionType.EXPORT)

    def postInitialize(self, wrappers):
        return
        for wrapper in wrappers:
            if wrapper.param.name == self.param.parent:
                self.setLayer(wrapper.value())
                wrapper.widgetValueHasChanged.connect(self.parentValueChanged)
                break

    def parentValueChanged(self, wrapper):
        self.setLayer(wrapper.parameterValue())

    def setLayer(self, layer):
        if isinstance(layer, QgsMapLayer):
            layer = layer.source()
        # self.widget.setLayer(layer)

    def setValue(self, value):
        pass
        # self.widget.setValue(value)

    def value(self):
        return None
        # return self.widget.value()

    def widgetValue(self):
        return self.value()

    def setWidgetValue(self, value, context):
        self.setValue(value)
