#!/usr/bin/env python

import argparse
import copy

from ruamel.yaml import YAML

# This scripts helps with translatable content from mkdocs.yml
# It provides commands:
#   * to create the YAML translatable file
#   * to update the mkdocs.yml with the translated content


def read_config(file_path: str):
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    with open(file_path) as f:
        return yaml.load(f)


def nav_config(config):
    _nav_config = []

    def add_nav_entry(_title, _content):
        if type(_content) == str:
            _nav_config.append(_title)
        else:
            for _entry in _content:
                for title, content in _entry.items():
                    add_nav_entry(title, content)

    add_nav_entry(None, config["nav"])

    return _nav_config


def create_translation_source(config_path, source_path):
    config = read_config(config_path)

    tx_cfg = {"nav": nav_config(config)}

    try:
        tx_cfg["theme"] = {"palette": []}
        for palette in config["theme"]["palette"]:
            tx_cfg["theme"]["palette"].append(
                {"toggle": {"name": palette["toggle"]["name"]}}
            )
    except KeyError:
        print("No theme/palette/toggle/name to translate")

    with open(source_path, "w") as f:
        yaml = YAML()
        yaml.dump(tx_cfg, f)


def update_config(config_path, source_path, source_language):
    config = read_config(config_path)
    _nav_config = nav_config(config)

    found = False
    for plugin in config["plugins"]:
        if type(plugin) != str and "i18n" in plugin:
            found = True
            for lang in plugin["i18n"]["languages"]:
                ltx = lang["locale"]
                print(f"language found: '{ltx}'")

                if ltx == source_language:
                    print("skipping source language")
                    continue

                tx_file = f'{source_path.removesuffix(".yml")}.{ltx}.yml'
                with open(tx_file) as f:
                    yaml = YAML()
                    tx = yaml.load(f)

                    assert len(_nav_config) == len(tx["nav"])

                    lang["nav_translations"] = {}
                    for i in range(len(tx["nav"])):
                        lang["nav_translations"][_nav_config[i]] = (
                            tx["nav"][i] or _nav_config[i]
                        )

                    try:
                        lang["palette"] = copy.deepcopy(config["theme"]["palette"])
                        i = 0
                        for palette in tx["theme"]["palette"]:
                            _name = (
                                palette["toggle"]["name"]
                                or config["theme"]["palette"][i]["toggle"]["name"]
                            )
                            lang["palette"][i]["toggle"]["name"] = _name
                            i += 1
                    except KeyError:
                        print("No theme/palette/toggle/name to translate")

    assert found

    with open(config_path, "w") as f:
        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        yaml.dump(config, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config_path", default="mkdocs.yml", help="mkdocs.yml complete path"
    )
    parser.add_argument(
        "-s", "--source_language", default="en", help="source language of the config"
    )
    parser.add_argument(
        "-t",
        "--translation_file_path",
        default="mkdocs_tx.yml",
        help="Translation file to create and translate",
    )

    subparsers = parser.add_subparsers(title="command", dest="command")

    # create the parser for the create_source command
    parser_source = subparsers.add_parser(
        "create_source", help="Creates the source file to be translated"
    )

    # create the parser for the update_config command
    parser_update = subparsers.add_parser(
        "update_config",
        help="Updates the mkdocs.yml config file from the downloaded translated files",
    )

    args = parser.parse_args()

    if args.command == "create_source":
        create_translation_source(args.config_path, args.translation_file_path)

    elif args.command == "update_config":
        update_config(
            args.config_path, args.translation_file_path, args.source_language
        )

    else:
        raise ValueError
