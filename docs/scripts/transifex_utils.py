#!/usr/bin/env python

import glob
import os

from slugify import slugify

TX_ORGANIZATION = "opengisch"
TX_PROJECT = "qgis-model-baker-docs"
TX_SOURCE_LANG = "en"
TX_TYPE = "GITHUBMARKDOWN"


def create_transifex_config():
    """Parse all source documentation files and add the ones with tx_slug metadata
    defined to transifex config file.
    """
    print("Start creating transifex configuration")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(current_dir, "..", "..", ".tx", "config")
    root = os.path.join(current_dir, "..", "..")
    count = 0

    with open(config_file, "w") as f:
        f.write("[main]\n")
        f.write("host = https://www.transifex.com\n\n")

        for file in glob.iglob(current_dir + "/../**/*.md", recursive=True):
            # Get relative path of file
            relative_path = os.path.relpath(file, start=root)

            tx_slug = slugify(os.path.splitext(relative_path)[0])

            if (
                tx_slug and relative_path.count(".") == 1
            ):  # if no dots defining language (to filter out the indes.de.md etc.)
                print(f"Found file with tx_slug defined: {relative_path}, {tx_slug}")
                f.write(f"[o:{TX_ORGANIZATION}:p:{TX_PROJECT}:r:{tx_slug}]\n")
                f.write(
                    f"file_filter = {os.path.splitext(relative_path)[0]}.<lang>.md\n"
                )
                f.write(f"source_file = {relative_path}\n")
                f.write(f"source_lang = {TX_SOURCE_LANG}\n")
                f.write(f"type = {TX_TYPE}\n\n")
                count += 1

    print(f"Transifex configuration created: {count} resources added.")


create_transifex_config()
