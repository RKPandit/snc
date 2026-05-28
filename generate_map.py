#!/usr/bin/env python3
"""
Generate an interactive Folium map of student home locations from SNC PDF.

Shaheed Sayed Nazrul Islam College, Session 2003-2005, Science Department.
Extracts 240 student records from snc.pdf and plots ~237 on a map of Bangladesh.

The PDF uses SutonnyMJ (Bijoy) font encoding, so text must be converted to Unicode.
"""

import csv
import json
import re
from collections import defaultdict
from html import escape as html_escape
from pathlib import Path

import folium
import pdfplumber

# ──────────────────────────────────────────────────────────────────────────────
# SutonnyMJ / Bijoy -> Unicode Bengali conversion
# Based on https://github.com/MS-Jahan/unicode2bijoy (reverse direction)
# ──────────────────────────────────────────────────────────────────────────────

PRE_CONVERSION = {
    'yy': 'y',
    'vv': 'v',
    '\xad\xad': '\xad',
    'y&': 'y',
    '\u201e&': '\u201e',
    '\u2021u': 'u\u2021',
    'wu': 'uw',
}

BIJOY_TO_UNICODE = [
    ('\u201e\u201e', '\u09c3'),
    ('Av', '\u0986'),
    ('v', '\u09be'),
    ('w', '\u09bf'),
    ('x', '\u09c0'),
    ('y', '\u09c1'),
    ('z', '\u09c1'),
    ('\u201c', '\u09c1'),
    ('\u2013', '\u09c1'),
    ('~', '\u09c2'),
    ('\u0192', '\u09c2'),
    ('\u201a', '\u09c2'),
    ('\u201e', '\u09c3'),
    ('\u2026', '\u09c3'),
    ('\u2020', '\u09c7'),
    ('\u2021', '\u09c7'),
    ('\u02c6', '\u09c8'),
    ('\u2030', '\u09c8'),
    ('\u0160', '\u09d7'),
    ('\\|', '\u0964'),
    ('\\&', '\u09cd\u200c'),
    ('\\^', '\u09cd\u09ac'),
    ('\u2018', '\u09cd\u09a4\u09c1'),
    ('\u2019', '\u09cd\u09a5'),
    ('\u2039', '\u09cd\u0995'),
    ('\u0152', '\u09cd\u0995\u09cd\u09b0'),
    ('\u2014', '\u09cd\u09a4'),
    ('\u02dc', '\u09a6\u09cd'),
    ('\u2122', '\u09a6\u09cd'),
    ('\u0161', '\u09a8\u09cd'),
    ('\u203a', '\u09a8\u09cd'),
    ('\u0153', '\u09cd\u09a8'),
    ('\u0178', '\u09cd\u09ac'),
    ('\xa1', '\u09cd\u09ac'),
    ('\xa2', '\u09cd\u09ad'),
    ('\xa3', '\u09cd\u09ad\u09cd\u09b0'),
    ('\xa4', '\u09ae\u09cd'),
    ('\xa5', '\u09cd\u09ae'),
    ('\xa6', '\u09cd\u09ac'),
    ('\xa7', '\u09cd\u09ae'),
    ('\xa8', '\u09cd\u09af'),
    ('\xa9', '\u09b0\u09cd'),
    ('\xaa', '\u09cd\u09b0'),
    ('\xab', '\u09cd\u09b0'),
    ('\xac', '\u09cd\u09b2'),
    ('\xad', '\u09cd\u09b2'),
    ('\xae', '\u09b7\u09cd'),
    ('\xaf', '\u09b8\u09cd'),
    ('\xb0', '\u0995\u09cd\u0995'),
    ('\xb1', '\u0995\u09cd\u099f'),
    ('\xb2', '\u0995\u09cd\u09b7\u09cd\u09a3'),
    ('\xb3', '\u0995\u09cd\u09a4'),
    ('\xb4', '\u0995\u09cd\u09ae'),
    ('\xb5', '\u0995\u09cd\u09b0'),
    ('\xb6', '\u0995\u09cd\u09b7'),
    ('\xb7', '\u0995\u09cd\u09b8'),
    ('\xb8', '\u0997\u09c1'),
    ('\xb9', '\u099c\u09cd\u099e'),
    ('\xba', '\u0997\u09cd\u09a6'),
    ('\xbb', '\u0997\u09cd\u09a7'),
    ('\xbc', '\u0999\u09cd\u0995'),
    ('\xbd', '\u0999\u09cd\u0997'),
    ('\xbe', '\u099c\u09cd\u099c'),
    ('\xbf', '\u09cd\u09a4\u09cd\u09b0'),
    ('\xc0', '\u099c\u09cd\u099d'),
    ('\xc1', '\u099c\u09cd\u099e'),
    ('\xc2', '\u099e\u09cd\u099a'),
    ('\xc3', '\u099e\u09cd\u099b'),
    ('\xc4', '\u099e\u09cd\u099c'),
    ('\xc5', '\u099e\u09cd\u099d'),
    ('\xc6', '\u099f\u09cd\u099f'),
    ('\xc7', '\u09a1\u09cd\u09a1'),
    ('\xc8', '\u09a3\u09cd\u099f'),
    ('\xc9', '\u09a3\u09cd\u09a0'),
    ('\xca', '\u09a3\u09cd\u09a1'),
    ('\xcb', '\u09a4\u09cd\u09a4'),
    ('\xcc', '\u09a4\u09cd\u09a5'),
    ('\xcd', '\u09a4\u09cd\u09ae'),
    ('\xce', '\u09a4\u09cd\u09b0'),
    ('\xcf', '\u09a6\u09cd\u09a6'),
    ('\xd0', '-'),
    ('\xd1', '-'),
    ('\xd2', '\u201c'),
    ('\xd3', '\u201d'),
    ('\xd4', '\u2018'),
    ('\xd5', '\u2019'),
    ('\xd6', '\u09cd\u09b0'),
    ('\xd7', '\u09a6\u09cd\u09a7'),
    ('\xd8', '\u09a6\u09cd\u09ac'),
    ('\xd9', '\u09a6\u09cd\u09ae'),
    ('\xda', '\u09a8\u09cd\u09a0'),
    ('\xdb', '\u09a8\u09cd\u09a1'),
    ('\xdc', '\u09a8\u09cd\u09a7'),
    ('\xdd', '\u09a8\u09cd\u09b8'),
    ('\xde', '\u09aa\u09cd\u099f'),
    ('\xdf', '\u09aa\u09cd\u09a4'),
    ('\xe0', '\u09aa\u09cd\u09aa'),
    ('\xe1', '\u09aa\u09cd\u09b8'),
    ('\xe2', '\u09ac\u09cd\u099c'),
    ('\xe3', '\u09ac\u09cd\u09a6'),
    ('\xe4', '\u09ac\u09cd\u09a7'),
    ('\xe5', '\u09ad\u09cd\u09b0'),
    ('\xe6', '\u09ae\u09cd\u09a8'),
    ('\xe7', '\u09ae\u09cd\u09ab'),
    ('\xe8', '\u09cd\u09a8'),
    ('\xe9', '\u09b2\u09cd\u0995'),
    ('\xea', '\u09b2\u09cd\u0997'),
    ('\xeb', '\u09b2\u09cd\u099f'),
    ('\xec', '\u09b2\u09cd\u09a1'),
    ('\xed', '\u09b2\u09cd\u09aa'),
    ('\xee', '\u09b2\u09cd\u09ab'),
    ('\xef', '\u09b6\u09c1'),
    ('\xf0', '\u09b6\u09cd\u099a'),
    ('\xf1', '\u09b6\u09cd\u099b'),
    ('\xf2', '\u09b7\u09cd\u09a3'),
    ('\xf3', '\u09b7\u09cd\u099f'),
    ('\xf4', '\u09b7\u09cd\u09a0'),
    ('\xf5', '\u09b7\u09cd\u09ab'),
    ('\xf6', '\u09b8\u09cd\u0996'),
    ('\xf7', '\u09b8\u09cd\u099f'),
    ('\xf8', '\u09b8\u09cd\u09a8'),
    ('\xf9', '\u09b8\u09cd\u09ab'),
    ('\xfa', '\u09cd\u09aa'),
    ('\xfb', '\u09b9\u09c1'),
    ('\xfc', '\u09b9\u09c3'),
    ('\xfd', '\u09b9\u09cd\u09a8'),
    ('\xfe', '\u09b9\u09cd\u09ae'),
    ('\u2022', '\u0999\u09cd'),
    ('A', '\u0985'),
    ('B', '\u0987'),
    ('C', '\u0988'),
    ('D', '\u0989'),
    ('E', '\u098a'),
    ('F', '\u098b'),
    ('G', '\u098f'),
    ('H', '\u0990'),
    ('I', '\u0993'),
    ('J', '\u0994'),
    ('K', '\u0995'),
    ('L', '\u0996'),
    ('M', '\u0997'),
    ('N', '\u0998'),
    ('O', '\u0999'),
    ('P', '\u099a'),
    ('Q', '\u099b'),
    ('R', '\u099c'),
    ('S', '\u099d'),
    ('T', '\u099e'),
    ('U', '\u099f'),
    ('V', '\u09a0'),
    ('W', '\u09a1'),
    ('X', '\u09a2'),
    ('Y', '\u09a3'),
    ('Z', '\u09a4'),
    ('_', '\u09a5'),
    ('`', '\u09a6'),
    ('a', '\u09a7'),
    ('b', '\u09a8'),
    ('c', '\u09aa'),
    ('d', '\u09ab'),
    ('e', '\u09ac'),
    ('f', '\u09ad'),
    ('g', '\u09ae'),
    ('h', '\u09af'),
    ('i', '\u09b0'),
    ('j', '\u09b2'),
    ('k', '\u09b6'),
    ('l', '\u09b7'),
    ('m', '\u09b8'),
    ('n', '\u09b9'),
    ('o', '\u09dc'),
    ('p', '\u09dd'),
    ('q', '\u09df'),
    ('r', '\u09ce'),
    ('s', '\u0982'),
    ('t', '\u0983'),
    ('u', '\u0981'),
    ('0', '\u09e6'),
    ('1', '\u09e7'),
    ('2', '\u09e8'),
    ('3', '\u09e9'),
    ('4', '\u09ea'),
    ('5', '\u09eb'),
    ('6', '\u09ec'),
    ('7', '\u09ed'),
    ('8', '\u09ee'),
    ('9', '\u09ef'),
]

