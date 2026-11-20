from collections import Counter

import pytest

from kb.cases import case_files, find_sensitive, load_cases, load_taxonomy, parse_case, validate_case

TAXONOMY = load_taxonomy()
CASE_FILES = case_files()


def test_there_are_cases():
    assert CASE_FILES


@pytest.mark.parametrize("path", CASE_FILES, ids=lambda p: p.stem)
def test_case_is_valid(path):
    assert validate_case(parse_case(path), TAXONOMY) == []


def test_ids_are_unique():
    counts = Counter(c.id for c in load_cases())
    assert [i for i, n in counts.items() if n > 1] == []


def test_reviewed_only_filter():
    all_cases = load_cases()
    reviewed = load_cases(reviewed_only=True)
    assert all(c.reviewed for c in reviewed)
    assert len(reviewed) == sum(c.reviewed for c in all_cases)


def test_taxonomy_lists_have_no_duplicates():
    for name, values in TAXONOMY.items():
        assert len(values) == len(set(values)), name


@pytest.mark.parametrize("text", [
    "Unit at 192.168.10.5 tripped",
    "MAC 00:1A:2B:3C:4D:5E",
    "contact tech@example.com",
    "SN: 4F7K22009",
    "module AB12-7781 replaced",
])
def test_sensitive_scan_detects(text):
    assert find_sensitive(text)


@pytest.mark.parametrize("text", [
    "See CASE-014 for a similar trip.",
    "IGBT module overtemperature at about 5% above rated power.",
    "Checked the 24 V auxiliary supply.",
    "Serial fieldbus link between the EMS and PCS.",
])
def test_sensitive_scan_allows(text):
    assert find_sensitive(text) == []


def test_validation_reports_problems(tmp_path):
    bad = tmp_path / "CASE-999.md"
    bad.write_text(
        "---\nid: CASE-998\ntitle: x\nsymptom_component: fan\nroot_cause_component: cooling\n"
        "operating_mode: charging\nalarm_categories: [made_up]\nimpact: trip\nsource: synthetic\nreviewed: maybe\n---\n"
        "## Symptoms\nUnit at 10.0.0.1\n## Extra\ntext\n",
        encoding="utf-8",
    )
    errors = validate_case(parse_case(bad), TAXONOMY)
    joined = "\n".join(errors)
    for expected in ["does not match id", "symptom_component", "made_up", "reviewed must be",
                     "section 'Conditions'", "unknown section 'Extra'", "IPv4"]:
        assert expected in joined, expected
