import json
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv

from name_gen import *
from space_containing import *

version = "3.0.1"

load_dotenv(os.path.join(Path.cwd(), ".env"))
api_url = os.environ.get("API_URL")
#api_url = "http://localhost:10000/api"

url_pattern = r"(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)"
si_pattern = r"s(äp|eyk|äpeyk)?(iv|ol|er|am|ìm|ìy|ay|ilv|irv|imv|iyev|ìyev|alm|ìlm|ìly|aly|arm|ìrm|ìry|ary|ìsy|asy)?(eiy|äng|eng|uy|ats)?i"
paren_pattern = r"(\(.+\))"
char_limit = 2000

global_onset = ["",""]

def get_language(inter):
    channel_languages = {
        1104882512607576114: "fr", # LN/fr/#commandes-bot
        298701183898484737: "de",  # LN/other/#deutsch
        365987412163297284: "fr",  # LN/other/#français
        466721683496239105: "nl",  # LN/other/#nederlands
        649363324143665192: "pl",  # LN/other/#polski
        507306946190114846: "ru",  # LN/other/#русский
        998643038878453870: "tr"   # LN/other/#türkçe
    }
    if inter.channel is None:
        return "en"
    if inter.channel.id in channel_languages:
        return channel_languages[inter.channel.id]
    server_languages = {
        935489523155075092: "en",
        395558141162422275: "en",
        154318499722952704: "en",
        860933619296108564: "en",
        1058520916612624536: "fr",
        1061696962304426025: "fr",
        1103339942538645605: "fr",
        1065673594354548757: "ru",
        1063774395748847648: "ru"
    }
    if inter.guild is None:
        return "en"
    if inter.guild_id not in server_languages:
        server_languages[inter.guild_id] = "en"
    return server_languages[inter.guild_id]


def format_ipa(word: dict) -> str:
    return word['IPA']


def do_underline(stressed: str, syllables: str) -> str:
    syllables = syllables.replace(" ", "-")
    if "-" not in syllables:
        return syllables
    s0 = int(stressed) - 1
    s1 = syllables.split("-")
    if s0 >= 0 and s0 < len(s1):
        s1[s0] = f"__{s1[s0]}__"
        return '-'.join(s1)
    return syllables


def format_breakdown(word: dict) -> str:
    breakdown = do_underline(word['Stressed'], word['Syllables'])
    if word['InfixDots'] != "NULL":
        breakdown += f", {word['InfixDots']}"
    return breakdown


def format_prefixes(word: dict) -> str:
    results = ""
    len_pre_list = ["me", "pxe", "ay", "fay",
                    "tsay", "fray", "pe", "pem", "pep", "pay"]
    prefixes = word['Affixes']['Prefix']
    if prefixes is not None and len(prefixes) > 0:
        results += "      prefixes: "
        for k, prefix in enumerate(prefixes):
            if k != 0:
                results += ", "
            if prefix in len_pre_list:
                results += f"**{prefix}**+"
            else:
                results += f"**{prefix}**-"
        results += "\n"
    return results


def format_infixes(word: dict) -> str:
    results = ""
    infixes = word['Affixes']['Infix']
    if infixes is not None and len(infixes) > 0:
        results += "      infixes: "
        for k, infix in enumerate(infixes):
            if k != 0:
                results += ", "
            results += f"<**{infix}**>"
        results += "\n"
    return results


def format_suffixes(word: dict) -> str:
    results = ""
    suffixes = word['Affixes']['Suffix']
    if suffixes is not None and len(suffixes) > 0:
        results += "      suffixes: "
        for k, suffix in enumerate(suffixes):
            if k != 0:
                results += ", "
            results += f"-**{suffix}**"
        results += "\n"
    return results

def format_comment(word: dict) -> str:
    results = ""
    comment = word['Affixes']['Comment']
    if comment is not None and len(comment) > 0:
        results += "      comment: "
        for k, comment in enumerate(comment):
            if k != 0:
                results += ", "
            results += f"**{comment}**"
        results += "\n"
    return results