POST_CONVERSION = {
    '\u09cd\u09cd': '\u09cd',
    '\u0985\u09be': '\u0986',
    '\u09cd\u200c\u09cd\u200c': '\u09cd\u200c',
}


def _is_bangla_prekar(c):
    return c in ('\u09bf', '\u09c8', '\u09c7')


def _is_bangla_postkar(c):
    return c in ('\u09be', '\u09cb', '\u09cc', '\u09d7', '\u09c1', '\u09c2', '\u09c0', '\u09c3')


def _is_bangla_kar(c):
    return _is_bangla_prekar(c) or _is_bangla_postkar(c)


def _is_bangla_banjonborno(c):
    return c in (
        '\u0995', '\u0996', '\u0997', '\u0998', '\u0999',
        '\u099a', '\u099b', '\u099c', '\u099d', '\u099e',
        '\u099f', '\u09a0', '\u09a1', '\u09a2', '\u09a3',
        '\u09a4', '\u09a5', '\u09a6', '\u09a7', '\u09a8',
        '\u09aa', '\u09ab', '\u09ac', '\u09ad', '\u09ae',
        '\u09af', '\u09b0', '\u09b2', '\u09b6', '\u09b7',
        '\u09b8', '\u09b9', '\u09dc', '\u09dd', '\u09df',
        '\u09ce', '\u0982', '\u0983', '\u0981',
    )


def _is_bangla_halant(c):
    return c == '\u09cd'


def _rearrange_unicode(text):
    """Rearrange pre-kars and ref to correct Unicode positions."""
    s = list(text)

    # Pass 1: Move ref (র্) before the consonant cluster it belongs to
    i = 0
    while i < len(s):
        if (i < len(s) - 1 and s[i] == '\u09b0' and
                i + 1 < len(s) and _is_bangla_halant(s[i + 1]) and
                (i == 0 or not _is_bangla_halant(s[i - 1]))):
            j = 1
            while True:
                if i - j < 0:
                    break
                if (_is_bangla_banjonborno(s[i - j]) and
                        i - j - 1 >= 0 and _is_bangla_halant(s[i - j - 1])):
                    j += 2
                elif j == 1 and _is_bangla_kar(s[i - j]):
                    j += 1
                else:
                    break
            chunk = s[:i - j] + [s[i], s[i + 1]] + s[i - j:i] + s[i + 2:]
            s = chunk
            i += 1
            continue
        i += 1

    # Pass 2: Move pre-kars after the consonant cluster
    i = 0
    while i < len(s):
        if i < len(s) - 1 and _is_bangla_prekar(s[i]) and s[i + 1] != ' ':
            j = 1
            while (i + j < len(s) - 1 and _is_bangla_banjonborno(s[i + j])):
                if i + j + 1 < len(s) and _is_bangla_halant(s[i + j + 1]):
                    j += 2
                else:
                    break
            l = 0
            if s[i] == '\u09c7' and i + j + 1 < len(s) and s[i + j + 1] == '\u09be':
                combined = '\u09cb'
                l = 1
            elif s[i] == '\u09c7' and i + j + 1 < len(s) and s[i + j + 1] == '\u09d7':
                combined = '\u09cc'
                l = 1
            else:
                combined = s[i]
            chunk = s[:i] + s[i + 1:i + j + 1] + [combined] + s[i + j + l + 1:]
            s = chunk
            i += j + 1
            continue
        i += 1

    # Pass 3: Chandrabindu (ঁ) should come after vowel sign, not before
    i = 0
    while i < len(s) - 1:
        if s[i] == '\u0981' and _is_bangla_postkar(s[i + 1]):
            s[i], s[i + 1] = s[i + 1], s[i]
            i += 2
            continue
        i += 1

    return ''.join(s)


def bijoy_to_unicode(text):
    """Convert SutonnyMJ/Bijoy encoded text to proper Unicode Bengali."""
    if not text:
        return text
    for old, new in PRE_CONVERSION.items():
        text = text.replace(old, new)
    for bijoy_char, unicode_char in BIJOY_TO_UNICODE:
        text = text.replace(bijoy_char, unicode_char)
    for old, new in POST_CONVERSION.items():
        text = text.replace(old, new)
    text = _rearrange_unicode(text)
    return text


# ──────────────────────────────────────────────────────────────────────────────
# Raw SutonnyMJ address -> (upazila, district) direct mapping
# This is more reliable than converting and then parsing, since there are
# only ~72 unique addresses in the PDF.
# ──────────────────────────────────────────────────────────────────────────────

