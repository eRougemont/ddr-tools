#!/usr/bin/env python3
"""Restore TEI page breaks by aligning the running text of two XML files.

Requires: pip install lxml
Usage: python restore_pb.py original.xml corrected-revuNS.xml restored.xml
"""
import argparse
from bisect import bisect_left, bisect_right
from collections import Counter
from copy import deepcopy
from difflib import SequenceMatcher
from pathlib import Path
import re
import unicodedata

from lxml import etree

TEI = "{http://www.tei-c.org/ns/1.0}"
WORD = re.compile(r"[^\W_]+", re.UNICODE)


def normalized(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s.casefold())
                   if not unicodedata.combining(c))


def content(node):
    """Yield running-text fragments and pb events, excluding footnote contents."""
    if node.tag == TEI + "note":
        return
    if node.text:
        yield (node, "text", node.text)
    for child in node:
        if child.tag == TEI + "pb":
            yield (child, "pb", None)
        else:
            yield from content(child)
        if child.tail:
            yield (child, "tail", child.tail)


class TextView:
    def __init__(self, body):
        self.parts = []
        self.breaks = []
        fragments = []
        length = 0
        for element, kind, string in content(body):
            if kind == "pb":
                self.breaks.append((element, length))
            else:
                self.parts.append((length, length + len(string), element, kind))
                fragments.append(string)
                length += len(string)
        self.text = "".join(fragments)
        spans = list(WORD.finditer(self.text))
        self.starts = [m.start() for m in spans]
        self.tokens = [normalized(m.group()) for m in spans]
        self.ends = [end for _, end, _, _ in self.parts]

    def at(self, char_index):
        part_i = bisect_right(self.ends, char_index)
        start, end, element, kind = self.parts[part_i]
        return element, kind, char_index - start


def matching_positions(old_tokens, new_tokens):
    blocks = SequenceMatcher(None, old_tokens, new_tokens, autojunk=True).get_matching_blocks()
    positions = {}
    for i, j, size in blocks:
        for offset in range(size):
            positions[i + offset] = j + offset
    return positions, blocks


def page_position(token_index, old_tokens, new_tokens, matches):
    """Find the target position of the first word following a source page break."""
    if token_index in matches:
        return matches[token_index], "exact"
    if token_index == len(old_tokens):
        return len(new_tokens), "end"

    left = token_index - 1
    while left >= 0 and left not in matches:
        left -= 1
    right = token_index + 1
    while right < len(old_tokens) and right not in matches:
        right += 1

    if left < 0:
        return (matches[right] if right < len(old_tokens) else 0), "estimated"
    if right == len(old_tokens):
        return matches[left] + 1, "estimated"

    # Prefer the right anchor when source words following the page break
    # were corrected; the left anchor otherwise. Flag genuine uncertainty.
    left_pos = matches[left] + 1
    right_pos = matches[right]
    if right_pos == left_pos:
        return right_pos, "gap (unambiguous)"
    if token_index == left + 1:
        return left_pos, "gap (left anchor)"
    if token_index == right:
        return right_pos, "gap (right anchor)"
    fraction = (token_index - left) / (right - left)
    return round(left_pos + fraction * (right_pos - left_pos)), "estimated"


