"""
/***************************************************************************
    begin                :    18/06/19
    git sha              :    :%H$
    copyright            :    (C) 2019 by Yesid Polania (BSF Swissphoto)
    email                :    yesidpol.3@gmail.com
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
import re

import pyodbc

regex_list = ["sql.*server", "mssql", "FreeTDS"]


def get_odbc_drivers():
    result = list()
    for item in pyodbc.drivers():
        regex_sql_server = "({})".format("|".join(regex_list))

        x = re.search(regex_sql_server, item, re.IGNORECASE)

        if x:
            result.append(item)

    return result