RAW_ADDRESS_MAP = {
    # Mymensingh District (ময়মনসিংহ)
    'MdiMuvI, gqgbwmsn':           ("গফরগাঁও", "ময়মনসিংহ"),
    'Mdi MuvI, gqgbwmsn':          ("গফরগাঁও", "ময়মনসিংহ"),
    'Ck\xa6iM\xc4, gqgbwmsn':     ("ঈশ্বরগঞ্জ", "ময়মনসিংহ"),
    'm`i, gqgbwmsn':               ("সদর", "ময়মনসিংহ"),
    'ZvivKv\u203a`v, gqgbwmsn':    ("তারাকান্দা", "ময়মনসিংহ"),
    'ZvivKv\u203a`v gqgbwmsn':     ("তারাকান্দা", "ময়মনসিংহ"),
    'w\xcekvj, gqgbwmsn':          ("ত্রিশাল", "ময়মনসিংহ"),
    'w\xcekvj, gqgbwmsn|':         ("ত্রিশাল", "ময়মনসিংহ"),
    'w\xcekvj,gqgbwmsn':           ("ত্রিশাল", "ময়মনসিংহ"),
    'gy\xb3vMvQv, gqgbwmsn':       ("মুক্তাগাছা", "ময়মনসিংহ"),
    'nvjyqvNvU, gqgbwmsn':         ("হালুয়াঘাট", "ময়মনসিংহ"),
    '\u2021M\u0160ixcyi, gqgbwmsn|':  ("গৌরীপুর", "ময়মনসিংহ"),
    '\u2021M\u0160ixcyi, gqgbwmsn': ("গৌরীপুর", "ময়মনসিংহ"),
    '\u2020M\u0160ixcyi, gqgbwmsn': ("গৌরীপুর", "ময়মনসিংহ"),
    'dzjcyi, gqgbwmsn':            ("ফুলপুর", "ময়মনসিংহ"),
    'dzjcyi, gqgbwmsn|':           ("ফুলপুর", "ময়মনসিংহ"),
    'dzjdzi, gqgbwmsn':            ("ফুলপুর", "ময়মনসিংহ"),
    'bv\u203a`vBj, gqgbwmsn':      ("নান্দাইল", "ময়মনসিংহ"),
    'fvjyKv, gqgbwmsn':            ("ভালুকা", "ময়মনসিংহ"),
    'dzjevoxqv, gqgbwmsn':         ("ফুলবাড়ীয়া", "ময়মনসিংহ"),
    'dyjevoxqv, gqgbwmsn':         ("ফুলবাড়ীয়া", "ময়মনসিংহ"),
    '\u2020Kv\u2021Zvqvjx, gqgbwmsn':  ("সদর", "ময়মনসিংহ"),
    'gqgbwmsn':                    ("সদর", "ময়মনসিংহ"),

    # Netrokona District (নেত্রকোনা) - note: \xce = Î = ত্র in SutonnyMJ
    'c~e\xa9ajv, \u2020b\xce\u2021Kvbv':  ("পূর্বধলা", "নেত্রকোনা"),
    'AvUcvov, \u2020b\xce\u2021Kvbv':     ("আটপাড়া", "নেত্রকোনা"),
    'LvjyqvRyox, \u2020b\xce\u2021Kvbv':  ("খালিয়াজুড়ী", "নেত্রকোনা"),
    'LvwjqvRyox, \u2020b\xce\u2021Kvbv':  ("খালিয়াজুড়ী", "নেত্রকোনা"),
    '\u2021K\u203a`yqv, \u2020b\xce\u2021Kvbv':  ("কেন্দুয়া", "নেত্রকোনা"),
    '`~M\xa9vcyi, \u2020b\xce\u2021Kvbv': ("দুর্গাপুর", "নেত্রকোনা"),
    '\u2020gvnbM\xc4 \u2020b\xce\u2021Kvbv':  ("মোহনগঞ্জ", "নেত্রকোনা"),
    'DwKjcvov, \u2020b\xce\u2021Kvbv':    ("সদর", "নেত্রকোনা"),
    'wbDUb \u2020b\xce\u2021Kvbv':        ("সদর", "নেত্রকোনা"),
    '\u2021b\xce\u2021Kvbv':               ("সদর", "নেত্রকোনা"),
    '\u2020b\xce\u2021Kvbv':               ("সদর", "নেত্রকোনা"),
    '\u2020b\xce\u2021Kvbv m`i,\n\u2020b\xce\u2021Kvbv':  ("সদর", "নেত্রকোনা"),
    'evinv\xc6v, gqgbwmsn':        ("বারহাট্টা", "নেত্রকোনা"),
    'g`b, gqgbwmsn':               ("মদন", "নেত্রকোনা"),
    '\u2020K\u203a`yqv, gqgbwmsn':  ("কেন্দুয়া", "নেত্রকোনা"),

    # Jamalpur District (জামালপুর)
    'gv`viM\xc4, Rvgvjcyi':       ("মাদারগঞ্জ", "জামালপুর"),
    'Rvgvjcyi m`i,\nRvgvjcyi':    ("সদর", "জামালপুর"),
    'Rvgvjcyi, m`i,\nRvgvjcyi':   ("সদর", "জামালপুর"),
    'Rvgvjcyi':                    ("সদর", "জামালপুর"),
    'Bmjvgcyi, Rvgvjcyi':         ("ইসলামপুর", "জামালপুর"),
    'eKwkM\xc4, Rvgvjcyi':        ("বকশিগঞ্জ", "জামালপুর"),

    # Sherpur District (শেরপুর)
    '\u2020kicyi m`i, \u2020kicyi':  ("সদর", "শেরপুর"),
    '\u2020kicyi m`i, \u2021kicyi':  ("সদর", "শেরপুর"),
    '\u2021kicyi':                   ("সদর", "শেরপুর"),
    'bKjv, \u2020kicyi':             ("নকলা", "শেরপুর"),
    'bKkjv, \u2020kicyi':            ("নকলা", "শেরপুর"),

    # Kishoreganj District (কিশোরগঞ্জ)
    'ZvovBj, wK\u2021kviM\xc4':     ("তাড়াইল", "কিশোরগঞ্জ"),
    'KwUqv`x, wK\u2021kviM\xc4':    ("কটিয়াদী", "কিশোরগঞ্জ"),
    'Kzwjqvi Pi, wK\u2021kviM\xc4': ("কুলিয়ার চর", "কিশোরগঞ্জ"),
    'wK\u2021kviM\xc4 m`i,\nwK\u2021kviM\xc4':  ("সদর", "কিশোরগঞ্জ"),
    'bKjv, wK\u2021kviM\xc4':       ("নকলা", "কিশোরগঞ্জ"),

    # Tangail District (টাঙ্গাইল)
    'mwLicyi, Uv\xbdvBj':           ("সখিপুর", "টাঙ্গাইল"),
    'wgR\xa9vcyi, Uv\xbdvBj':       ("মির্জাপুর", "টাঙ্গাইল"),
    '\u2020Mvcvjcyi, Uv\xbdvBj':    ("গোপালপুর", "টাঙ্গাইল"),
    'NvUvBj, Uv\xbdvBj':            ("ঘাটাইল", "টাঙ্গাইল"),
    '............., Uv\xbdvBj':      ("সদর", "টাঙ্গাইল"),
    'Uv\xbdvBj':                     ("সদর", "টাঙ্গাইল"),

    # Gopalganj District (গোপালগঞ্জ)
    '\u2020MvcvjM\xc4, \u2020MvcvjM\xc4':  ("সদর", "গোপালগঞ্জ"),
    '\u2021MvcvjM\xc4 m`i,\n\u2020MvcvjM\xc4':  ("সদর", "গোপালগঞ্জ"),

    # Dhaka (ঢাকা)
    'beveM\xc4, XvKv':              ("নবাবগঞ্জ", "ঢাকা"),

    # Narsingdi (নরসিংদী)
    '\u2020ejve,biwms`x':            ("বেলাব", "নরসিংদী"),

    # Manikganj (মানিকগঞ্জ)
    'gvwbKM\xc4 m`i, gvwbKM\xc4':   ("সদর", "মানিকগঞ্জ"),

    # Brahmanbaria (ব্রাহ্মণবাড়ীয়া)
    'Kmev, e\xaav\xfebevoxqv':      ("কসবা", "ব্রাহ্মণবাড়ীয়া"),

    # Thakurgaon (ঠাকুরগাঁও)
    'VvKziMuvI, VvKziMuvI':          ("সদর", "ঠাকুরগাঁও"),

    # Barisal (বরিশাল)
    'ewikvj m`i, ewikvj':            ("সদর", "বরিশাল"),

    # Noakhali (নোয়াখালী)
    '\u2020mvbvBgyox, \u2020bvqvLvjx':  ("সোনাইমুড়ী", "নোয়াখালী"),

    # Chandpur (চাঁদপুর)
    'KPzqv Puv`cyi':                ("কচুয়া", "চাঁদপুর"),

    # Jhenaidah (বিনাইদহ)
    'wSbvB`n':                       ("সদর", "বিনাইদহ"),

    # Empty / missing
    '': None,
}

