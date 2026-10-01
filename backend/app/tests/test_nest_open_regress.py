from app.services.nest_open_view import open_first_only

def test_detail_truncates_to_first_box():
    raw = {"boxes": [{"paper_m2": 0.1, "box_surface": 0.1}, {"paper_m2": 0.2, "box_surface": 0.2}], "total_paper_m2": 0.3}
    out = open_first_only(raw, view="detail")
    assert len(out["boxes"]) == 1
    assert out["total_paper_m2"] == 0.1
    assert out.get("list_total_paper_m2") == 0.3