def format_lenition(word: dict) -> str:
    results = ""
    lenition = word['Affixes']['Lenition']
    if lenition is not None and len(lenition) > 0:
        results += "      lenition: "
        for k, lenite in enumerate(lenition):
            if k != 0:
                results += ", "
            results += f"{lenite}"
        results += "\n"
    return results


def format_source(response_text: str) -> str:
    word = json.loads(response_text)
    if isinstance(word, dict) and "message" in word:
        return word["message"]
    results = ""
    for i in range(1, len(word) + 1):
        w = word[i - 1]
        if w['Source'] is None:
            results += f"[{i}] **{w['Navi']}**: no source results\n"
        else:
            w['Source'] = re.sub(url_pattern, r"<\1>", w['Source'])
            results += f"[{i}] **{w['Navi']}** @ {w['Source']}\n"
    return results


def format_audio(response_text: str) -> str:
    word = json.loads(response_text)
    if isinstance(word, dict) and "message" in word:
        return word["message"]
    results = ""
    for i in range(1, len(word) + 1):
        w = word[i - 1]
        syllables = do_underline(w['Stressed'], w['Syllables'])
        results += f"[{i}] **{w['Navi']}** ({syllables}) :speaker: [click here to listen](https://s.learnnavi.org/audio/vocab/{w['ID']}.mp3)\n"
    return results


def format_alphabet(letter: str, letters_dict: dict, names_dict: dict, i: int) -> str:
    letter = letter.lower()
    letter_id = -1
    current_letter = ""
    current_letter_name = ""
    if letter in letters_dict:
        letter_id = letters_dict[letter]
        current_letter = letter
        current_letter_name = list(names_dict.keys())[letter_id - 1]
    elif letter in names_dict:
        letter_id = names_dict[letter]
        current_letter = list(letters_dict.keys())[letter_id - 1]
        current_letter_name = letter
    if letter_id == -1:
        return f"[{i + 1}] **{letter}**: no results\n"
    return f"[{i + 1}] **{current_letter}** ({current_letter_name}) :speaker: [click here to listen](https://s.learnnavi.org/audio/alphabet/{letter_id}.mp3)\n"


def format(response_text: str, languageCode: str, showIPA: bool = False) -> str:
    words = json.loads(response_text)
    if isinstance(words, dict) and "message" in words:
        return words["message"]
    results = ""
    for i in range(1, len(words) + 1):
        word = words[i - 1]
        ipa = format_ipa(word)
        breakdown = format_breakdown(word)
        if showIPA:
            results += f"[{i}] **{word['Navi']}** [{ipa}] ({breakdown}) *{word['PartOfSpeech']}* {word[languageCode.upper()]}\n"
        else:
            results += f"[{i}] **{word['Navi']}** ({breakdown}) *{word['PartOfSpeech']}* {word[languageCode.upper()]}\n"
        results += format_prefixes(word)
        results += format_infixes(word)
        results += format_suffixes(word)
        results += format_lenition(word)
        results += format_comment(word)
    if len(results) > char_limit:
        return f"{len(words)} results. please search a more specific list, or use /random with number and same args"
    return results


def get_naive_plural_en(word_en: str) -> str:
    if word_en == 'stomach':
        return 'stomachs'
    endings_es = ['s', 'x', 'z', 'sh', 'ch']
    for ending in endings_es:
        if word_en.endswith(ending):
            return f"{word_en}es"
    return f"{word_en}s"