# Roll-specific overrides (corrections to PDF address data)
ROLL_OVERRIDES = {
    163: ("আটপাড়া", "নেত্রকোনা"),
}

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

BD_BOUNDARY_PATH = Path(__file__).parent / "bd_boundary.json"
PDF_PATH = Path(__file__).parent / "snc.pdf"
OUTPUT_PATH = Path(__file__).parent / "index.html"
CSV_PATH = Path(__file__).parent / "students.csv"

LOCATION_COORDS = {
    # Mymensingh District (corrected from Google Maps / geographic databases)
    ("সদর", "ময়মনসিংহ"): (24.7500, 90.4167),
    ("গফরগাঁও", "ময়মনসিংহ"): (24.3900, 90.5600),
    ("ত্রিশাল", "ময়মনসিংহ"): (24.5600, 90.4200),
    ("ঈশ্বরগঞ্জ", "ময়মনসিংহ"): (24.6500, 90.5900),
    ("তারাকান্দা", "ময়মনসিংহ"): (24.9500, 90.4667),
    ("মুক্তাগাছা", "ময়মনসিংহ"): (24.7668, 90.2596),
    ("ফুলপুর", "ময়মনসিংহ"): (24.9525, 90.3588),
    ("গৌরীপুর", "ময়মনসিংহ"): (24.7600, 90.6200),
    ("নান্দাইল", "ময়মনসিংহ"): (24.5692, 90.6925),
    ("ভালুকা", "ময়মনসিংহ"): (24.3750, 90.3783),
    ("ফুলবাড়ীয়া", "ময়মনসিংহ"): (24.6340, 90.2732),
    ("হালুয়াঘাট", "ময়মনসিংহ"): (25.1223, 90.3396),
    ("ধোবাউড়া", "ময়মনসিংহ"): (25.0917, 90.5333),

    # Netrokona District
    ("সদর", "নেত্রকোনা"): (24.8750, 90.7333),
    ("পূর্বধলা", "নেত্রকোনা"): (24.9333, 90.6028),
    ("আটপাড়া", "নেত্রকোনা"): (24.8100, 90.8600),
    ("খালিয়াজুড়ী", "নেত্রকোনা"): (24.6900, 91.1000),
    ("কেন্দুয়া", "নেত্রকোনা"): (24.6900, 90.8700),
    ("দুর্গাপুর", "নেত্রকোনা"): (25.1200, 90.6900),
    ("মোহনগঞ্জ", "নেত্রকোনা"): (24.8667, 90.9667),
    ("মদন", "নেত্রকোনা"): (24.7167, 90.9667),
    ("বারহাট্টা", "নেত্রকোনা"): (24.9000, 90.8750),

    # Jamalpur District
    ("সদর", "জামালপুর"): (24.9167, 89.9583),
    ("মাদারগঞ্জ", "জামালপুর"): (24.8900, 89.7500),
    ("ইসলামপুর", "জামালপুর"): (25.0833, 89.7917),
    ("বকশিগঞ্জ", "জামালপুর"): (25.1844, 89.8681),

    # Sherpur District
    ("সদর", "শেরপুর"): (25.0194, 90.0137),
    ("নকলা", "শেরপুর"): (24.9833, 90.1833),

    # Kishoreganj District
    ("সদর", "কিশোরগঞ্জ"): (24.4333, 90.7833),
    ("তাড়াইল", "কিশোরগঞ্জ"): (24.5375, 90.8750),
    ("কটিয়াদী", "কিশোরগঞ্জ"): (24.2500, 90.7917),
    ("কুলিয়ার চর", "কিশোরগঞ্জ"): (24.1542, 90.9000),
    ("নকলা", "কিশোরগঞ্জ"): (24.4300, 90.7800),

    # Tangail District
    ("সদর", "টাঙ্গাইল"): (24.2500, 89.9167),
    ("সখিপুর", "টাঙ্গাইল"): (24.3206, 90.1809),
    ("মির্জাপুর", "টাঙ্গাইল"): (24.1083, 90.0917),
    ("গোপালপুর", "টাঙ্গাইল"): (24.5800, 89.8750),
    ("ঘাটাইল", "টাঙ্গাইল"): (24.4700, 89.9700),

    # Other districts
    ("সদর", "গোপালগঞ্জ"): (23.0167, 89.8333),
    ("নবাবগঞ্জ", "ঢাকা"): (23.6667, 90.1667),
    ("বেলাব", "নরসিংদী"): (24.0917, 90.8500),
    ("সদর", "মানিকগঞ্জ"): (23.8347, 90.0187),
    ("কসবা", "ব্রাহ্মণবাড়ীয়া"): (23.7700, 91.1200),
    ("সদর", "ঠাকুরগাঁও"): (26.0208, 88.4667),
    ("সদর", "বরিশাল"): (22.7385, 90.4314),
    ("সোনাইমুড়ী", "নোয়াখালী"): (23.0509, 91.1113),
    ("কচুয়া", "চাঁদপুর"): (23.3500, 90.8917),
    ("সদর", "বিনাইদহ"): (23.5417, 89.1833),
}

DISTRICT_COLORS = {
    "ময়মনসিংহ": "#6366f1",
    "নেত্রকোনা": "#10b981",
    "জামালপুর": "#f59e0b",
    "শেরপুর": "#8b5cf6",
    "কিশোরগঞ্জ": "#ef4444",
    "টাঙ্গাইল": "#ec4899",
    "গোপালগঞ্জ": "#14b8a6",
    "ঢাকা": "#22c55e",
    "নরসিংদী": "#f97316",
    "মানিকগঞ্জ": "#06b6d4",
    "ব্রাহ্মণবাড়ীয়া": "#a78bfa",
    "ঠাকুরগাঁও": "#84cc16",
    "বরিশাল": "#eab308",
    "নোয়াখালী": "#64748b",
    "চাঁদপুর": "#fb923c",
    "বিনাইদহ": "#94a3b8",
}


