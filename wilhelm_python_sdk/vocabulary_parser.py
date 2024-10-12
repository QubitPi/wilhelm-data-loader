# Copyright Jiaqi (Hutao of Emberfire)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
import re

import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

GERMAN = "German"
LATIN = "Latin"
ANCIENT_GREEK = "Ancient Greek"

EXCLUDED_DECLENSION_ENTRIES = [
    "",
    "singular",
    "plural",
    "masculine",
    "feminine",
    "neuter",
    "nominative",
    "genitive",
    "dative",
    "accusative",
    "N/A"
]


def get_vocabulary(yaml_path: str) -> list:
    with open(yaml_path, "r") as f:
        return yaml.safe_load(f)["vocabulary"]


def get_definitions(word) -> list[(str, str)]:
    """
    Extract definitions from a word as a list of bi-tuples, with the first element being the predicate and the second
    being the definition.

    For example::

    definition:
      - term: nämlich
        definition:
          - (adj.) same
          - (adv.) namely
          - because

    The method will return `[("adj.", "same"), ("adv.", "namely"), (None, "because")]`

    The method works for the single-definition case, i.e.::

    definition:
      - term: na klar
        definition:

    returns a list of one tupple `[(None, "of course")]`

    Note that any definition are converted to string. If the word does not contain a field named exactly "definition", a
    ValueError is raised.

    :param word:  A dictionary that contains a "definition" key whose value is either a single-value or a list of
                  single-values
    :return: a list of two-element tuples, where the first element being the predicate (can be `None`) and the second
             being the definition
    """
    logging.info("Extracting definitions from {}".format(word))

    if "definition" not in word:
        raise ValueError("{} does not contain 'definition' field. Maybe there is a typo".format(word))

    predicate_with_definition = []

    definitions = [word["definition"]] if not isinstance(word["definition"], list) else word["definition"]

    for definition in definitions:
        definition = str(definition)

        definition = definition.strip()

        match = re.match(r"\((.*?)\)", definition)
        if match:
            predicate_with_definition.append((match.group(1), re.sub(r'\(.*?\)', '', definition).strip()))
        else:
            predicate_with_definition.append((None, definition))

    return predicate_with_definition


def get_declension_attributes(word: object) -> dict[str, str]:
    """
    Returns noun-specific attributes as a flat map.

    If the noun's declension is, for some reasons, "Unknown", this function will return an empty dict. Otherwise, the
    declension table is flattened like with row-col index in the map key::

    "declension-0-0": "",
    "declension-0-1": "singular",
    "declension-0-2": "singular",
    "declension-0-3": "singular",
    "declension-0-4": "plural",
    "declension-0-5": "plural",

    :param word:  A vocabulary represented in YAML dictionary which has a "declension" key

    :return: a flat map containing all the YAML encoded information about the noun excluding term and definition
    """

    declension = word["declension"]

    if declension == "Unknown":
        return {}

    attributes = {}
    for i, row in enumerate(declension):
        for j, col in enumerate(row):
            attributes[f"declension-{i}-{j}"] = declension[i][j]

    return attributes


def get_attributes(word: object, language: str, node_label_property_key: str) -> dict[str, str]:
    """
    Returns a flat map as the Term node properties stored in Neo4J.

    :param word:  A German vocabulary representing

    :return: a flat map containing all the YAML encoded information about the vocabulary
    """
    attributes = {node_label_property_key: word["term"], "language": language}

    if "declension" in word:
        attributes = attributes | get_declension_attributes(word)

    return attributes


def get_inferred_links(vocabulary: list[dict], label_key: str) -> list[dict]:
    link_hints = {}
    for word in vocabulary:
        attributes = get_attributes(word, GERMAN, label_key)

        link_hints = update_link_hints(link_hints, attributes, word["term"])

    inferred_links = []
    for word in vocabulary:
        term = word["term"]
        attributes = get_attributes(word, GERMAN, label_key)

        for attribute_value in attributes.values():
            if (attribute_value in link_hints) and (term != link_hints[attribute_value]):
                inferred_links.append({
                    "source_label": term,
                    "target_label": link_hints[attribute_value],
                    "attributes": {label_key: f"sharing declensions: {link_hints[attribute_value]}"},
                })

    return inferred_links


def update_link_hints(link_hints: dict[str, str], attributes: dict[str, str], term: str):
    """
    Update and prepare a mapping between shared attribute values (key) to the term that has that attribute (value).

    This mapping will be used to create more links in graph database.

    The operation calling this method was inspired by the spotting the relationship between "die Reise" and "der Reis"
    who share large portions of their declension table. In this case, there will be a link between "die Reise" and
    "der Reis". Linking the vocabulary this way helps memorize vocabulary more efficiently

    :param link_hints:  The mapping
    :param attributes:  The source of mapping hints
    :param term:  the term that has the attribute
    """
    for key, value in attributes.items():
        if key.startswith("declension-") and value not in EXCLUDED_DECLENSION_ENTRIES:
            link_hints[value] = term
    return link_hints
