#!/usr/bin/env python

import sys
import os
import json
import string


class FormatError(Exception):
    pass


class Transformer(object):
    def __init__(self, input, slugs):
        self.markdown = input
        self.unseen_slugs = slugs
        self.line_index = 0
        self.character_index = 0
        self.beginning_of_name = None
        self.iterations = 0

    def _end_of_markdown(self):
        last_line = self.line_index == len(self.markdown) - 1
        last_char = self._end_of_line()

        return last_line and last_char

    def _end_of_line(self):
        return self.character_index == len(self.markdown[self.line_index]) - 1

    def _found_markdown_link(self):
        return self.markdown[self.line_index][self.character_index] == "["

    def _next_character(self):
        return self.markdown[self.line_index][self.character_index]

    def _scanning_for_name_beginning(self):
        return self.beginning_of_name is None

    def _scanning_for_name_ending(self):
        return self.beginning_of_name is not None

    def _get_current_substring(self):
        return self.markdown[self.line_index][
            self.beginning_of_name : self.character_index + 1
        ]

    def _at_name_ending(self):
        substring = self._get_current_substring()
        next_char = self.markdown[self.line_index][self.character_index + 1]
        if next_char.isalpha():
            return False
        for slug in self.unseen_slugs:
            if slugify(substring) == slug.lower():
                return True

        return False

    def _matches_unseen_slug(self, candidate):
        can_slug = slugify(candidate)
        for slug in self.unseen_slugs:
            can_len = len(can_slug)
            if can_slug == slug[:can_len]:
                return True

        return False

    def _step(self):
        self.iterations = self.iterations + 1
        if self.iterations > 100000:
            assert False

        if self._end_of_markdown():
            raise StopIteration

        if self._end_of_line():
            self.line_index = self.line_index + 1
            self.character_index = 0
            self.beginning_of_name = None
            return

        if self._found_markdown_link():
            beginning_of_link = self.character_index
            end_of_link = self.character_index
            while True:
                end_of_link = end_of_link + 1
                if self.markdown[self.line_index][end_of_link] == ")":
                    break
            link_string = self.markdown[self.line_index][
                beginning_of_link : end_of_link + 1
            ]

            if "characters/" in link_string:
                slug = link_string.split("characters/")[1].split("/")[0]
                self.unseen_slugs.pop(self.unseen_slugs.index(slug))

            self.character_index = self.character_index + len(link_string)
            return

        next_character = self._next_character()

        if self._scanning_for_name_beginning():
            if self._matches_unseen_slug(next_character):
                self.beginning_of_name = self.character_index

        elif self._scanning_for_name_ending():
            substring = self._get_current_substring()
            if not self._matches_unseen_slug(substring):
                self.beginning_of_name = None
                return

            if self._at_name_ending():
                slug = self.unseen_slugs.pop(
                    self.unseen_slugs.index(slugify(substring))
                )
                link_string = "[{}](/characters/{}/)".format(substring, slug)
                before = self.markdown[self.line_index][: self.beginning_of_name]
                after = self.markdown[self.line_index][self.character_index + 1 :]
                new_line = before + link_string + after
                new_index = len(before + link_string)
                self.markdown[self.line_index] = new_line
                self.character_index = new_index
                return

        self.character_index = self.character_index + 1

    def transform(self):
        while True:
            try:
                self._step()
            except StopIteration:
                break

        return self.markdown


def transform(input_markdown, slugs):
    input_slugs = slugs.copy()
    t = Transformer(input=input_markdown, slugs=slugs)
    text = t.transform()
    found_slugs = [s for s in input_slugs if s not in t.unseen_slugs]
    return found_slugs, text


def get_base_dir():
    file_path = os.path.realpath(__file__)
    script_dir = os.path.dirname(file_path)
    return os.path.split(script_dir)[0]


def find_json_boundaries(content):
    beginning_of_json = None
    end_of_json = None

    for i, l in enumerate(content):
        if l.strip() == "{":
            beginning_of_json = i
            break

    for i, l in enumerate(content):
        if l.strip() == "}" and beginning_of_json is not None:
            end_of_json = i + 1

    if beginning_of_json is None or end_of_json is None:
        raise FormatError()

    return beginning_of_json, end_of_json


def slugify(input):
    exclude = set(string.punctuation)
    cleaned = "".join(ch for ch in input if ch not in exclude)
    return cleaned.replace(" ", "-").lower()


def extract_character_data(char_dir):
    paths = [
        os.path.join(char_dir, filename)
        for filename in os.listdir(char_dir)
        if filename != "_index.md"
    ]

    characters = []
    for path in paths:
        with open(path) as infile:
            content = infile.readlines()

        beginning_of_json, end_of_json = find_json_boundaries(content)
        json_string = "".join(content[beginning_of_json:end_of_json])
        serialized = json.loads(json_string)
        if "slug" not in serialized:
            serialized["slug"] = slugify(serialized["title"])
        characters.append(serialized)

    return characters


def get_content_paths(content_dir):
    paths = []
    for root, dirs, files in os.walk(content_dir):
        for filename in files:
            if filename == "_index.md":
                continue
            if filename[-3:] != ".md":
                continue
            paths.append(os.path.join(root, filename))

    return paths


def find_matching_name(word, characters, mentioned):
    for char in characters:
        if mentioned[char["slug"]]:
            continue
        if word.lower() == char["title"].split(" ")[0].lower():
            return char["slug"]
        # TODO 's form etc

    return False


def generate_md_link(slug, name_parts):
    name = "".join(name_parts)
    return "[{}](/characters/{})".format(name, slug)


def ensure_cross_link(chapter_path, characters):
    with open(chapter_path) as infile:
        content = infile.readlines()

    beginning_of_json, end_of_json = find_json_boundaries(content)
    json_string = "".join(content[beginning_of_json:end_of_json])

    try:
        front_matter = json.loads(json_string)
    except json.decoder.JSONDecodeError:
        print(json_string)
        print("can't decode json: {}".format(chapter_path))
        sys.exit(1)

    original_markdown = content[end_of_json:]

    if not original_markdown:
        print("empty content, skipping {}".format(chapter_path))
        return None

    character_slugs = [c["slug"] for c in characters]

    found_slugs, new_markdown = transform(original_markdown, character_slugs)
    front_matter["appearances"] = found_slugs
    if front_matter.get("chapter"):
        try:
            front_matter["appearances_weight"] = int(front_matter["chapter"]) * 10
        except ValueError as err:
            if front_matter["chapter"] == "26: Part I":
                front_matter["appearances_weight"] = 260
            elif front_matter["chapter"] == "26: Part II":
                front_matter["appearances_weight"] = 265
            else:
                raise err
    elif front_matter.get("timestamp"):
        front_matter["appearances_weight"] = int(
            front_matter["timestamp"].replace("-", "")
        )

    with open(chapter_path, "w") as outfile:
        json.dump(front_matter, outfile, sort_keys=True, indent=4, ensure_ascii=False)
        outfile.write("\n")
        [outfile.write(l) for l in new_markdown]


def main():
    base_dir = get_base_dir()
    char_dir = os.path.join(base_dir, "southside/content/characters")
    characters = extract_character_data(char_dir)

    for content_type in ["chapters", "hanamir-case-files"]:
        content_dir = os.path.join(
            base_dir, "southside/content/{}".format(content_type)
        )
        content_paths = get_content_paths(content_dir)
        for content in content_paths:
            ensure_cross_link(content, characters)


if __name__ == "__main__":
    main()