def format_translation(response_text: str, languageCode: str) -> str:
    words = json.loads(response_text)
    if isinstance(words, dict) and "message" in words:
        return "(?)"
    results = ""
    root_index = -1
    for i, word in enumerate(words):
        prefixes = word['Affixes']['Prefix']
        infixes = word['Affixes']['Infix']
        suffixes = word['Affixes']['Suffix']
        lenition = word['Affixes']['Lenition']
        if prefixes is None and infixes is None and suffixes is None and lenition is None:
            root_index = i
            break
    if root_index != -1:
        word = words[root_index]
        definition = f"{word[languageCode.upper()]}"
        definition_clean = re.sub(paren_pattern, "", definition)
        results += f"{definition_clean}"
    else:
        for i in range(len(words)):
            word = words[i]
            if i != 0:
                results += " / "
            definition = f"{word[languageCode.upper()]}"
            definition_clean = re.sub(paren_pattern, "", definition)
            prefixes = word['Affixes']['Prefix']
            if prefixes is not None:
                if "fì" in prefixes:
                    definition_clean = f"this {definition_clean}"
                elif "tsa" in prefixes:
                    definition_clean = f"that {definition_clean}"
                elif "fay" in prefixes:
                    definition_clean = f"these {get_naive_plural_en(definition_clean)}"
                elif "tsay" in prefixes:
                    definition_clean = f"those {get_naive_plural_en(definition_clean)}"
                elif "fra" in prefixes:
                    definition_clean = f"every {definition_clean}"
                elif "fray" in prefixes:
                    definition_clean = f"all {get_naive_plural_en(definition_clean)}"
            results += f"{definition_clean}"
    return results


def format_version(response_text: str) -> str:
    version_info = json.loads(response_text)
    version_text = "```\n"
    version_text += f"slash-fwew: {version}\n"
    version_text += f"fwew-api:   {version_info['APIVersion']}\n"
    version_text += f"fwew-lib:   {version_info['FwewVersion']}\n"
    version_text += f"dictionary: {version_info['DictVersion']}\n"
    version_text += "```"
    return version_text


def format_number(response_text: str) -> str:
    number = json.loads(response_text)
    if isinstance(number, dict) and "message" in number:
        return number["message"]
    name = number["name"]
    octal = number["octal"]
    decimal = number["decimal"]
    return f"`  na'vi`: {name}\n`  octal`: {octal}\n`decimal`: {decimal}"


def get_word_bundles(words: str) -> list[str]:
    result = []
    for pattern in patterns:
        if words[0] == '"' and words[-1] == '"':
            break
        else:
            words = re.sub(pattern, r'"\1"', words)
    yy = [c for c in re.split(r'("\w+ \w+\s?\w*")', words) if len(c) > 0]
    for w in yy:
        if w.startswith('"') and w.endswith('"'):
            result.append(w[1:-1])
        else:
            result.extend(w.split())
    result = [r for r in result if r != '"']
    return result


def get_fwew(languageCode: str, words: str, showIPA: bool = False, fixesCheck = True) -> str:
    results = ""
    word_list = get_word_bundles(words)
    for i, word in enumerate(word_list):
        if i != 0:
            results += "\n"
        if fixesCheck or word == "pela'ang":
            res = requests.get(f"{api_url}/fwew/{word}")
        else:
            res = requests.get(f"{api_url}/fwew-simple/{word}")
        text = res.text
        results += format(text, languageCode, showIPA)
    return results


def get_fwew_reverse(languageCode: str, words: str, showIPA: bool = False) -> str:
    results = ""
    word_list = words.split()
    for i, word in enumerate(word_list):
        if i != 0:
            results += "\n"
        res = requests.get(f"{api_url}/fwew/r/{languageCode.lower()}/{word}")
        text = res.text
        results += format(text, languageCode, showIPA)
    return results


def get_profanity(lang: str, showIPA: bool) -> str:
    words = "skxawng kalweyaveng kurkung pela'ang pxasìk teylupil tsahey txanfwìngtu vonvä' wiya"
    return get_fwew(lang, words, showIPA, fixesCheck=False)


def get_source(words: str) -> str:
    results = ""
    word_list = get_word_bundles(words)
    for i, word in enumerate(word_list):
        if i != 0:
            results += "\n"
        res = requests.get(f"{api_url}/fwew/{word}")
        text = res.text
        results += format_source(text)
    return results


def get_audio(words: str) -> str:
    results = ""
    word_list = get_word_bundles(words)
    for i, word in enumerate(word_list):
        if i != 0:
            results += "\n"
        res = requests.get(f"{api_url}/fwew/{word}")
        text = res.text
        results += format_audio(text)
    return results


