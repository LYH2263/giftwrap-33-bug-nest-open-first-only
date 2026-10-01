from app.engines.wrap_math import paper_area
def test_overlap_one():
    assert paper_area(1,1,1,1.0)["paper_m2"] == 6.0
