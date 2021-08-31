# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 5.1.2017
        git sha              : :%H$
        copyright            : (C) 2017 by OPENGIS.ch
        email                : matthias@opengis.ch
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

import yaml


def extend_constructor(loader, node):
    """
    Return an ExtendObject. This will be used in a post-processing step
    to extend the base object.
    """
    return ExtendObject(node)


# Register the '<<<' syntax with our custom constructor
yaml.add_implicit_resolver(
    "tag:opengis.ch,2016:extend", re.compile(r"^(?:<<<)$"), ["<"]
)

yaml.add_constructor("tag:opengis.ch,2016:extend", extend_constructor)


class ExtendObject(object):
    """
    The ExtendObject will be used as a placeholder for the loading time
    """

    def __init__(self, data):
        self.data = data


class YamlReaderError(RuntimeError):
    pass


class InheritanceLoader(yaml.Loader):
    def __init__(self, stream):
        yaml.Loader.__init__(self, stream)

    """
    We override the main entry point
    """

    def get_single_data(self):
        data = yaml.Loader.get_single_data(self)
        return self.recursive_extend(data)

    def recursive_extend(self, item):
        if isinstance(item, list):
            return [self.recursive_extend(data) for data in item]
        elif isinstance(item, dict):
            result = {}
            base = None
            for key, value in item.items():
                if isinstance(key, ExtendObject):
                    base = value
                else:
                    result[key] = self.recursive_extend(value)

            if base:
                self.data_merge(result, base)

            return result
        elif isinstance(item, ExtendObject):
            return "ay"
        else:
            return item

    @classmethod
    def data_merge(cls, a, b):
        """merges b into a and return merged result

        NOTE: tuples and arbitrary objects are not handled as it is totally ambiguous what should happen"""
        key = None
        # ## debug output
        # sys.stderr.write("DEBUG: %s to %s\n" %(b,a))
        try:
            if (
                a is None
                or isinstance(a, str)
                or isinstance(a, int)
                or isinstance(a, float)
            ):
                # border case for first run or if a is a primitive
                a = b
            elif isinstance(a, list):
                # lists can be only appended
                if isinstance(b, list):
                    # merge lists
                    a.extend(b)
                else:
                    # append to list
                    a.append(b)
            elif isinstance(a, dict):
                # dicts must be merged
                if isinstance(b, dict):
                    for key in b:
                        if key in a:
                            a[key] = cls.data_merge(a[key], b[key])
                        else:
                            a[key] = b[key]
                else:
                    raise YamlReaderError(
                        'Cannot merge non-dict "%s" into dict "%s"' % (b, a)
                    )
            else:
                raise YamlReaderError('NOT IMPLEMENTED "%s" into "%s"' % (b, a))
        except TypeError as e:
            raise YamlReaderError(
                'TypeError "%s" in key "%s" when merging "%s" into "%s"'
                % (e, key, b, a)
            )
        return a