def get_alphabet(letters: str) -> str:
    letters_dict = {
        "'": 1, "a": 2, "aw": 3, "ay": 4, "ä": 5, "e": 6, "ew": 7, "ey": 8,
        "f": 9, "h": 10, "i": 11, "ì": 12, "k": 13, "kx": 14, "l": 15, "ll": 16,
        "m": 17, "n": 18, "ng": 19, "o": 20, "p": 21, "px": 22, "r": 23, "rr": 24,
        "s": 25, "t": 26, "tx": 27, "ts": 28, "u": 29, "v": 30, "w": 31, "y": 32,
        "z": 33,
    }
    names_dict = {
        "tìftang": 1, "a": 2, "aw": 3, "ay": 4, "ä": 5, "e": 6, "ew": 7, "ey": 8,
        "fä": 9, "hä": 10, "i": 11, "ì": 12, "kek": 13, "kxekx": 14, "lel": 15,
        "'ll": 16, "mem": 17, "nen": 18, "ngeng": 19, "o": 20, "pep": 21,
        "pxepx": 22, "rer": 23, "'rr": 24, "sä": 25, "tet": 26, "txetx": 27,
        "tsä": 28, "u": 29, "vä": 30, "wä": 31, "yä": 32, "zä": 33
    }
    results = ""
    letter_list = letters.split()
    for i, letter in enumerate(letter_list):
        if i != 0:
            results += "\n"
        results += format_alphabet(letter, letters_dict, names_dict, i)
    return results


def get_list(languageCode: str, args: str, showIPA: bool) -> str:
    res = requests.get(f"{api_url}/list/{args}")
    text = res.text
    return format(text, languageCode, showIPA)


def get_random(languageCode: str, n: int, showIPA: bool) -> str:
    res = requests.get(f"{api_url}/random/{n}")
    text = res.text
    return format(text, languageCode, showIPA)


def get_random_filter(languageCode: str, n: int, args: str, showIPA: bool) -> str:
    res = requests.get(f"{api_url}/random/{n}/{args}")
    text = res.text
    return format(text, languageCode, showIPA)


def get_number(word: str) -> str:
    res = requests.get(f"{api_url}/number/{word}")
    text = res.text
    return format_number(text)


def get_number_reverse(num: int) -> str:
    if int(num) > 32767:
        return "Error: Maximum is 32,767 (octal: 077777)"
    if int(num) < 0:
        return "Na'vi has no negative numbers"
    res = requests.get(f"{api_url}/number/r/{num}")
    text = res.text
    return format_number(text)


def get_line_ending(word: str) -> str:
    results = ""
    match = re.search(r"([.?!]+)$", word)
    if match and match.group() is not None:
        results += match.group()
        results += "\n\n"
    return results


def get_translation(text: str, languageCode: str) -> str:
    results = ""
    word_list = get_word_bundles(text)
    for i, word in enumerate(word_list):
        if i != 0 and not results.endswith("\n"):
            results += " **|** "
        word = word_list[i]
        if re.match(r"hrh", word):
            results += f"lol{get_line_ending(word)}"
            continue
        elif word == "a":
            results += "that"
            continue
        elif re.match(si_pattern, word):
            results += f"do / make{get_line_ending(word)}"
            continue
        elif word == "srake":
            results += "(yes/no question)"
            continue
        elif re.match(r"srak", word):
            results += f"(yes/no question){get_line_ending(word)}"
            continue
        res = requests.get(f"{api_url}/fwew/{word}")
        text = res.text
        results += format_translation(text, languageCode)
        results += get_line_ending(word)
    if len(results) > char_limit:
        return f"translation exceeds character limit of {char_limit}"
    return results