# ──────────────────────────────────────────────────────────────────────────────
# Extraction & Map Building
# ──────────────────────────────────────────────────────────────────────────────

def extract_records(pdf_path):
    """Extract all student records from the PDF."""
    records = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue
            for row in table:
                if not row or len(row) < 4:
                    continue
                roll_cell = (row[0] or "").strip()
                if not roll_cell or not roll_cell.isdigit():
                    continue

                roll = int(roll_cell)
                name_raw = (row[1] or "").strip()
                address_raw = (row[3] or "").strip()

                name = bijoy_to_unicode(name_raw)
                location = ROLL_OVERRIDES.get(roll, RAW_ADDRESS_MAP.get(address_raw))

                # If not found in lookup, try to handle unknown addresses
                if location is None and address_raw and address_raw not in RAW_ADDRESS_MAP:
                    print(f"  UNMAPPED address for roll {roll}: {address_raw!r}")

                records.append({
                    "roll": roll,
                    "name": name,
                    "location": location,
                })

    records.sort(key=lambda r: r["roll"])
    return records


def _load_bangladesh_boundary():
    """Load detailed Bangladesh boundary (1513 points, 17 polygons)."""
    with open(BD_BOUNDARY_PATH) as f:
        return json.load(f)


def build_map_for_embed(records):
    """Build a Folium map suitable for iframe embedding."""
    location_students = defaultdict(list)
    missing = 0
    for rec in records:
        loc = rec["location"]
        if loc is None:
            missing += 1
            continue
        location_students[loc].append(rec)

    total = len(records)
    plotted = total - missing

    m = folium.Map(
        location=[23.7, 90.35],
        zoom_start=7,
        tiles="OpenStreetMap",
        control_scale=True,
        prefer_canvas=True,
    )

    # Mask everything outside Bangladesh with a white overlay
    # Uses detailed 1513-point boundary from geoBoundaries ADM0 (CC BY 4.0)
    bd_polys = _load_bangladesh_boundary()
    world_ring = [[-180, -90], [180, -90], [180, 90], [-180, 90], [-180, -90]]
    # Each Bangladesh polygon becomes a hole in the world polygon
    holes = [list(reversed(poly)) for poly in bd_polys]
    mask_geojson = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [world_ring] + holes,
        },
    }
    folium.GeoJson(
        mask_geojson,
        style_function=lambda x: {
            "fillColor": "#000000",
            "fillOpacity": 0.3,
            "color": "#2ca02c",
            "weight": 2,
        },
    ).add_to(m)

    unmapped = []
    for loc, students in location_students.items():
        upazila, district = loc
        coords = LOCATION_COORDS.get(loc)
        if coords is None:
            unmapped.append((loc, len(students)))
            continue

        count = len(students)
        color = DISTRICT_COLORS.get(district, "#333333")
        radius = max(8, min(count * 1.5, 35))

        student_rows = "".join(
            f"<tr><td style='padding:2px 6px;border-bottom:1px solid #eee;'>{s['roll']}</td>"
            f"<td style='padding:2px 6px;border-bottom:1px solid #eee;'>{s['name']}</td></tr>"
            for s in sorted(students, key=lambda s: s["roll"])
        )

        popup_html = f"""
        <div style="font-family:'Noto Sans Bengali',sans-serif;min-width:200px;">
            <h4 style="margin:0 0 4px 0;color:{color};">{upazila}, {district}</h4>
            <p style="margin:0 0 6px 0;font-size:13px;">মোট: <b>{count}</b> জন</p>
            <div style="max-height:300px;overflow-y:auto;">
                <table style="width:100%;border-collapse:collapse;font-size:13px;">
                    <tr style="background:#f0f0f0;">
                        <th style="padding:4px 6px;text-align:left;">রোল</th>
                        <th style="padding:4px 6px;text-align:left;">নাম</th>
                    </tr>
                    {student_rows}
                </table>
            </div>
        </div>
        """

        tooltip_text = f"{upazila}, {district} ({count} জন)"

        folium.CircleMarker(
            location=coords,
            radius=radius,
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.6,
            weight=2,
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=tooltip_text,
        ).add_to(m)

    if unmapped:
        print(f"WARNING: {len(unmapped)} location(s) not in coordinate dict:")
        for loc, cnt in unmapped:
            print(f"  {loc} ({cnt} students)")

    # PostMessage listener for district filtering from outer page
    filter_script = """
    <script>
    setTimeout(function(){
      var mapObj;
      for(var k in window){
        try{if(window[k] instanceof L.Map){mapObj=window[k];break;}}catch(e){}
      }
      if(!mapObj)return;
      var byDistrict={};
      mapObj.eachLayer(function(layer){
        if(layer instanceof L.CircleMarker && !(layer instanceof L.Circle)){
          var tip=layer.getTooltip();
          if(tip){
            var text=typeof tip.getContent==='function'?tip.getContent():'';
            var m=text.match(/,\\s*(.+?)\\s*\\(/);
            if(m){var d=m[1];if(!byDistrict[d])byDistrict[d]=[];byDistrict[d].push(layer);}
          }
        }
      });
      window.addEventListener('message',function(e){
        var d=e.data&&e.data.district;
        var bounds=L.latLngBounds();
        var has=false;
        for(var dist in byDistrict){
          byDistrict[dist].forEach(function(mk){
            if(!d||d===dist){
              if(!mapObj.hasLayer(mk))mapObj.addLayer(mk);
              bounds.extend(mk.getLatLng());has=true;
            }else{
              if(mapObj.hasLayer(mk))mapObj.removeLayer(mk);
            }
          });
        }
        if(d&&has)mapObj.fitBounds(bounds,{padding:[40,40],maxZoom:12});
        else if(!d)mapObj.setView([23.7,90.35],7);
      });
    },100);
    </script>
    """
    m.get_root().html.add_child(folium.Element(filter_script))

    # Fonts for popups (viewport already set by folium)
    head_html = """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Bengali:wght@400;700&display=swap" rel="stylesheet">
    """
    m.get_root().header.add_child(folium.Element(head_html))

    return m


def compute_statistics(records):
    """Compute district/upazila counts, summary stats, and student lists."""
    district_counts = defaultdict(int)
    upazila_counts = defaultdict(int)
    district_student_lists = defaultdict(list)
    upazila_student_lists = defaultdict(list)
    plotted = 0

    for rec in records:
        loc = rec["location"]
        if loc is None:
            continue
        plotted += 1
        upazila, district = loc
        district_counts[district] += 1
        upazila_counts[loc] += 1
        entry = {"roll": rec["roll"], "name": rec["name"]}
        district_student_lists[district].append(entry)
        upazila_student_lists[loc].append(entry)

    # Sort districts descending by count
    district_sorted = sorted(district_counts.items(), key=lambda x: x[1], reverse=True)
    district_labels = [d for d, _ in district_sorted]
    district_values = [c for _, c in district_sorted]
    district_colors = [DISTRICT_COLORS.get(d, "#94a3b8") for d in district_labels]

    # All upazilas sorted descending
    upazila_sorted = sorted(upazila_counts.items(), key=lambda x: x[1], reverse=True)
    upazila_labels = [f"{up}, {dist}" for (up, dist), _ in upazila_sorted]
    upazila_values = [c for _, c in upazila_sorted]
    upazila_colors = [DISTRICT_COLORS.get(dist, "#94a3b8") for (_, dist), _ in upazila_sorted]

    # Student lookup dicts for chart click interaction
    district_students = {
        dist: sorted(district_student_lists[dist], key=lambda s: s["roll"])
        for dist in district_labels
    }
    upazila_students = {
        f"{up}, {dist}": sorted(upazila_student_lists[(up, dist)], key=lambda s: s["roll"])
        for (up, dist), _ in upazila_sorted
    }

    return {
        "total": len(records),
        "plotted": plotted,
        "num_districts": len(district_counts),
        "num_upazilas": len(upazila_counts),
        "district_labels": district_labels,
        "district_values": district_values,
        "district_colors": district_colors,
        "upazila_labels": upazila_labels,
        "upazila_values": upazila_values,
        "upazila_colors": upazila_colors,
        "district_students": district_students,
        "upazila_students": upazila_students,
    }


