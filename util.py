"""
This file holds the code used by both generators.
"""

import json
from bs4 import BeautifulSoup
import glob
import os


def path_to_soup(path: str) -> BeautifulSoup:
    """
    Converts a filepath to a soup object
    :param path: The path to the HTML page to parse
    :return: A Beautiful soup object
    """
    with open(path, encoding="utf8", errors='ignore', mode="r") as fp:
        return BeautifulSoup(fp, "html5lib")


def get_valid_paths(site_root_dir: str, exclude_paths: list) -> set:
    """
    Removes the intersection of valid and invalid paths
    :param site_root_dir: The directory that holds all the website files
    :param excluded_paths: RELATIVE paths to the root that shouldnt be added to search index
    :return: A set of urls to be indexed
    """
    valid = set(glob.glob(f"{site_root_dir}/**/*.html", recursive=True))

    invalid = set()

    for exclude_path in exclude_paths:
        invalid.update(glob.glob(os.path.join(site_root_dir, exclude_path), recursive=True))

    return valid - invalid


def get_root_relative_url(site_root_dir: str, path: str) -> str:
    """
    Gets the root relative url of this file.
    :param site_root_dir: The path to the web page root directory
    :param path: The path to make root relative
    :return: The root relative website page
    """

    root_relative_path = path[len(site_root_dir):]

    return root_relative_path


def string_to_file(file_path: str, string: str):
    """
    Write a string to file
    :param file_path: Where to write the file
    :param string: The string to write to the file
    """
    with open(file_path, "w") as fp:
        fp.write(string)