# Helper function for name-alu()
def one_word_verb(intransitive_or_si_allowed: bool, current):
    new_verb = current['InfixDots'].split()
    pos = current['PartOfSpeech']
    query = ""
    buffer = ""
    # Transitive or intransitive allowed
    if intransitive_or_si_allowed:
        # one word and not si: allowed (e.g. "takuk")
        # two words and not si: disallowed (e.g. "tswìk kxenerit")
        # one word and si: disallowed ("si" only)
        # two words and si: allowed (e.g. "unil si")
        # Any three-word verb: disallowed ("eltur tìtxen si" only)
        # != is used as an exclusive "or"
        while (len(new_verb) == 2) != (new_verb[-1] == "s..i"):
            query = requests.get(f"{api_url}/random/1/pos starts v")
            buffer = json.loads(query.text)
            new_verb = buffer[0]['InfixDots'].split()
            pos = buffer[0]['PartOfSpeech']
    else: # Transitive verbs only
        while len(new_verb) > 1:
            query = requests.get(f"{api_url}/random/1/pos starts vtr")
            buffer = json.loads(query.text)
            new_verb = buffer[0]['InfixDots'].split()
            pos = buffer[0]['PartOfSpeech']
    return new_verb, pos

# One-word names to be sent to Discord
def get_single_name_discord(n: int, dialect: str, s: int):
    results = ""
    
    if not valid(int(n), [int(s)]):
        results = "Max name-count is 50, max syllables is 4"
    else:
        for k in range(0,int(n)):
            results += get_single_name(int(s),dialect) + "\n"
    return results

# Full names to be sent to Discord
def get_name(ending: str, n: int, dialect: str, s1: int, s2: int, s3: int) -> str:
    results = ""
    # for temp storage before appending to results
    loader = ""
    if not valid(int(n), [int(s1), int(s2), int(s3)]):
        results = "Max name-count is 50, max syllables-1/2/3 are 4"
    else:
        n, s1, s2, s3 = int(n), int(s1), int(s2), int(s3)
        mk = 0
        # Do entire generator process n times
        for mk in range(0,n):
            loader = ""

            # BUILD FIRST NAME
            # first syllable: CV
            loader += get_single_name(s1,dialect)

            loader += " te "

            # BUILD FAMILY NAME
            loader += get_single_name(s2,dialect)

            loader += " "

            # BUILD PARENT'S NAME
            loader += get_single_name(s3,dialect)

            # ADD ENDING
            if loader.endswith("'"):
                loader = loader.removesuffix("'")
            if dialect == "reef" and loader[-1] in ["a", "e", "ì", "o", "u", "i", "ä", "ù"]:# , "w", "y"}: # does kaw'it become kawit?
                loader += ending[1:]
            else:
                loader += ending
            
            # BEWARE THE 2000 CHARACTER LIMIT
            if len(loader) + len(results) > 1914: # 1914 picked though manual testing as the highest possible super reliable number
                return results + loader + "\n(stopped at " + str(mk + 1) + ". 2000 Character limit)"
            else:
                results += loader + "\n"

    return results

