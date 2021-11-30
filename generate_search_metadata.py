from bs4 import BeautifulSoup
import json
from util import path_to_soup, get_valid_paths, get_root_relative_url, string_to_file
import sys

def get_title(soup: BeautifulSoup) -> str:
    """
    Look through the DOM object for a page title by order of tag precedence
    :param soup: The Beautiful soup DOM object
    :return: title
    """

    # If title Meta Data is set use it
    if soup.find("title") is not None:
        return soup.find("title").get_text()

    if soup.find("h1") is not None:
        return soup.find("h1").get_text()

    if soup.find("h2") is not None:
        return soup.find("h2").get_text()

    if soup.find("h3") is not None:
        return soup.find("h3").get_text()

    if soup.find("h4") is not None:
        return soup.find("h4").get_text()

    if soup.find("h4") is not None:
        return soup.find("h4").get_text()

    if soup.find("h5") is not None:
        return soup.find("h5").get_text()

    print(f"Cannot find a title on page : {soup.root_relative_url}")


def get_meta_data(soup: BeautifulSoup):
    title = get_title(soup)

    return {
        "title": title
    }


def generate_search_metadata(site_root_dir: str, output_dir: str, exclude_paths: list):
    """
    Generates the json file to be indexed by lunr.js
    :param output_dir: Where the output json should be put
    :param site_root_dir: The root of the generated site
    :param exclude_paths: Paths to exclude based on glob syntax
    :return: Json file ready to be indexed
    """

    valid_paths = get_valid_paths(site_root_dir, exclude_paths)

    soups = []
    for path in valid_paths:
        soup = path_to_soup(path)
        setattr(soup, "root_relative_url", get_root_relative_url(site_root_dir, path))
        soups.append(soup)

    meta_data = {}
    for soup in soups:
        meta_data[soup.root_relative_url] = get_meta_data(soup)

    meta_data_json = json.dumps(meta_data)

    string_to_file(output_dir, meta_data_json)


def main():
    """
    Open the args file and begin the generation
    """
    with open(sys.argv[1], "r") as fp:
        args = json.load(fp)

    site_root = args["site_root"]

    exclude_paths = []
    if "exclude_paths" in args:
        exclude_paths = args["exclude_paths"]

    output_dir = args["meta_data_output"]

    generate_search_metadata(site_root, output_dir, exclude_paths)


if __name__ == '__main__':
    main()