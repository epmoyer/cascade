import pytest

from cascade.util import make_json, get_requirement_id

@pytest.mark.parametrize("req_text, req_id", [
    # Positives
    ('[ABC-DEF-123,X]', 'ABC-DEF-123'),
    ('[ABC-DEF-123, X, GUI-796]', 'ABC-DEF-123'),
    ('[ABC-DEF-123, X, GUI-796]', 'ABC-DEF-123'),
    (' [ ABC-DEF-123 , X, GUI-796, X, X, X]', 'ABC-DEF-123'),
    (' [ ABC-DEF-1 , X, GUI-796]', 'ABC-DEF-1'),
    (' [ ABC-DEF-123,2xy] ', 'ABC-DEF-123'),
    (' [ ABC-DEF-123, 2xy] ', 'ABC-DEF-123'),
    ('  \t[  \tABC-DEF-123,\t 2xy \t]\t ', 'ABC-DEF-123'),

    # Negatives
    ('[ABC-DEF-,X]', None),
    ('[ABC-DEF-?,X]', None),
    ('[ABC-DEF-??,X]', None),
    ('[ABC-DEF-G,X]', None),
    ('[ABC-DEF-GH,X]', None),
    ('[ABC]', None),
    ('[ABC-DEF]', None),
    ('[ABC-DEF-123]', None),
    ('[ABC-DEF-123,]', None),
    ('[ SRD-RCN-art-09-796]', None),
    ('[ SRD-RCN-123,2wf', None),
    ('[ SRD-RCN-123,2wf]abc', None),
    ('[ SRD-RCN-123,2wf] abc', None),
    ('[ABC-DEF-123,X]\nLine2\nLine3', None),
    ('Line1\n[ABC-DEF-123,X]\nLine3', None),
])

def test_get_requirement_id_strict(req_text, req_id):
    r = get_requirement_id(req_text, fuzzy=False)
    assert r == req_id

@pytest.mark.parametrize("req_text, req_id", [
    # Positives
    ('[ABC-DEF-123,X]', 'ABC-DEF-123'),
    ('[ABC-DEF-123, X, GUI-796]', 'ABC-DEF-123'),
    ('[ABC-DEF-123, X, GUI-796]', 'ABC-DEF-123'),
    (' [ ABC-DEF-123 , X, GUI-796, X, X, X]', 'ABC-DEF-123'),
    (' [ ABC-DEF-1 , X, GUI-796]', 'ABC-DEF-1'),
    (' [ ABC-DEF-123,2xy] ', 'ABC-DEF-123'),
    (' [ ABC-DEF-123, 2xy] ', 'ABC-DEF-123'),
    ('  \t[  \tABC-DEF-123,\t 2xy \t]\t ', 'ABC-DEF-123'),
    ('[ABC-DEF-,X]',   'ABC-DEF-'),
    ('[ABC-DEF-?,X]',  'ABC-DEF-?'),
    ('[ABC-DEF-??,X]', 'ABC-DEF-??'),
    ('[ABC-DEF-G,X]',  'ABC-DEF-G'),
    ('[ABC-DEF-GH,X]', 'ABC-DEF-GH'),

    # Negatives
    ('[ABC]', None),
    ('[ABC-DEF]', None),
    ('[ABC-DEF-123]', None),
    ('[ABC-DEF-123,]', None),
    ('[ SRD-RCN-art-09-796]', None),
    ('[ SRD-RCN-123,2wf', None),
    ('[ SRD-RCN-123,2wf]abc', None),
    ('[ SRD-RCN-123,2wf] abc', None),
    ('[ABC-DEF-123,X]\nLine2\nLine3', None),
    ('Line1\n[ABC-DEF-123,X]\nLine3', None),
])

def test_get_requirement_id_fuzzy(req_text, req_id):
    r = get_requirement_id(req_text, fuzzy=True)
    assert r == req_id