# [name] the [adjective] [noun] format names to be sent to Discord
def get_name_alu(n: int, dialect: str, s: int, noun_mode: str, adj_mode: str) -> str:
    results = ""
    if not valid(int(n), [int(s)]):
        results = "Max name-count is 50, max syllables is 4"
    else:
        n, s = int(n), int(s)

        # Adjectives and nouns can be shared across loops
        buffer = ""

        # Find out how many of these names we want and what kinds
        name_kinds = []
        nouns = 0
        adjectives = 0
        verbs = 0
        transitive_verbs = 0

        #
        # STAGE 1:
        # Decide what kind and how many nouns we need
        #
        
        mode = 0
        if noun_mode == "normal noun":
            nouns = n # n nouns
            mode = 1
        elif noun_mode == "verb-er":
            verbs = n # n verbs
            mode = 2
        else:
            for mk in range(n):
                a = random.randint(1,5)
                if a == 1: # 80% chance of normal noun
                    a = 2
                    verbs += 1
                else:
                    a = 1
                    nouns += 1
                name_kinds.append([a,2]) # something, normal adjective
        
        # If the noun mode isn't "something",
        # Input homogenous noun modes
        if mode != 0:
            for mk in range(n):
                name_kinds.append([mode,2]) # mode, normal adjective
        
        mode = 0
        # Same, but for adjectives
        if adj_mode == "none":
            mode = 1
        if adj_mode == "normal adjective":
            adjectives = n # It's the only thing that controls how Adjectives gets its value
            # No need for name_kinds[mk][1] = 2.  We set that already
        elif adj_mode == "genitive noun":
            mode = 3
            nouns += n
        elif adj_mode == "origin noun":
            mode = 4
            nouns += n
        elif adj_mode == "participle verb":
            mode = 5
            verbs += n
        elif adj_mode == "active participle verb":
            mode = 6
            verbs += n
        elif adj_mode == "passive participle verb":
            mode = 7
            transitive_verbs = n # Also has no other thing adding to it
        elif adj_mode == "something": # cannot pick "none"
            for mk in range(n):
                mode_2 = random.randint(-1,6)
                if mode_2 <= 2: # 50% chance of normal adjective
                    mode_2 = 2
                    adjectives += 1
                elif mode_2 >= 5: # Verb participles get two sides of the die
                    mode_2 = 5
                    verbs += 1
                else:
                    nouns += 1
                name_kinds[mk][1] = mode_2
        elif adj_mode == "any": # can pick "none", equal chance of anything
            # verb participles get one side, just like every option
            for mk in range(n):
                mode_2 = random.randint(0,5)
                if mode_2 == 2:
                    adjectives += 1
                elif mode_2 <= 4:
                    nouns += 1
                else: # mode is 5
                    verbs += 1
                name_kinds[mk][1] = mode_2
        
        # If adj_mode isn't "something" or "any",
        # Input homogenous adjective modes
        if mode != 0:
            for mk in range(n):
                name_kinds[mk][1] = mode

        #
        # STAGE 2:
        # Look up all the words we need
        #
        if nouns > 0:
            query = requests.get(f"{api_url}/random/{nouns}/pos is n.")
            nouns = json.loads(query.text)
        
        if verbs > 0:
            query = requests.get(f"{api_url}/random/{verbs}/pos starts v")
            verbs = json.loads(query.text)
        
        if adjectives > 0:
            query = requests.get(f"{api_url}/random/{adjectives}/pos is adj.")
            adjectives = json.loads(query.text)
        
        if transitive_verbs > 0: # allow transitive modal verbs, too
            query = requests.get(f"{api_url}/random/{transitive_verbs}/pos starts vtr")
            transitive_verbs = json.loads(query.text)
        
        #
        # STAGE 3:
        # Apply the words as needed
        #
        
        for kind in name_kinds:
            results += get_single_name(s,dialect) + " alu "

            noun = ""

            two_word_noun = False
            # What kind of noun do we have?
            if kind[0] == 2: #verb-er noun
                verber = verbs.pop(0)

                # Throw us our current word if valid, get a new one if not
                new_noun, pos = one_word_verb(True, verber) # intransitive and si-verbs are allowed
                
                for a in new_noun:
                    noun += a.replace(".","")
                noun += "yu"
                results += glottal_caps(noun) + " "
            else:
                noun = nouns.pop(0)["Navi"].split()
                # If there's more than one word in the noun, the adjective comes first
                if len(noun) > 1:
                    two_word_noun = True
                else:
                    results += glottal_caps(noun[0]) + " "
            # Wivatch youä profanitit
            # if noun in ["kalweyaveng", "kurkung", "la'ang",
            #            "skxawng", "teylupil", "txanfwìngtu", "vonvä'"]:
            #    noun = "Skxawng"

            adj = ""
            mode = kind[1]
            
            # ADJECTIVE
            if mode == 2:
                # Get adjectives
                adj = adjectives.pop(0)["Navi"]
                # Unlike the other le-adjectives, these don't put le- in front of a preexisting word.
                fake_le_adjectives = ["ler", "leyr"]
                # Forest doesn't duplicate an a in apxa   | Even if after a noun | le-adjectives don't need an a
                if (not two_word_noun) and (adj[0] != 'a' or dialect != "forest") and (adj in fake_le_adjectives or not adj.startswith("le")):
                    adj = "a" + adj
                elif two_word_noun and (adj[-1] != 'a' or dialect != "forest"):
                    adj += "a "
                
                results += glottal_caps(adj)
            # GENITIVE OR ORIGIN NOUN
            elif mode == 3 or mode == 4:
                loader = ""
                # Get nouns
                words = nouns.pop(0)["Navi"]
                wordList = words.split()

                yvowels = ['a', 'e', 'ì', 'i', 'ä']

                # Genitive noun
                if mode == 3:
                    # The only nouns put together using a space
                    if words == "tsko swizaw":
                        results += "Tsko Swizawyä"
                    elif words == "toruk makto":
                        results += "Torukä Maktoyuä"
                    # the only noun with two spaces
                    elif words == "mo a fngä'":
                        results += "Moä a Fgnä'"
                    # Watch your profanity
                    # elif words in ["kalweyaveng", "kurkung", "la'ang",
                    #               "skxawng", "teylupil", "txanfwìngtu", "vonvä'"]:
                    #    results += "Skxawngä "
                    elif two_word_noun: # Origin noun goes before the noun
                        for i in range(len(wordList) - 1, -1, -1):
                            loader = ""
                            # The only a-attributed word in the dictionary, part of "swoasey ayll"
                            if wordList[i] == "ayll":
                                loader += "Ylla "
                            elif wordList[i].startswith("le"):
                                loader += glottal_caps(wordList[i]) + "a "
                            elif wordList[i].endswith("yä"):
                                loader += glottal_caps(wordList[i]) + " "
                            elif wordList[i].endswith("ia"): # aungia, meuia, soaia, tìftia, kemuia
                                loader += glottal_caps(wordList[i][:-1]) + "ä "
                            elif wordList[i][-1] in yvowels:
                                loader += glottal_caps(wordList[i]) + "yä "
                            else: #If's it's a conosonent, psuedovowel, xdiphthong, o or u
                                loader += glottal_caps(wordList[i]) + "ä "
                            results += loader
                    else: # Origin noun goes after the noun
                        first = True
                        loader = ""
                        for i in wordList:
                            # Only put the genitive on the first word in the noun
                            if first:
                                if i.endswith("ia"): # aungia, meuia, soaia, tìftia, kemuia
                                    loader += glottal_caps(i[:-1]) + "ä "
                                elif i[-1] in yvowels:
                                    loader += glottal_caps(i) + "yä "
                                else: #If's it's a conosonent, psuedovowel, diphthong, o or u
                                    loader += glottal_caps(i) + "ä "
                                first = False
                                continue
                            loader += glottal_caps(i)
                        results += loader
                # Origin noun
                elif mode == 4:
                    # The only nouns put together using a space
                    if words == "tsko swizaw":
                        results += "ta Tsko Swizaw"
                    elif words == "toruk makto":
                        results += "ta Torukä Maktoyu"
                    # the only noun with two spaces
                    elif words == "mo a fngä'":
                        results += "ta Mo a Fgnä'"
                    # Watch your profanity
                    # elif words in ["kalweyaveng", "kurkung", "la'ang",
                    #                "skxawng", "teylupil", "txanfwìngtu", "vonvä'"]:
                    #     results += "Skxawngta "i
                    elif two_word_noun: # Origin noun goes before the noun
                        for i in range(len(wordList) - 1, -1, -1):
                            loader = ""
                            # The only a-attributed word in the dictionary, part of "swoasey ayll"
                            if wordList[i] == "ayll":
                                loader += "Ylla "
                            elif wordList[i].startswith("le"):
                                loader += glottal_caps(wordList[i]) + "a "
                            elif wordList[i].endswith("yä"):
                                loader += glottal_caps(wordList[i]) + " "
                            else:
                                loader += "ta " + glottal_caps(wordList[i]) + " "
                            results += loader
                    else: # Origin noun goes after the noun
                        first = True
                        loader = ""
                        for i in wordList:
                            # Only put the origin on the first noun
                            if first:
                                loader += "ta " + glottal_caps(i)
                                first = False
                                continue
                            loader += " " + glottal_caps(i)
                        results += loader
            # PARTICIPLES
            elif mode >= 5:
                new_verb, pos = "", ""
                infix = "us" # greater than 50% chance of <us> if left random
                # VERB WITH UNSPECIFIED PARTICIPLE INFIX
                if mode == 5:
                    new_verb, pos = one_word_verb(True, verbs.pop(0))
                    # If transitive verb, 50% chance of <awn>
                    if pos.startswith("vtr") and bool(random.getrandbits(1)):
                        infix = "awn"
                # VERB WITH SPECIFIED PARTICIPLE INFIX
                elif mode == 6:
                    # Any verb can have <us>
                    new_verb, pos = one_word_verb(True, verbs.pop(0))
                else:
                    # Only transitive verbs can have <awn>
                    new_verb, pos = one_word_verb(False, transitive_verbs.pop(0))
                    infix = "awn"
                
                #adj += adj_loader[0]
                for word in new_verb:
                    found_dots = False
                    if "." in word: # This word gets the infixes
                        for a in word:
                            if a == ".":
                                if not found_dots:
                                    adj += infix
                                    found_dots = True
                            else:
                                adj += a
                    else: # Other words:
                        adj += word
                    # Hyphens for word-s<us>i:
                    if word != new_verb[-1]:
                        adj += "-"
                
                # Forest doesn't duplicate an a in apxa   | Even if after a noun
                if (not two_word_noun) and (adj[0] != 'a' or dialect != "forest"):
                    adj = "a" + adj
                elif two_word_noun and (adj[-1] != 'a' or dialect != "forest"):
                    adj += "a "
                
                results += glottal_caps(adj)
            
            # If the adjective came first, put the two-word noun on.
            if two_word_noun:
                for n in noun:
                    results += glottal_caps(n) + " "

            # ADD ENDING
            results += "\n"

    return results

