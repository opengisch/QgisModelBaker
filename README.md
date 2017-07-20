[![Read the documentation](https://img.shields.io/badge/Read-the%20docs-green.svg)](http://qfield.org/docs/projectgenerator/index.html)
[![Release](https://img.shields.io/github/release/opengisch/projectgenerator.svg)](https://github.com/opengisch/projectgenerator/releases)
[![Build Status](https://travis-ci.org/opengisch/projectgenerator.svg?branch=master)](https://travis-ci.org/opengisch/projectgenerator)

# Projectgenerator

This is a QGIS plugin to quickly generate QGIS projects from an existing model
with a few mouseclicks.

Configuring QGIS layers and forms manually is a tedious process.
This plugin loads database schemas with various meta information to preconfigure the
layer tree, widget configuration, relations and more.

Interlis models contain more information than a plain database schema. This
plugin uses ili2pg to import an Interlis model into a PostGIS database and uses
the additional meta information to configure the user interface even better.

## Translating the plugin

We love to be multilingual!

Translating the plugin is done on
[Transifex](https://www.transifex.com/opengisch/projectgenerator/languages/). If
you would like to help translating this plugin into an existing or a new language,
please create a Transifex account and request access to the team.
