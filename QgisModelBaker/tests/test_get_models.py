from qgis.testing import (start_app,
                          unittest)
from QgisModelBaker.tests.utils import (testdata_path, 
                                        get_pg_conn, 
                                        get_gpkg_conn)
from QgisModelBaker.libili2db.globals import DbIliMode, displayDbIliMode

import os

start_app()

class TestGetModels(unittest.TestCase):
    @classmethod
    def test_pg_get_models(self):
        expected_dict = {'test_ladm_all_models': ['ANT_V2_9_6', 'Avaluos_V2_9_6', 'Cartografia_Referencia_V2_9_6', 
                                                        'Datos_Gestor_Catastral_V2_9_6', 'Datos_Integracion_Insumos_V2_9_6', 
                                                        'Datos_SNR_V2_9_6', 'Formulario_Catastro_V2_9_6', 'Operacion_V2_9_6', 
                                                        'ISO19107_PLANAS_V1', 'LADM_COL_V1_3'],
                         'test_ladm_integration': ['Datos_SNR_V2_9_6', 'Datos_Integracion_Insumos_V2_9_6', 
                                                            'Datos_Gestor_Catastral_V2_9_6', 'ISO19107_PLANAS_V1', 'LADM_COL_V1_3'],
                         'test_ladm_operation_model': ['Operacion_V2_9_6', 'Datos_SNR_V2_9_6', 'Datos_Integracion_Insumos_V2_9_6', 
                                                            'Datos_Gestor_Catastral_V2_9_6', 'ISO19107_PLANAS_V1', 'LADM_COL_V1_3'],
                         'test_ladm_cadastral_manager_data': ['Datos_Gestor_Catastral_V2_9_6', 'ISO19107_PLANAS_V1']} 

        for schema_name in expected_dict:
            model_names = []
            db_connector = get_pg_conn(schema_name)
            result = db_connector.get_models()
            if result is not None:
                model_names = [db_model['modelname'] for db_model in result]
                
            self.assertEqual(set(expected_dict[schema_name]), set(model_names))
            db_connector.conn.close()

    def test_gpkg_get_models(self):
        expected_dict = {'test_ladm_all_models_v2_9_6': ['ANT_V2_9_6', 'Avaluos_V2_9_6', 'Cartografia_Referencia_V2_9_6', 
                                                        'Datos_Gestor_Catastral_V2_9_6', 'Datos_Integracion_Insumos_V2_9_6', 
                                                        'Datos_SNR_V2_9_6', 'Formulario_Catastro_V2_9_6', 'Operacion_V2_9_6', 
                                                        'ISO19107_PLANAS_V1', 'LADM_COL_V1_3'],
                         'test_ladm_integration_model_v2_9_6': ['Datos_SNR_V2_9_6', 'Datos_Integracion_Insumos_V2_9_6', 
                                                            'Datos_Gestor_Catastral_V2_9_6', 'ISO19107_PLANAS_V1', 'LADM_COL_V1_3'],
                         'test_ladm_operation_model_v2_9_6': ['Operacion_V2_9_6', 'Datos_SNR_V2_9_6', 'Datos_Integracion_Insumos_V2_9_6', 
                                                            'Datos_Gestor_Catastral_V2_9_6', 'ISO19107_PLANAS_V1', 'LADM_COL_V1_3'],
                         'test_ladm_cadastral_manager_model_v2_9_6': ['Datos_Gestor_Catastral_V2_9_6', 'ISO19107_PLANAS_V1']} 

        for gpkg in expected_dict:
            db_connector = get_gpkg_conn(gpkg)
            result = db_connector.get_models()
            if result is not None:
                model_names = [db_model['modelname'] for db_model in result]
            else:
                model_names = {}
                            
            self.assertEqual(set(expected_dict[gpkg]), set(model_names))
