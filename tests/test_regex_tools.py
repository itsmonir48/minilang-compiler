from itertools import product

import pytest

from minilang import regex_tools as rt


def test_prefixes_suffixes():
    assert rt.prefixes("abc") == ["", "a", "ab", "abc"]
    assert rt.suffixes("abc") == ["abc", "bc", "c", ""]
    assert rt.proper_prefixes("banana") == ["b", "ba", "ban", "bana", "banan"]
    assert rt.proper_suffixes("abc") == ["bc", "c"]


def test_substrings_and_subsequences():
    assert rt.substrings("ab") == {"", "a", "b", "ab"}
    assert rt.proper_substrings("abc") == {"a", "b", "c", "ab", "bc"}
    assert rt.subsequences("abc") == {"", "a", "b", "c", "ab", "ac", "bc", "abc"}
    assert "ac" not in rt.substrings("abc")


@pytest.mark.parametrize("s", ["", "a", "ab", "abcde", "compil"])
def test_formulas_hold_for_distinct_characters(s):
    assert rt.string_report(s) == rt.count_formulas(len(s))


def test_repeated_characters_give_fewer():
    report = rt.string_report("banana")
    assert report["substrings"] < rt.count_formulas(6)["substrings"]


@pytest.mark.parametrize("name, good, bad", [
    ("vowels", ["facetious", "abstemious", "aeiou", "aaeiouu"], ["aeiuo", "aeio", "uoiea"]),
    ("ascending", ["", "abc", "aabcz", "z"], ["ba", "abca"]),
    ("comment", ["/**/", "/* x */", "/* a * b */", "/***/", "/* x **/"], ["/* a */ b */", "/*/", "/* x"]),
    ("no_repeat_digit", ["0", "1234567890", "93"], ["11", "1231", ""]),
    ("one_repeat_digit", ["112", "1211", "123"], ["1122", "112233"]),
    ("chess", ["p-k4", "kbp*qn", "n-kb3", "q*p"], ["p-k9", "x-k4", "p k4"]),
    ("sql_select", ["select", "SELECT", "SeLeCt"], ["selec", "selects"]),
])
def test_definitions(name, good, bad):
    for s in good:
        assert rt.matches(name, s), s
    for s in bad:
        assert not rt.matches(name, s), s


def _brute(n: int):
    for k in range(n + 1):
        for t in product("ab", repeat=k):
            yield "".join(t)


def test_no_abb_substring_against_brute_force():
    for s in _brute(9):
        assert rt.matches("no_abb", s) == ("abb" not in s), s


def test_no_abb_subsequence_against_brute_force():
    for s in _brute(9):
        assert rt.matches("no_abb_subseq", s) == ("abb" not in rt.subsequences(s)), s


def test_vowels_against_definition():
    import re
    words = ["facetious", "sequoia", "education", "aeiou", "aeoiu", "abcdefghijklmnopqrstu"]
    for w in words:
        vowels = re.sub("[^aeiou]", "", w)
        expected = set(vowels) == set("aeiou") and list(vowels) == sorted(vowels)
        assert rt.matches("vowels", w) == expected, w


def test_strings_command(capsys):
    from minilang.cli import main
    assert main(["strings", "abc"]) == 0
    out = capsys.readouterr().out
    assert "proper prefixes   : 'a', 'ab'" in out
    assert "subsequences      : ε, 'a', 'b', 'c', 'ab', 'ac', 'bc', 'abc'" in out


def test_regex_command(capsys):
    from minilang.cli import main
    assert main(["regex"]) == 0
    assert "no_abb" in capsys.readouterr().out
    assert main(["regex", "chess", "p-k4", "p-k9"]) == 0
    out = capsys.readouterr().out
    assert "'p-k4'  yes" in out and "'p-k9'  no" in out
    assert main(["regex", "nope"]) == 2
