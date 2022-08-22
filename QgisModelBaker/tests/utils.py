import datetime
import os

import pytest

from QgisModelBaker.internal_libs.toppingmaker import Target


@pytest.mark.skip("This is a utility function, not a test function")
def testdata_path(path):
    basepath = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(basepath, "testdata", path)


def ilidata_path_resolver(target: Target, name, type):
    _, relative_filedir_path = target.filedir_path(type)
    id = unique_id_in_target_scope(target, f"{target.projectname}.{type}_{name}_001")
    path = os.path.join(relative_filedir_path, name)
    type = type
    version = datetime.datetime.now().strftime("%Y-%m-%d")
    toppingfile = {"id": id, "path": path, "type": type, "version": version}
    target.toppingfileinfo_list.append(toppingfile)
    return path


def unique_id_in_target_scope(target: Target, id):
    for toppingfileinfo in target.toppingfileinfo_list:
        if "id" in toppingfileinfo and toppingfileinfo["id"] == id:
            iterator = int(id[-3:])
            iterator += 1
            id = f"{id[:-3]}{iterator:03}"
            return unique_id_in_target_scope(target, id)
    return id
