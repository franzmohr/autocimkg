"""
Tests of the KG models.
"""
import pytest

from autocimkg.models import Entity, Relationship


@pytest.mark.parametrize("label, expected", [
    ("Competence", "Competence"),
    ("Financial Instrument", "Financial_Instrument"),
    ("3D Printing", "_3D_Printing"),  # labels must not start w/ a digit
    ("R&D", "R_D"),
])
def test_entity_labels_are_valid_identifiers(label, expected):
    entity = Entity(label=label, name="Stress-Testing")
    entity.process()
    entity.process()  # idempotent
    assert (entity.label, entity.name) == (expected, "stress testing")


@pytest.mark.parametrize("name, expected", [("knows", "knows"), ("is part of", "is_part_of"),
                                            ("1st author of", "_1st_author_of")])
def test_relationship_names_are_valid_identifiers(name, expected):
    relationship = Relationship(name=name)
    relationship.process()
    relationship.process()  # idempotent
    assert relationship.name == expected
