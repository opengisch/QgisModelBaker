from QgisModelBaker.gui.panel.db_config_panel import DbActionType, DbConfigPanel
from QgisModelBaker.libs.modelbaker.iliwrapper.globals import DbIliMode

available_database_config_panels = dict()

try:
    from QgisModelBaker.gui.panel.pg_config_panel import PgConfigPanel

    available_database_config_panels.update({DbIliMode.pg: PgConfigPanel})
except ModuleNotFoundError:
    pass
try:
    from QgisModelBaker.gui.panel.gpkg_config_panel import GpkgConfigPanel

    available_database_config_panels.update({DbIliMode.gpkg: GpkgConfigPanel})
except ModuleNotFoundError:
    pass
try:
    from QgisModelBaker.gui.panel.mssql_config_panel import MssqlConfigPanel

    available_database_config_panels.update({DbIliMode.mssql: MssqlConfigPanel})
except ModuleNotFoundError:
    pass

# Get panel depending on DB
def get_config_panel(tool, parent, db_action_type: DbActionType) -> DbConfigPanel:
    """Returns an instance of a panel where users to fill out connection parameters to database.
    :param parent: The parent of this widget.
    :param db_action_type: The action type of QgisModelBaker that will be executed.
    :type db_action_type: :class:`DbActionType`
    :return: A panel where users to fill out connection parameters to database.
    :rtype: :class:`DbConfigPanel`
    """
    if tool in available_database_config_panels:
        return available_database_config_panels[tool](parent, db_action_type)

    return None