def build_full_page(map_html_escaped, stats):
    """Build modern HTML page with hero, embedded map, interactive charts, and footer."""
    import json as _json

    district_labels_js = _json.dumps(stats["district_labels"], ensure_ascii=False)
    district_values_js = _json.dumps(stats["district_values"])
    district_colors_js = _json.dumps(stats["district_colors"])
    upazila_labels_js = _json.dumps(stats["upazila_labels"], ensure_ascii=False)
    upazila_values_js = _json.dumps(stats["upazila_values"])
    upazila_colors_js = _json.dumps(stats["upazila_colors"])
    district_students_js = _json.dumps(stats["district_students"], ensure_ascii=False)
    upazila_students_js = _json.dumps(stats["upazila_students"], ensure_ascii=False)
    num_upazilas = len(stats["upazila_labels"])

    # Build district filter pills HTML
    pills = [
        '<button class="filter-pill active" data-district="">'
        '<span class="pill-dot" style="background:linear-gradient(135deg,#6366f1,#10b981)"></span>সকল</button>'
    ]
    for label, color in zip(stats["district_labels"], stats["district_colors"]):
        pills.append(
            f'<button class="filter-pill" data-district="{label}">'
            f'<span class="pill-dot" style="background:{color}"></span>{label}</button>'
        )
    filter_pills_html = "\n    ".join(pills)

    return f'''<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>সৈনক | বিজ্ঞান ২০০৩-২০০৫</title>
<meta property="og:title" content="SSNIC Science 2003-2005 — Student Map &amp; Stats"/>
<meta property="og:description" content="শহীদ সৈয়দ নজরুল ইসলাম কলেজ, ময়মনসিংহ — ২০০৩-২০০৫ সেশনের বিজ্ঞান বিভাগের ছাত্রদের ইন্টারেক্টিভ ম্যাপ ও পরিসংখ্যান"/>
<meta property="og:type" content="website"/>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Bengali:wght@300;400;500;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html{{scroll-behavior:smooth}}
body{{font-family:'Noto Sans Bengali','Inter',system-ui,sans-serif;background:#f8fafc;color:#0f172a;line-height:1.7;overflow-x:hidden}}

/* ── Hero ── */
.hero{{position:relative;min-height:55vh;display:flex;align-items:center;justify-content:center;background:#0f172a;overflow:hidden;padding:clamp(2.5rem,6vw,4rem) 1.5rem}}
.hero::before{{content:'';position:absolute;inset:-50%;background:radial-gradient(circle at 20% 50%,rgba(99,102,241,.3) 0%,transparent 50%),radial-gradient(circle at 80% 20%,rgba(16,185,129,.25) 0%,transparent 50%),radial-gradient(circle at 60% 80%,rgba(139,92,246,.2) 0%,transparent 50%),radial-gradient(circle at 40% 30%,rgba(236,72,153,.15) 0%,transparent 40%);animation:meshMove 12s ease-in-out infinite alternate}}
@keyframes meshMove{{0%{{transform:translate(0,0) scale(1)}}33%{{transform:translate(-5%,3%) scale(1.05)}}66%{{transform:translate(3%,-2%) scale(.98)}}100%{{transform:translate(-2%,5%) scale(1.03)}}}}
.hero-content{{position:relative;z-index:1;text-align:center;max-width:820px}}
.badge{{display:inline-block;background:rgba(99,102,241,.15);border:1px solid rgba(99,102,241,.25);color:#a5b4fc;padding:.35rem 1.2rem;border-radius:100px;font-size:.82rem;font-weight:500;margin-bottom:1.4rem;letter-spacing:.02em}}
.hero h1{{font-size:clamp(1.7rem,5vw,2.8rem);font-weight:700;color:#fff;margin-bottom:.25rem;line-height:1.3}}
.hero-en{{font-size:clamp(.8rem,1.8vw,1rem);color:#94a3b8;font-weight:400;margin-bottom:.7rem;font-family:'Inter','Noto Sans Bengali',sans-serif}}
.session-badge{{display:inline-flex;align-items:center;gap:.5rem;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.1);color:#cbd5e1;padding:.4rem 1.1rem;border-radius:10px;font-size:.88rem;margin-bottom:2rem}}
.stat-cards{{display:flex;justify-content:center;gap:clamp(.7rem,2vw,1.2rem);flex-wrap:wrap}}
.stat-card{{background:rgba(255,255,255,.06);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,.1);border-radius:16px;padding:clamp(.9rem,2vw,1.3rem) clamp(1.3rem,3vw,2rem);min-width:130px;transition:transform .2s,background .2s}}
.stat-card:hover{{transform:translateY(-3px);background:rgba(255,255,255,.11)}}
.stat-card .number{{font-size:clamp(1.8rem,4.5vw,2.8rem);font-weight:700;color:#fff;line-height:1.1}}
.stat-card .label{{font-size:.82rem;color:#94a3b8;margin-top:.25rem;font-weight:400}}

/* ── Sections ── */
.section{{max-width:1100px;margin:0 auto;padding:clamp(2rem,5vw,3.5rem) 1.5rem}}
.section-header{{text-align:center;margin-bottom:2rem}}
.section-header h2{{font-size:clamp(1.2rem,3vw,1.7rem);font-weight:600;color:#0f172a;margin-bottom:.4rem}}
.section-header p{{color:#64748b;font-size:.92rem}}
.accent-line{{width:48px;height:3px;background:linear-gradient(90deg,#6366f1,#10b981);border-radius:2px;margin:.8rem auto 0}}

/* ── Map ── */
.district-filter{{display:flex;flex-wrap:wrap;justify-content:center;gap:.4rem;margin-bottom:1.2rem}}
.filter-pill{{display:inline-flex;align-items:center;gap:.4rem;padding:.3rem .8rem;border:1px solid #e2e8f0;border-radius:100px;background:#fff;cursor:pointer;font-family:inherit;font-size:.8rem;color:#475569;transition:all .2s;white-space:nowrap}}
.filter-pill:hover{{border-color:#94a3b8;background:#f8fafc}}
.filter-pill.active{{background:#0f172a;color:#fff;border-color:#0f172a}}
.filter-pill.active .pill-dot{{box-shadow:0 0 0 2px rgba(255,255,255,.4)}}
.pill-dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
.map-card{{border-radius:16px;overflow:hidden;box-shadow:0 4px 32px rgba(99,102,241,.1),0 1px 4px rgba(0,0,0,.04);border:1px solid #e2e8f0}}
.map-card iframe{{width:100%;height:65vh;border:none;display:block}}

/* ── Charts ── */
.toggle-wrap{{display:flex;justify-content:center;margin-bottom:1.5rem}}
.toggle-group{{display:inline-flex;background:#e2e8f0;border-radius:12px;padding:4px;gap:2px}}
.toggle-btn{{padding:.55rem 1.6rem;border:none;background:transparent;border-radius:10px;cursor:pointer;font-family:inherit;font-size:.92rem;font-weight:500;color:#64748b;transition:all .25s ease}}
.toggle-btn.active{{background:#fff;color:#0f172a;box-shadow:0 2px 8px rgba(0,0,0,.08)}}
.toggle-btn:hover:not(.active){{color:#334155}}
.chart-card{{background:#fff;border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,.06);border:1px solid #e2e8f0;padding:clamp(1rem,2.5vw,1.5rem)}}
.chart-meta{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:.8rem;flex-wrap:wrap;gap:.3rem}}
.chart-title{{font-size:1rem;font-weight:600;color:#334155}}
.chart-hint{{font-size:.78rem;color:#94a3b8}}
.chart-wrap{{position:relative;transition:height .35s ease}}

/* ── Modal ── */
.modal-overlay{{position:fixed;inset:0;background:rgba(15,23,42,.5);backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px);z-index:9999;display:flex;align-items:center;justify-content:center;padding:1rem;opacity:0;pointer-events:none;transition:opacity .25s ease}}
.modal-overlay.show{{opacity:1;pointer-events:auto}}
.modal-content{{background:#fff;border-radius:20px;padding:1.8rem;max-width:480px;width:100%;max-height:80vh;overflow:hidden;display:flex;flex-direction:column;box-shadow:0 24px 64px rgba(0,0,0,.2);transform:translateY(12px) scale(.97);transition:transform .25s ease}}
.modal-overlay.show .modal-content{{transform:translateY(0) scale(1)}}
.modal-header{{display:flex;align-items:flex-start;justify-content:space-between;gap:1rem;margin-bottom:.8rem}}
.modal-header h3{{font-size:1.1rem;font-weight:600;color:#0f172a;line-height:1.4}}
.modal-close{{background:#f1f5f9;border:none;width:34px;height:34px;border-radius:10px;cursor:pointer;font-size:1.2rem;color:#64748b;display:flex;align-items:center;justify-content:center;transition:background .15s;flex-shrink:0}}
.modal-close:hover{{background:#e2e8f0}}
.modal-count{{font-size:.85rem;color:#6366f1;font-weight:500;margin-bottom:.8rem}}
.modal-list{{overflow-y:auto;flex:1}}
.student-row{{display:flex;align-items:center;padding:.55rem 0;border-bottom:1px solid #f1f5f9;gap:.8rem}}
.student-row:last-child{{border-bottom:none}}
.student-roll{{background:#f1f5f9;color:#475569;font-size:.78rem;font-weight:600;padding:.15rem .55rem;border-radius:6px;min-width:40px;text-align:center;font-family:'Inter',monospace}}
.student-name{{font-size:.92rem;color:#1e293b}}

/* ── Footer ── */
footer{{background:#0f172a;color:#94a3b8;padding:2rem 1.5rem;text-align:center;font-size:.82rem;line-height:1.8}}
footer a{{color:#a5b4fc;text-decoration:none}}
footer a:hover{{text-decoration:underline}}
.footer-sep{{display:inline-block;width:40px;height:1px;background:#334155;vertical-align:middle;margin:0 .8rem}}

/* ── Responsive ── */
@media(max-width:768px){{
  .hero{{min-height:auto;padding:2rem 1rem 2.5rem}}
  .map-card iframe{{height:50vh}}
  .section{{padding:2rem 1rem}}
  .stat-card{{padding:.8rem 1.1rem;min-width:95px}}
  .toggle-btn{{padding:.45rem 1.1rem;font-size:.85rem}}
  .chart-card{{padding:1rem}}
  .modal-content{{padding:1.3rem;border-radius:16px}}
}}

/* ── Fade-in animation ── */
.fade-in{{opacity:0;transform:translateY(20px);transition:opacity .6s ease,transform .6s ease}}
.fade-in.visible{{opacity:1;transform:translateY(0)}}
</style>
</head>
<body>

<!-- ═══ Hero ═══ -->
<section class="hero">
  <div class="hero-content">
    <div class="badge">প্রতিষ্ঠা ১৯৯৯ &bull; ময়মনসিংহ &bull; EIIN 111910</div>
    <h1>শহীদ সৈয়দ নজরুল ইসলাম কলেজ</h1>
    <p class="hero-en">Shaheed Syed Nazrul Islam College, Mymensingh</p>
    <div class="session-badge">
      <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M12 14l9-5-9-5-9 5 9 5z"/><path d="M12 14l6.16-3.42A12.08 12.08 0 0121 17.5C21 20 16.97 22 12 22s-9-2-9-4.5a12.08 12.08 0 012.84-6.92L12 14z"/></svg>
      সেশন ২০০৩–২০০৫ &middot; বিজ্ঞান বিভাগ
    </div>
    <div class="stat-cards">
      <div class="stat-card">
        <div class="number" data-count="{stats["total"]}">0</div>
        <div class="label">মোট ছাত্র</div>
      </div>
      <div class="stat-card">
        <div class="number" data-count="{stats["plotted"]}">0</div>
        <div class="label">ম্যাপে প্রদর্শিত</div>
      </div>
      <div class="stat-card">
        <div class="number" data-count="{stats["num_districts"]}">0</div>
        <div class="label">জেলা</div>
      </div>
      <div class="stat-card">
        <div class="number" data-count="{stats["num_upazilas"]}">0</div>
        <div class="label">উপজেলা</div>
      </div>
    </div>
  </div>
</section>

<!-- ═══ Map ═══ -->
<section class="section fade-in">
  <div class="section-header">
    <h2>বন্ধুদের অবস্থান</h2>
    <p>মার্কারে ক্লিক করে বিস্তারিত দেখুন</p>
    <div class="accent-line"></div>
  </div>
  <div class="district-filter" id="districtFilter">
    {filter_pills_html}
  </div>
  <div class="map-card">
    <iframe srcdoc="{map_html_escaped}" title="Student Location Map" loading="lazy" id="mapIframe"></iframe>
  </div>
</section>

<!-- ═══ Charts ═══ -->
<section class="section fade-in">
  <div class="section-header">
    <h2>ছাত্র পরিসংখ্যান</h2>
    <p>জেলা ও উপজেলা অনুযায়ী বিতরণ</p>
    <div class="accent-line"></div>
  </div>
  <div class="toggle-wrap">
    <div class="toggle-group">
      <button class="toggle-btn active" data-view="district">জেলা</button>
      <button class="toggle-btn" data-view="upazila">উপজেলা</button>
    </div>
  </div>
  <div class="chart-card">
    <div class="chart-meta">
      <span class="chart-title" id="chartTitle">জেলা অনুযায়ী ছাত্র সংখ্যা</span>
      <span class="chart-hint" id="chartHint">বারে ক্লিক করে ছাত্রদের তালিকা দেখুন</span>
    </div>
    <div class="chart-wrap" id="chartWrap">
      <canvas id="mainChart"></canvas>
    </div>
  </div>
</section>

<!-- ═══ Modal ═══ -->
<div class="modal-overlay" id="studentModal">
  <div class="modal-content">
    <div class="modal-header">
      <h3 id="modalTitle"></h3>
      <button class="modal-close" id="modalCloseBtn" aria-label="Close">&times;</button>
    </div>
    <div class="modal-count" id="modalCount"></div>
    <div class="modal-list" id="modalList"></div>
  </div>
</div>

<!-- ═══ Footer ═══ -->
<footer>
  শহীদ সৈয়দ নজরুল ইসলাম কলেজ, ময়মনসিংহ
  <span class="footer-sep"></span>
  সেশন ২০০৩–২০০৫ ভর্তি তালিকা থেকে সংগৃহীত
  <br>
  ম্যাপে প্রদর্শিত {stats["plotted"]}/{stats["total"]} জন
  &nbsp;&middot;&nbsp;
  <a href="https://ssnic.edu.bd" target="_blank" rel="noopener">ssnic.edu.bd</a>
</footer>

<script>
(function(){{
/* ── Data ── */
const D={{labels:{district_labels_js},values:{district_values_js},colors:{district_colors_js}}};
const U={{labels:{upazila_labels_js},values:{upazila_values_js},colors:{upazila_colors_js}}};
const dStudents={district_students_js};
const uStudents={upazila_students_js};
const total={stats["plotted"]};

/* ── Chart state ── */
let chart=null, view='district';

function render(v){{
  view=v;
  const wrap=document.getElementById('chartWrap');
  const canvas=document.getElementById('mainChart');
  if(chart)chart.destroy();

  const isD=v==='district';
  const src=isD?D:U;
  const barH=isD?40:30;
  wrap.style.height=(src.labels.length*barH+60)+'px';

  document.getElementById('chartTitle').textContent=isD?'জেলা অনুযায়ী ছাত্র সংখ্যা':'উপজেলা অনুযায়ী ছাত্র সংখ্যা';
  document.getElementById('chartHint').textContent='বারে ক্লিক করে ছাত্রদের তালিকা দেখুন';

  chart=new Chart(canvas,{{
    type:'bar',
    data:{{
      labels:src.labels,
      datasets:[{{
        data:src.values,
        backgroundColor:src.colors.map(c=>c+'cc'),
        hoverBackgroundColor:src.colors,
        borderRadius:6,
        barThickness:isD?28:22
      }}]
    }},
    options:{{
      indexAxis:'y',
      responsive:true,
      maintainAspectRatio:false,
      onClick:function(evt,els){{
        if(!els.length)return;
        const idx=els[0].index;
        const label=src.labels[idx];
        const s=isD?dStudents[label]:uStudents[label];
        if(s)showModal(label,s);
      }},
      plugins:{{
        legend:{{display:false}},
        tooltip:{{
          backgroundColor:'#1e293b',
          titleFont:{{family:"'Noto Sans Bengali'"}},
          bodyFont:{{family:"'Noto Sans Bengali'"}},
          padding:10,
          cornerRadius:8,
          callbacks:{{
            label:function(ctx){{
              const v2=ctx.parsed.x;
              return ' '+v2+' জন ('+((v2/total)*100).toFixed(1)+'%)';
            }}
          }}
        }}
      }},
      scales:{{
        x:{{beginAtZero:true,grid:{{color:'#f1f5f9'}},ticks:{{color:'#94a3b8',font:{{family:"'Inter'"}}}}}},
        y:{{grid:{{display:false}},ticks:{{color:'#334155',font:{{family:"'Noto Sans Bengali'",size:isD?13:11}}}}}}
      }},
      onHover:function(evt,els){{evt.native.target.style.cursor=els.length?'pointer':'default'}}
    }}
  }});
}}

/* ── Toggle ── */
document.querySelectorAll('.toggle-btn').forEach(function(btn){{
  btn.addEventListener('click',function(){{
    document.querySelectorAll('.toggle-btn').forEach(function(b){{b.classList.remove('active')}});
    btn.classList.add('active');
    render(btn.dataset.view);
  }});
}});

/* ── Modal ── */
function showModal(title,students){{
  document.getElementById('modalTitle').textContent=title;
  document.getElementById('modalCount').textContent='মোট: '+students.length+' জন';
  var html='';
  for(var i=0;i<students.length;i++){{
    html+='<div class="student-row"><span class="student-roll">'+students[i].roll+'</span><span class="student-name">'+students[i].name+'</span></div>';
  }}
  document.getElementById('modalList').innerHTML=html;
  document.getElementById('studentModal').classList.add('show');
  document.body.style.overflow='hidden';
}}
function closeModal(){{
  document.getElementById('studentModal').classList.remove('show');
  document.body.style.overflow='';
}}
document.getElementById('studentModal').addEventListener('click',function(e){{if(e.target===e.currentTarget)closeModal()}});
document.getElementById('modalCloseBtn').addEventListener('click',closeModal);
document.addEventListener('keydown',function(e){{if(e.key==='Escape')closeModal()}});

/* ── Counter animation ── */
document.querySelectorAll('[data-count]').forEach(function(el){{
  var target=parseInt(el.dataset.count);
  var start=performance.now();
  var dur=1200;
  function tick(now){{
    var p=Math.min((now-start)/dur,1);
    var ease=1-Math.pow(1-p,3);
    el.textContent=Math.floor(ease*target);
    if(p<1)requestAnimationFrame(tick);
    else el.textContent=target;
  }}
  requestAnimationFrame(tick);
}});

/* ── Fade-in on scroll ── */
var obs=new IntersectionObserver(function(entries){{
  entries.forEach(function(e){{if(e.isIntersecting){{e.target.classList.add('visible');obs.unobserve(e.target)}}}});
}},{{threshold:0.1}});
document.querySelectorAll('.fade-in').forEach(function(el){{obs.observe(el)}});

/* ── District filter → map ── */
var mapIframe=document.getElementById('mapIframe');
document.getElementById('districtFilter').addEventListener('click',function(e){{
  var pill=e.target.closest('.filter-pill');
  if(!pill)return;
  document.querySelectorAll('.filter-pill').forEach(function(p){{p.classList.remove('active')}});
  pill.classList.add('active');
  var d=pill.dataset.district;
  if(mapIframe&&mapIframe.contentWindow){{
    mapIframe.contentWindow.postMessage({{district:d||null}},'*');
  }}
}});

/* ── Init ── */
render('district');
}})();
</script>
</body>
</html>'''


