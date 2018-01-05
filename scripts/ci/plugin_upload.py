#!/usr/bin/env python
# coding=utf-8
"""This script uploads a plugin package to the repository.
        Authors: A. Pasotti, V. Picavet
        git sha              : $TemplateVCSFormat
"""
from __future__ import print_function
from future import standard_library

import sys
import getpass
import xmlrpc.client
import json
import http.client
import os
from optparse import OptionParser

standard_library.install_aliases()

# Configuration
PROTOCOL = 'https'
SERVER = 'plugins.qgis.org'
PORT = '443'
ENDPOINT = '/plugins/RPC2/'
VERBOSE = False


def main(parameters, arguments):
    """Main entry point.

    :param parameters: Command line parameters.
    :param arguments: Command line arguments.
    """
    filename = arguments[0]
    address = "{protocol}://{username}:{password}@{server}:{port}{endpoint}".format(
        protocol=PROTOCOL,
        username=parameters.username,
        password=parameters.password,
        server=parameters.server,
        port=parameters.port,
        endpoint=ENDPOINT)

    server = xmlrpc.client.ServerProxy(address, verbose=VERBOSE)

    try:
        with open(filename, 'rb') as handle:
            plugin_id, version_id = server.plugin.upload(
                xmlrpc.client.Binary(handle.read()))
        print("Plugin ID: %s" % plugin_id)
        print("Version ID: %s" % version_id)
    except xmlrpc.client.ProtocolError as err:
        print("A protocol error occurred")
        print("URL: %s" % hide_password(err.url, 0))
        print("HTTP/HTTPS headers: %s" % err.headers)
        print("Error code: %d" % err.errcode)
        print("Error message: %s" % err.errmsg)
    except xmlrpc.client.Fault as err:
        print("A fault occurred")
        print("Fault code: %d" % err.faultCode)
        print("Fault string: %s" % err.faultString)

    conn = http.client.HTTPSConnection('api.github.com')
    headers = {
        'User-Agent': 'Deploy-Script',
        'Authorization': 'token {}'.format(os.environ['OAUTH_TOKEN'])
    }

    raw_data = {
        "tag_name": parameters.release
    }
    if parameters.changelog:
        with open(parameters.changelog, 'r') as cl:
            raw_data['body'] = cl.read()
    data = json.dumps(raw_data)
    conn.request('POST', '/repos/{repo_slug}/releases'.format(
        repo_slug=os.environ['TRAVIS_REPO_SLUG']), body=data, headers=headers)
    response = conn.getresponse()
    release = json.loads(response.read().decode())
    print(release)

    conn = http.client.HTTPSConnection('uploads.github.com')
    headers['Content-Type'] = 'application/zip'
    url = '{}?name={}'.format(release['upload_url'][:-13], filename)
    print('Upload to {}'.format(url))

    with open(filename, 'rb') as f:
        conn.request('POST', url, f, headers)

    print(conn.getresponse().read())


def hide_password(url, start=6):
    """Returns the http url with password part replaced with '*'.

    :param url: URL to upload the plugin to.
    :type url: str

    :param start: Position of start of password.
    :type start: int
    """
    start_position = url.find(':', start) + 1
    end_position = url.find('@')
    return "%s%s%s" % (
        url[:start_position],
        '*' * (end_position - start_position),
        url[end_position:])


if __name__ == "__main__":
    parser = OptionParser(usage="%prog [options] plugin.zip")
    parser.add_option(
        "-w", "--password", dest="password",
        help="Password for plugin site", metavar="******")
    parser.add_option(
        "-u", "--username", dest="username",
        help="Username of plugin site", metavar="user")
    parser.add_option(
        "-p", "--port", dest="port",
        help="Server port to connect to", metavar="80")
    parser.add_option(
        "-s", "--server", dest="server",
        help="Specify server name", metavar="plugins.qgis.org")
    parser.add_option(
        "-r", "--release", dest="release",
        help="Specify the release name", metavar="v1.0.0")
    parser.add_option(
        "-c", "--changelog", dest="changelog",
        help="Specify the changelog file", metavar="/tmp/changelog")
    options, args = parser.parse_args()
    if len(args) != 1:
        print("Please specify zip file.\n")
        parser.print_help()
        sys.exit(1)
    if not options.server:
        options.server = SERVER
    if not options.port:
        options.port = PORT
    if not options.username:
        # interactive mode
        username = getpass.getuser()
        print("Please enter user name [%s] :" % username, end=' ')
        # this may not be present in the QGIS python, so since this module is not used for the plugin
        # import dynamically so as to not break the plugin in QGIS
        from builtins import input

        res = input()
        if res != "":
            options.username = res
        else:
            options.username = username
    if not options.password:
        # interactive mode
        options.password = getpass.getpass()
    main(options, args)
