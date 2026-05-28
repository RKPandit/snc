#!/usr/bin/env python3
"""
Generate an interactive Folium map of student home locations from SNC PDF.

Shaheed Sayed Nazrul Islam College, Session 2003-2005, Science Department.
Extracts 240 student records from snc.pdf and plots ~237 on a map of Bangladesh.

The PDF uses SutonnyMJ (Bijoy) font encoding, so text must be converted to Unicode.
"""

import csv
import re
from collections import defaultdict
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
    "ময়মনসিংহ": "#1f77b4",
    "নেত্রকোনা": "#2ca02c",
    "জামালপুর": "#ff7f0e",
    "শেরপুর": "#9467bd",
    "কিশোরগঞ্জ": "#d62728",
    "টাঙ্গাইল": "#8c564b",
    "গোপালগঞ্জ": "#5f9ea0",
    "ঢাকা": "#006400",
    "নরসিংদী": "#e377c2",
    "মানিকগঞ্জ": "#17becf",
    "ব্রাহ্মণবাড়ীয়া": "#7b68ee",
    "ঠাকুরগাঁও": "#90ee90",
    "বরিশাল": "#f5deb3",
    "নোয়াখালী": "#a9a9a9",
    "চাঁদপুর": "#808080",
    "বিনাইদহ": "#333333",
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


def build_map(records):
    """Build a Folium map from student records."""
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
        location=[24.75, 90.40],
        zoom_start=9,
        tiles="OpenStreetMap",
        control_scale=True,
        prefer_canvas=True,
    )

    # Mask everything outside Bangladesh with a dark overlay
    bangladesh_boundary = [
        [92.672721,22.041239],[92.652257,21.324048],[92.303234,21.475485],
        [92.368554,20.670883],[92.082886,21.192195],[92.025215,21.70157],
        [91.834891,22.182936],[91.417087,22.765019],[90.496006,22.805017],
        [90.586957,22.392794],[90.272971,21.836368],[89.847467,22.039146],
        [89.70205,21.857116],[89.418863,21.966179],[89.031961,22.055708],
        [88.876312,22.879146],[88.52977,23.631142],[88.69994,24.233715],
        [88.084422,24.501657],[88.306373,24.866079],[88.931554,25.238692],
        [88.209789,25.768066],[88.563049,26.446526],[89.355094,26.014407],
        [89.832481,25.965082],[89.920693,25.26975],[90.872211,25.132601],
        [91.799596,25.147432],[92.376202,24.976693],[91.915093,24.130414],
        [91.46773,24.072639],[91.158963,23.503527],[91.706475,22.985264],
        [91.869928,23.624346],[92.146035,23.627499],[92.672721,22.041239],
    ]
    # World outer ring [lng, lat], Bangladesh hole reversed for GeoJSON winding
    world_ring = [[-180, -90], [180, -90], [180, 90], [-180, 90], [-180, -90]]
    bd_hole = list(reversed(bangladesh_boundary))
    mask_geojson = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [world_ring, bd_hole],
        },
    }
    folium.GeoJson(
        mask_geojson,
        style_function=lambda x: {
            "fillColor": "#ffffff",
            "fillOpacity": 1.0,
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

    # Title banner
    title_html = f"""
    <div style="position:fixed;top:10px;left:50%;transform:translateX(-50%);
         z-index:1000;background:white;padding:10px 20px;border-radius:8px;
         box-shadow:0 2px 6px rgba(0,0,0,0.3);font-family:'Noto Sans Bengali',sans-serif;
         font-size:16px;font-weight:bold;text-align:center;max-width:90vw;">
        শহীদ সৈয়দ নজরুল ইসলাম কলেজ<br>
        <span style="font-size:12px;font-weight:normal;">
        সেশন ২০০৩-২০০৫ | বিজ্ঞান বিভাগ | মোট ছাত্র: {total} | ম্যাপে: {plotted}
        </span>
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))

    # Legend
    legend_items = "".join(
        f'<div style="margin:2px 0;"><span style="display:inline-block;width:14px;height:14px;'
        f'background:{color};border-radius:3px;margin-right:6px;vertical-align:middle;"></span>'
        f'<span style="vertical-align:middle;font-size:12px;">{district}</span></div>'
        for district, color in DISTRICT_COLORS.items()
    )
    legend_html = f"""
    <div style="position:fixed;bottom:30px;right:10px;z-index:1000;background:white;
         padding:10px;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.3);
         font-family:'Noto Sans Bengali',sans-serif;max-height:300px;overflow-y:auto;">
        <div style="font-size:13px;font-weight:bold;margin-bottom:4px;">জেলা</div>
        {legend_items}
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # Meta tags
    head_html = """
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Bengali:wght@400;700&display=swap" rel="stylesheet">
    <meta property="og:title" content="SNC Science 2003-2005 - Student Map" />
    <meta property="og:description" content="শহীদ সৈয়দ নজরুল ইসলাম কলেজ - ২০০৩-২০০৫ সেশনের বিজ্ঞান বিভাগের ছাত্রদের ম্যাপ" />
    <meta property="og:type" content="website" />
    """
    m.get_root().header.add_child(folium.Element(head_html))

    return m


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

    # Build and save map
    m = build_map(records)
    m.save(str(OUTPUT_PATH))
    print(f"Map saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
