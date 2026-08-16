import json
import logging
import os
import pandas as pd

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DYNAMIC_DIR: str = os.getenv('DYNAMIC_DIR', './static/dynamic')


def read_rgs_and_categories(file_nm_in):
    nodes_dict = {}
    try:
        df = pd.read_csv(file_nm_in)
        node1_list = []
        nodes_dict = {"name": "rgs", "children": node1_list}

        cat3 = df.groupby(["Category.3"]).count()

        cat3_dict = {}
        for cat3_index, row in cat3.iterrows():
            count = int(row['Wormbase.ID'])
            cat3_dict[cat3_index] = count

        for key in cat3_dict:
            components = key.split(':')
            size = int(cat3_dict[key])
            if len(components) == 1:
                node1_list.append({"name": components[0].strip(), "size": size})
            elif len(components) == 2:
                node_list = getChildrenFor(components[0].strip(), nodes_dict)
                node_list.append({"name": components[1].strip(), "size": size})
            else:
                node_list = getChildrenFor2(components[0].strip(), components[1].strip(), nodes_dict)
                node_list.append({"name": components[2].strip(), "size": size})
    except Exception as e:
        logger.error("Error reading RGS and categories from %s: %s", file_nm_in, e, exc_info=True)
    return nodes_dict


def create_flare(dir_nm: str) -> None:
    file_nm_sunburst_templet = f"{DYNAMIC_DIR}/sunburst.templet"
    file_nm_sunburst_html = f"{DYNAMIC_DIR}/{dir_nm}/sunburst.html"
    file_nm_rgs_and_categories = f"{DYNAMIC_DIR}/{dir_nm}/rgs_and_categories.csv"
    with open(file_nm_sunburst_templet, "r") as file:
        data = file.readlines()

    with open(file_nm_sunburst_html, "w") as file:
        for d in data:
            file.write(d)
            if "insert json here" in d:
                json_data = json.dumps(read_rgs_and_categories(file_nm_rgs_and_categories))
                json_var = "var json_data = {}".format(json_data)
                file.write(json_var)



def getChildrenFor(parent, nodes_dict):
    children = nodes_dict['children']
    node_list = None
    for key in children:
        if parent == key['name']:
            if 'children' in key:
                node_list = key['children']
            break

    if node_list is None:
        node_list = []
        children.append({"name":parent, "children":node_list})
    return node_list


def getChildrenFor2(grand_parent, parent, nodes_dict):
    children = getChildrenFor(grand_parent, nodes_dict)
    node_list = None
    for key in children:
        if parent == key['name']:
            if 'children' in key:
                node_list = key['children']
            break

    if node_list is None:
        node_list = []
        children.append({"name":parent, "children":node_list})

    return node_list



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    logger.info("Starting flare generation in %s", os.getcwd())
    create_flare('RGS_Feb-14-2020-11_45_54')
