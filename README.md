[![Read the documentation](https://img.shields.io/badge/Read-the%20docs-green.svg)](https://opengisch.github.io/QgisModelBaker/)
[![Release](https://img.shields.io/github/release/opengisch/QgisModelBaker.svg)](https://github.com/opengisch/QgisModelBaker/releases)
[![Build Status](https://travis-ci.org/opengisch/QgisModelBaker.svg?branch=master)](https://travis-ci.com/opengisch/QgisModelBaker)

![logo](branding/logo/long_logo/Long-Logo_Green_Modelbaker_RGB_QGIS.png)

This is a QGIS plugin to quickly generate [QGIS](https://www.qgis.org) projects
from an existing model with a few mouseclicks.

Configuring QGIS layers and forms manually is a tedious and error prone process.
This plugin loads database schemas with various meta information to preconfigure the
layer tree, widget configuration, relations and more.

[INTERLIS](https://en.wikipedia.org/wiki/INTERLIS) models contain more information than a plain database schema. This
plugin uses [ili2pg](https://github.com/claeis/ili2db#ili2db---importsexports-interlis-transfer-files-to-a-sql-db) to import an INTERLIS model into a PostGIS database and uses
the additional meta information to configure the user interface even better.

[Read the documentation](https://opengisch.github.io/QgisModelBaker/) for more information.

## Translating the plugin

We love to be multilingual!

Translating the plugin is done on
[Transifex](https://explore.transifex.com/search/?q=model%20baker). If
you would like to help translating this plugin into an existing or a new language,
please create a Transifex account and request access to the team. Find the documentation [here](https://opengisch.github.io/QgisModelBaker/about/translation/)

## Infos for Devs

### The modelbaker library

The whole backend library used by this plugin here can be found [here](https://github.com/opengisch/QgisModelBakerLibrary). It's distributed on [PYPI as a package](https://pypi.org/project/modelbaker/) as well.

### Code style

Is enforced with pre-commit. To use, make:
```
pip install pre-commit
pre-commit install
```
And to run it over all the files (with infile changes):
```
pre-commit run --color=always --all-file
```

### Needed packages from PyPI

Needed packages from PyPI are downloaded and packaged on deployment to the plugin's libs folder.

Run the script to download and unpack them or install them to your system.

Script:
```
./scripts/package_pip_packages.sh
```