def main():
    print(f"Reading PDF: {PDF_PATH}")
    records = extract_records(PDF_PATH)
    print(f"Extracted {len(records)} records")

    rolls = {r["roll"] for r in records}
    missing_rolls = set(range(1, 241)) - rolls
    if missing_rolls:
        print(f"WARNING: Missing roll numbers: {sorted(missing_rolls)}")

    located = sum(1 for r in records if r["location"] is not None)
    unlocated = sum(1 for r in records if r["location"] is None)
    print(f"Located: {located}, Unlocated: {unlocated}")

    # Print unlocated
    unlocated_rolls = [r["roll"] for r in records if r["location"] is None]
    print(f"Unlocated rolls: {unlocated_rolls}")

    # Print sample names
    print("\nSample records:")
    for r in records[:5]:
        print(f"  Roll {r['roll']}: {r['name']} -> {r['location']}")

    # Save CSV
    with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["রোল", "নাম", "উপজেলা", "জেলা"])
        for r in records:
            upazila = r["location"][0] if r["location"] else ""
            district = r["location"][1] if r["location"] else ""
            writer.writerow([r["roll"], r["name"], upazila, district])
    print(f"CSV saved to: {CSV_PATH}")

    # Build full page with embedded map and charts
    m = build_map_for_embed(records)
    map_html_escaped = html_escape(m.get_root().render(), quote=True)
    stats = compute_statistics(records)
    full_page = build_full_page(map_html_escaped, stats)
    OUTPUT_PATH.write_text(full_page, encoding="utf-8")
    print(f"Page saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
