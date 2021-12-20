import math
from bs4 import BeautifulSoup
import json
from util import path_to_soup, get_valid_paths, get_root_relative_url, string_to_file
import sys
import glob
import datetime
import re

site_root_dir = ""
path_boost_directory = {}
character_boost_directory = {}

OUTPUT_DIR = "./documents.json"


def clean_term(term: str):
    """
    Can be used to clean the term
    :param term: The term to clean
    :return: The clean term
    """
    return term


def path_to_soup_ext(path):
    global site_root_dir
    soup = path_to_soup(path)
    setattr(soup, "root_relative_url", get_root_relative_url(site_root_dir, path))
    setattr(soup, "path", path)
    if soup.find("meta", {'http-equiv': 'date'}):
        setattr(soup, "date", soup.find("meta", {'http-equiv': 'date'})['content'])
    return soup


def expand_glob_list(glob_paths: list) -> set:
    paths = set()
    for glob_path in glob_paths:
        paths.update(glob.glob(f"{site_root_dir}/{glob_path}"))

    return paths


def get_char_boosts_directory(char_boosts_globs: dict) -> dict:
    global site_root_dir

    char_boosts = {}
    for char_boosts_glob in char_boosts_globs:
        key, paths = list(char_boosts_glob.items())[0]
        char_boosts[key] = expand_glob_list(paths)

    return char_boosts


def get_path_boosts_directory(doc_boosts_globs: dict) -> dict:
    """
    Expands the glob paths in a dict of form  into sets
    so that a docs boost value can be queried
    :param doc_boosts: dict of form {<boost int>: ["glob_path"], <boost int>:["glob_path"]}
    :return: dict of form {<boost int>: set("/root/**expanded_path**)}
    """
    global site_root_dir

    doc_boosts = {}
    for doc_boosts_glob in doc_boosts_globs:
        key, paths = list(doc_boosts_glob.items())[0]
        doc_boosts[key] = expand_glob_list(paths)

    return doc_boosts


def get_explicit_document_boost(doc: dict):
    """
    Gets the average of all the boosts to be applied to this document from the user path entry
    :param document_boosts: dict of {boost: [paths]}
    :param doc: The dict containing the document attributes
    :return: The boost to be applied from this method
    """
    global path_boost_directory

    boost_matches = []
    for key, paths in path_boost_directory.items():
        if doc['path'] in paths:
            boost_matches.append(int(key))

    if boost_matches:
        return round(sum(boost_matches) / len(boost_matches))
    else:
        return 5  # If it was not addressed then give it the average boost value


def get_time_document_boost(document: dict):
    """
    Weight this document based on its date meta tag
    Boost is ~10 if recent, 5 ( average ) if 4 years old, ~1 if => 8
    :param document: A dict
    :return: The boost int
    """

    def sigmoid(z):
        return 1 / (1 + math.e ** (z * -1))

    if not document['date']:
        return 5

    current_year = int(datetime.datetime.now().strftime("%Y"))
    document_year = int(datetime.datetime.strptime(document['date'], "%Y-%m-%d %H:%M:%S %z").strftime("%Y"))

    z = document_year - current_year + 1

    boost = math.ceil(sigmoid(z) * 10)

    return boost


def get_document_boost(document: dict):
    """
    Calculates the amount that a document should be boosted.
    :return: The amount to boost this document
    """

    boosts = []

    boosts.append(get_explicit_document_boost(document))

    if "time" in character_boost_directory and document['path'] in character_boost_directory['time']:
        boosts.append(get_time_document_boost(document))

    return round(sum(boosts) / len(boosts))


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
    page['path'] = soup.path  # Set this to use as the ref later
    page['root_relative_url'] = soup.root_relative_url  # Set this to use as the ref later
    page['date'] = soup.date  # Set this to use as the ref later

    # Iterate through the key_tags in order of precedence stripping out their content into the doc
    for key_tags_pair in key_tags:
        key, values = list(key_tags_pair.items())[0]

        page[key] = []

        for value in values:

            for tag in soup.find_all(value):

                for term in tag.get_text().split():
                    fresh_term = clean_term(term)
                    page[key].append(fresh_term)

                tag.decompose()

        page[key] = " ".join(page[key])

    # Put the remaining content into a base 'content' section
    try:
        # Try to just extract just the main content if possible
        page['content'] = " ".join(soup.find("main").get_text().split())

    except:
        try:
            # Fallback on getting all the pages text
            page['content'] = " ".join(soup.get_text().split())
        except:
            page['content'] = ""

    return page


def generate_search_json(exclude_paths: list, key_tags: list, file_terms: dict):
    """
    Generates the json file to be indexed by lunr.js
    :param exclude_paths: Paths to exclude based on glob syntax
    :param key_tags: The html tags that should be extracted as separate components ( useful for search emphasis )
    :param file_terms: List of dicts of form {"file_path" : "term0 term1 term2"}
    :return: Json file ready to be indexed
    """

    valid_paths = get_valid_paths(site_root_dir, exclude_paths)
    print(valid_paths)

    soups = [path_to_soup_ext(path) for path in valid_paths]
    documents = [soup_to_dict(soup, key_tags) for soup in soups]

    # Add the user defined documents
    for document in documents:

        for file, terms in file_terms.items():
            if re.search(file, document['root_relative_url']) is not None:
                document["file_terms"] = terms
            else:
                document["file_terms"] = None

    boosted_documents = [{'document': document, 'boost': get_document_boost(document)} for document in documents]
    search = boosted_documents
    search_json = json.dumps(boosted_documents)

    string_to_file(OUTPUT_DIR, search_json)

    return search


def get_stats(search):
    doc_boosts = [doc['boost'] for doc in search]
    print(f"Average Document Boost: {sum(doc_boosts) / len(doc_boosts)}")


def main():
    """
    Open the args file and begin the generation
    """
    global site_root_dir
    global path_boost_directory
    global character_boost_directory

    with open(sys.argv[1], "r") as fp:
        args = json.load(fp)

    site_root_dir = args["site_root"]

    if "path_boosts" in args:
        path_boost_directory = get_path_boosts_directory(args['path_boosts'])

    if "char_boosts" in args:
        character_boost_directory = get_char_boosts_directory(args['char_boosts'])

    exclude_paths = []
    if "exclude_paths" in args:
        exclude_paths = args["exclude_paths"]

    key_tags = []
    if "key_tags" in args:
        key_tags = args["key_tags"]

    file_terms = []
    if "file_terms" in args:
        file_terms = args["file_terms"]

    search_json = generate_search_json(exclude_paths, key_tags, file_terms)

    get_stats(search_json)


if __name__ == '__main__':
    main()
