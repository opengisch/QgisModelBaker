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

import datetime

from QgisModelBaker.internal_libs.toppingmaker import Target


class IliTarget(Target):
    """
    Target extension of standard toppingmaker containing additional parameters like owner, publishing_date and version.
    """

    def __init__(
        self,
        projectname: str = "project",
        main_dir: str = None,
        sub_dir: str = None,
        path_resolver=None,
        owner="owner",
        publishing_date=None,
        version=None,
    ):
        super().__init__(projectname, main_dir, sub_dir, path_resolver)
        self.default_owner = owner
        self.default_publishing_date = (
            publishing_date or datetime.datetime.now().strftime("%Y-%m-%d")
        )
        self.default_version = version or datetime.datetime.now().strftime("%Y-%m-%d")
