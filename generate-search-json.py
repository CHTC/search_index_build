from bs4 import BeautifulSoup
import json
from util import path_to_soup, get_valid_paths, get_root_relative_url, string_to_file
import sys


def clean_term(term: str):
    return term


def soup_to_dict(soup: BeautifulSoup, key_tags: list) -> dict:
    """
    Iterates through the DOM tags by order of precedence, set by key_tags,
    destroying the tags it has seen to prevent duplicate content.
    :param soup: The Beautiful soup DOM object
    :param key_tags: A list of tuples that take the form -> ("tag_key", (tag1, tag2))
                     where "tag_key" acts as the key in the page index to the text in
                     the provided tags
    :return: A dictionary object with keys "root_relative_url" as the id,
             tag_keys as keys to their corresponding content,
             and "content" as the key to the remaining content
    """

    page = {}
    page['root_relative_url'] = soup.root_relative_url

    for key, values in key_tags:
        page[key] = []

        for value in values:

            for tag in soup.find_all(value):

                for term in tag.get_text().split():
                    fresh_term = clean_term(term)
                    page[key].append(fresh_term)

                tag.decompose()

        page[key] = " ".join(page[key])

    try:
        page['content'] = " ".join(soup.find("main").get_text().split())

    except:
        try:
            page['content'] = " ".join(soup.get_text().split())
        except:
            pass

    return page


def generate_search_json(site_root_dir: str, exclude_paths: list, output_dir: str, key_tags: list):
    """
    Generates the json file to be indexed by lunr.js
    :param output_dir: Where the output json should be put
    :param site_root_dir: The root of the generated site
    :param exclude_paths: Paths to exclude based on glob syntax
    :param key_tags: The html tags that should be extracted as separate components ( usefule for search emphasis )
    :return: Json file ready to be indexed
    """

    valid_paths = get_valid_paths(site_root_dir, exclude_paths)

    soups = []
    for path in valid_paths:
        soup = path_to_soup(path)
        setattr(soup, "root_relative_url", get_root_relative_url(site_root_dir, path))
        soups.append(soup)

    dicts = [soup_to_dict(soup, key_tags) for soup in soups]
    search_json = json.dumps(dicts)

    string_to_file("./search_json.json", search_json)


def main():
    site_root_dir = sys.argv[1]
    exclude_paths = json.loads(sys.argv[2])
    key_tags = json.loads(sys.argv[4])

    generate_search_json(site_root_dir, exclude_paths, key_tags)


if __name__ == '__main__':
    main()