def add_page_break(target, place, original_pb, old_parent_tag):
    """Insert a page break without changing the corrected text content."""
    if place == len(target.tokens):
        raise ValueError("Page break after the final word needs manual placement")
    text_index = target.starts[place]
    element, field, offset = target.at(text_index)
    pb = deepcopy(original_pb)
    pb.tail = None

    # For original breaks at division level, preserve division-level placement
    # when the target also starts a heading or paragraph at this word.
    if old_parent_tag in (TEI + "div", TEI + "quote"):
        node = element if field == "text" else element.getparent()
        while node is not None and node.tag not in (TEI + "head", TEI + "p"):
            node = node.getparent()
        if node is not None:
            first = next((normalized(m.group()) for fragment in content(node)
                          if fragment[1] != "pb"
                          for m in WORD.finditer(fragment[2])), None)
            if first == target.tokens[place] and node.getparent() is not None:
                # Verify this is the first textual token of the element,
                # not just a repeated word within it.
                txt = "".join(f[2] for f in content(node) if f[1] != "pb")
                current = next(WORD.finditer(txt), None)
                if current is not None:
                    # The node must start here in the document. Find its first
                    # word's actual global position using preceding text.
                    before = 0
                    for start, end, e, k in target.parts:
                        owner = e if k == "text" else e.getparent()
                        if owner is node or node in owner.iterancestors():
                            before = start
                            break
                    else:
                        before = -1
                    if before >= 0 and target.starts[place] == before + (len(txt) - len(txt.lstrip())):
                        node.addprevious(pb)
                        return "structural"

    old_text = getattr(element, field)
    setattr(element, field, old_text[:offset])
    if field == "text":
        element.insert(0, pb)
    else:
        parent = element.getparent()
        parent.insert(parent.index(element) + 1, pb)
    pb.tail = old_text[offset:]
    return "inline"


def restore(source, corrected, output):
    parser = etree.XMLParser(remove_blank_text=False, resolve_entities=False)
    old_tree = etree.parse(str(source), parser)
    new_tree = etree.parse(str(corrected), parser)
    old_body = old_tree.find(".//" + TEI + "body")
    new_body = new_tree.find(".//" + TEI + "body")
    if old_body is None or new_body is None:
        raise ValueError("Both documents must contain a TEI body")
    if new_body.findall(".//" + TEI + "pb"):
        raise ValueError("The corrected document already contains page breaks")

    original = TextView(old_body)
    target = TextView(new_body)
    matches, blocks = matching_positions(original.tokens, target.tokens)
    coverage = len(matches) / len(original.tokens)
    if coverage < 0.95:
        raise ValueError(f"Insufficient text alignment: {coverage:.1%}")

    placements = []
    for pb, char_offset in original.breaks:
        first_after = bisect_left(original.starts, char_offset)
        target_word, status = page_position(first_after, original.tokens, target.tokens, matches)
        placements.append((target_word, pb, status, first_after))

    # All insertions are made from the end to the start, keeping mapped text
    # offsets valid even when multiple page breaks share an XML text node.
    unchanged = "".join(new_body.itertext())
    locations = Counter()
    for word, pb, status, old_word in sorted(placements, key=lambda p: p[0], reverse=True):
        locations[add_page_break(target, word, pb, pb.getparent().tag)] += 1
    assert "".join(new_body.itertext()) == unchanged, "Text changed during reinsertion"

    restored = new_body.findall(".//" + TEI + "pb")
    assert len(restored) == len(original.breaks), "Some page breaks were lost"
    assert [(x.get("n"), x.get("{http://www.w3.org/XML/1998/namespace}id")) for x in restored] == [
        (x.get("n"), x.get("{http://www.w3.org/XML/1998/namespace}id")) for x, _ in original.breaks
    ], "Page-break order/attributes changed"

    new_tree.write(str(output), xml_declaration=True, encoding="UTF-8", pretty_print=False)
    etree.parse(str(output))  # Make sure the serialized XML is well formed.
    counts = Counter(p[2] for p in placements)
    print(f"Aligned source word tokens: {len(matches):,}/{len(original.tokens):,} ({coverage:.2%})")
    print(f"Restored page breaks: {len(restored)}; insertion sites: {dict(locations)}")
    print(f"Alignment statuses: {dict(counts)}")
    for word, pb, status, old_word in placements:
        if status != "exact":
            old_context = " ".join(original.tokens[max(old_word - 5, 0):old_word + 7])
            new_context = " ".join(target.tokens[max(word - 5, 0):word + 7])
            print(f"  Page {pb.get('n')}: {status}\n    source: {old_context}\n    target: {new_context}")
    print(f"Output: {output}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("original", type=Path, help="XML containing <pb> elements")
    ap.add_argument("corrected", type=Path, help="Corrected XML without <pb>")
    ap.add_argument("output", type=Path, help="Restored XML output")
    args = ap.parse_args()
    restore(args.original, args.corrected, args.output)


if __name__ == "__main__":
    main()