def get_phonemes() -> str:
    return get_phoneme_frequency_chart()


def get_lenition() -> str:
    return """```
kx → k
px → p
tx → t

k  → h
p  → f
t  → s

ts → s

'  → (disappears, except before ll or rr)
```"""

def get_len() -> str:
    return """```
kx, px, tx -> k, p, t
   k, p, t -> h, f, s
        ts -> s
         ' -> (disappears, except before ll or rr)
```"""

def get_all_thats() -> str:
    return """```
Case|Noun |   Clause wrapper   |
    |     |prox.| dist.|answer |
====|=====|=====|======|=======|
Sub.|Tsaw |Fwa  |Tsawa |Teynga |
Agt.|Tsal |Fula |Tsala |Teyngla|
Pat.|Tsat |Futa |Tsata |Teyngta|
Gen.|Tseyä| N/A |  N/A |
Dat.|Tsar |Fura |Tsara |
Top.|Tsari|Furia|Tsaria|

tsa-      pre.  that
tsa'u     n.    that (thing)
tsakem    n.    that (action)
fmawnta   sbd.  that news
fayluta   sbd.  these words
tsnì      sbd.  that (function word)
tsonta    conj. to (with kxìm)
kuma/akum conj. that (as a result)
a         part. clause level attributive marker
```"""

def get_cameron_words() -> str:
    return """## Cameron words:
- **A1 Names:** Akwey, Ateyo, Eytukan, Eywa, Mo'at, Na'vi, Newey, Neytiri, Ninat, Omatikaya, Otranyu, Rongloa, Silwanin, Tskaha, Tsu'tey, Tsumongwi
- **A2 Names:** Aonung, Kiri, Lo'ak, Neteyam, Ronal, Rotxo, Tonowari, Tuktirey, Tsireya
- **Nouns:** 'itan, 'ite, atan, au *(drum)*, eyktan, i'en, Iknimaya, mikyun, ontu, seyri, tsaheylu, tsahìk, unil
- **Life:** Atokirina', Ikran, Palulukan, Riti, talioang, teylu, Toruk
- **Other:** eyk, irayo, makto, taron, te"""



def get_version() -> str:
    res = requests.get(f"{api_url}/version")
    return format_version(res.text)
