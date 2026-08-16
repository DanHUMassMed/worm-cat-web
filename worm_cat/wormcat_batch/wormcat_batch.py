import os
import pandas as pd
from wormcat_batch.execute_r import ExecuteR
from wormcat_batch.create_wormcat_xlsx import process_category_files
from datetime import datetime
import logging
import redis
import json

REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_DB = int(os.environ.get('REDIS_DB', 1))

redis_server = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

logger = logging.getLogger(__name__)

def get_wormcat_lib():
    executeR = ExecuteR()
    path = executeR.wormcat_library_path_fun()
    if path:
        first_quote=path.find('"')
        last_quote=path.rfind('"')
        if last_quote == -1:
            logger.warning("WormCat library is not installed or cannot be found.")
        path = path[first_quote+1:last_quote]
    logger.debug("Resolved WormCat library path: %s", path)
    return path

# Call Wormcat once for each sheet (tab) in the spreadsheet
def call_wormcat(name, gene_ids, output_dir, annotation_file, input_type):
    file_nm = "{}.csv".format(name)
    dir_nm = "{}".format(name)
    title = dir_nm.replace('_', ' ')
    gene_ids = gene_ids.to_frame(name=input_type)
    gene_ids.to_csv(file_nm, index=False)
    executeR = ExecuteR()
    executeR.worm_cat_fun(file_nm, dir_nm, title, annotation_file, input_type)


# Process the Input spreadsheet
def process_spreadsheet(xsl_file_nm, output_dir, annotation_file, redis_channel):
    gene_id_all = None
    input_type = None
    xl = pd.ExcelFile(xsl_file_nm)
    current_working_dir = os.getcwd()
    os.chdir(output_dir)

    if redis_channel:
        redis_message = {'name': 'SHEETS', 'value': len(xl.sheet_names)}
        redis_server.lpush(redis_channel, json.dumps(redis_message))

    for sheet in xl.sheet_names:
        logger.info("Processing spreadsheet sheet: %s", sheet)
        df = xl.parse(sheet)
        if 'Wormbase ID' in df.columns:
            gene_id_all = df['Wormbase ID']
            input_type = 'Wormbase.ID'
        elif 'Sequence ID' in df.columns:
            gene_id_all = df['Sequence ID']
            input_type = 'Sequence.ID'
        else:
            logger.error("Sheet '%s' missing required ID column ('Sequence ID' or 'Wormbase ID')", sheet)

        if redis_channel:
            redis_message = {'name': 'MESSAGE', 'value': 'Processing {} data'.format(sheet)}
            redis_server.lpush(redis_channel, json.dumps(redis_message))

        if gene_id_all is None or input_type is None:
            pass
        else:
            call_wormcat(sheet, gene_id_all, output_dir, annotation_file, input_type)

    if redis_channel:
        redis_message = {'name': 'MESSAGE', 'value': 'Compiling Excel category summaries...'}
        redis_server.lpush(redis_channel, json.dumps(redis_message))

    os.chdir(current_working_dir)


def files_to_process(output_dir):
    rows = []
    for dir_nm in os.listdir(output_dir):
        full_dir = os.path.join(output_dir, dir_nm)
        if os.path.isdir(full_dir):
            for cat_num in [1, 2, 3]:
                rgs_fisher = os.path.join(output_dir, dir_nm, f"rgs_fisher_cat{cat_num}.csv")
                cat_nm = f"Cat{cat_num}"
                rows.append({'sheet': cat_nm, 'category': cat_num, 'file': rgs_fisher, 'label': dir_nm})
    return pd.DataFrame(rows, columns=['sheet', 'category', 'file', 'label'])

def cleanup_output_dir(output_dir):
    files = [f for f in os.listdir(output_dir) if os.path.isfile(os.path.join(output_dir, f))]
    for file in files:
        index_of_dot = file.rfind('.')
        extension = file[index_of_dot:]
        if extension in ['.zip', '.csv', '.pdf']:
            os.remove(os.path.join(output_dir, file))

DYNAMIC_DIR: str = os.getenv('DYNAMIC_DIR', './static/dynamic')


def run_wormcat_batch(batch_user, annotation_file, xsl_file_nm,
                      redis_channel=None, suffix=None, output_dir_base=DYNAMIC_DIR):
    wormcat_r_path = get_wormcat_lib()
    extdata_path = "{}{}extdata".format(wormcat_r_path, os.path.sep)

    if not suffix:
        suffix = datetime.now().strftime("%b-%d-%Y-%H_%M_%S")

    batch_user = batch_user.replace(' ','_')
    output_dir = "{}_{}".format(batch_user, suffix)
    output_dir_full_path = "{}{}{}".format(output_dir_base, os.path.sep, output_dir)

    index_of_sep = xsl_file_nm.rfind(os.path.sep)
    xsl_file_nm_dest = "{}{}".format(output_dir_full_path, xsl_file_nm[index_of_sep:])

    try:
        os.mkdir(output_dir_full_path)
        os.rename(xsl_file_nm, xsl_file_nm_dest)
        process_spreadsheet(xsl_file_nm_dest, output_dir_full_path, annotation_file, redis_channel)

        out_xsl_file_nm = "{}{}Out_{}".format(output_dir_full_path, os.path.sep, xsl_file_nm[index_of_sep + 1:])
        annotation_file = "{}{}{}".format(extdata_path, os.path.sep, annotation_file)
        df_process = files_to_process(output_dir_full_path)
        process_category_files(df_process, annotation_file, out_xsl_file_nm)
        cleanup_output_dir(output_dir_full_path)
    except Exception as e:
        logger.exception("Error executing WormCat batch processing: %s", e)
        raise
    return output_dir


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    logger.info("Starting WormCat Batch execution")
    batch_user="Dan Higgins"
    annotation_file = "whole_genome_jul-03-2019.csv"
    xsl_file_nm = "./static/dynamic/Murphy_TS.xlsx"
    run_wormcat_batch(batch_user, annotation_file, xsl_file_nm)


if __name__ == '__main__':
    main()