import xml.etree.ElementTree as ET

from scripts import nu_three_way_review as review


def test_drawings_share_body_and_changes_are_only_entry():
    rows,_=review.drawings()
    assert len(rows)==3
    assert rows[1][:-2]==rows[2][:-2]
    assert rows[1][-1]==rows[2][-1]
    assert rows[1][-2]!=rows[2][-2]


def test_complete_common_frame_and_labels():
    rows,_=review.drawings()
    left,top,right,bottom=review.renderer.frame(rows)
    for drawing in rows:
        for piece in drawing:
            for polygon in piece['polygons']:
                assert all(left<point[0]<right and top<-point[1]<bottom for point in polygon)
    document=ET.fromstring(review.board(rows,review.LABELS))
    panels=document.findall('{http://www.w3.org/2000/svg}svg')
    assert len(panels)==3
    assert len({panel.attrib['viewBox'] for panel in panels})==1


def test_no_physical_or_fitting_permission():
    approval=review.approval_record()
    assert not approval['new_geometry'] and not approval['fitting'] and not approval['mu']
    assert approval['retries']==approval['physical_runs']==0
