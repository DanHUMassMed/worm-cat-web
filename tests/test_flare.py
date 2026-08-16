from utils.data_2_flare_json import getChildrenFor, getChildrenFor2


def test_get_children_for():
    root = {"name": "rgs", "children": []}
    child_list = getChildrenFor("Category1", root)
    assert isinstance(child_list, list)
    assert len(root["children"]) == 1
    assert root["children"][0]["name"] == "Category1"

    # Fetch existing
    child_list_again = getChildrenFor("Category1", root)
    assert child_list_again is child_list
    assert len(root["children"]) == 1


def test_get_children_for2():
    root = {"name": "rgs", "children": []}
    sub_child_list = getChildrenFor2("Cat1", "Cat2", root)
    assert isinstance(sub_child_list, list)
    assert len(root["children"]) == 1
    assert root["children"][0]["name"] == "Cat1"
    assert len(root["children"][0]["children"]) == 1
    assert root["children"][0]["children"][0]["name"] == "Cat2"
