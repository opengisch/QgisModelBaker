# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 2022-07-17
        git sha              : :%H$
        copyright            : (C) 2022 by Dave Signer
        email                : david at opengis ch
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
import os
import re
import shutil
import unicodedata

from .target import Target


def toppingfile_link(target: Target, type: str, path: str):
    filename_slug = f"{slugify(target.projectname)}_{os.path.basename(path)}"
    absolute_filedir_path, relative_filedir_path = target.filedir_path(type)
    shutil.copy(
        path,
        os.path.join(absolute_filedir_path, filename_slug),
    )
    return target.path_resolver(target, filename_slug, type)


def slugify(text: str) -> str:
    if not text:
        return text
    slug = unicodedata.normalize("NFKD", text)
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", slug).strip("_")
    slug = re.sub(r"[-]+", "_", slug)
    slug = slug.lower()
    return slug
