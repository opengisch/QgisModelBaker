[![Read the documentation](https://img.shields.io/badge/Read-the%20docs-green.svg)](https://opengisch.github.io/QgisModelBaker/docs/en/)
[![Release](https://img.shields.io/github/release/opengisch/QgisModelBaker.svg)](https://github.com/opengisch/QgisModelBaker/releases)
[![Build Status](https://travis-ci.org/opengisch/QgisModelBaker.svg?branch=master)](https://travis-ci.com/opengisch/QgisModelBaker)

# QGIS Model Baker

This is a QGIS plugin to quickly generate [QGIS](https://www.qgis.org) projects
from an existing model with a few mouseclicks.

Configuring QGIS layers and forms manually is a tedious and error prone process.
This plugin loads database schemas with various meta information to preconfigure the
layer tree, widget configuration, relations and more.

[Interlis](https://en.wikipedia.org/wiki/Interlis) models contain more information than a plain database schema. This
plugin uses [ili2pg](https://github.com/claeis/ili2db#ili2db---importsexports-interlis-transfer-files-to-a-sql-db) to import an Interlis model into a PostGIS database and uses
the additional meta information to configure the user interface even better.

[Read the documentation](https://opengisch.github.io/QgisModelBaker/docs/en/) for more information.

## Translating the plugin

We love to be multilingual!

Translating the plugin is done on
[Transifex](https://www.transifex.com/opengisch/QgisModelBaker/languages/). If
you would like to help translating this plugin into an existing or a new language,
please create a Transifex account and request access to the team.
