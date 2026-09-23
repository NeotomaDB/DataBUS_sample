from datetime import datetime
import json
import os

import psycopg2
from dotenv import load_dotenv

import DataBUS.neotomaHelpers as nh
import DataBUS.vocabUploader as vu

"""Example script to push new taxa into ndb.taxa table

The script should be run twice, once with the --upload flag set to False to generate a new csv with all new taxa.
A second time with the --upload flag set to True to upload the new taxa to the database. This is necessary because the taxon validation step needs to check for duplicates in the database, so the new taxa need to be generated and validated before they can be uploaded.

Run with uv
Example usage:
    uv run taxa_upload-example.py --template='data/chiro/template.yml' --data='data/chiro/list_v2.csv' --upload False
    uv run taxa_upload-example.py --template='data/chiro/template.yml' --data='data/chiro/list_v2.csv' --upload True
"""

args = nh.parse_arguments()
load_dotenv()
connection = json.loads(os.getenv("PGDB_LOCAL"))

# Load YAML template and CSV/XLSX file
yml_dict = nh.template_to_dict(temp_file=args["template"])
if args["data"].endswith(".xlsx"):
    csv_file = nh.read_xlsx(args["data"])
else:
    csv_file = nh.read_csv(args["data"])

# Connect to the PostgreSQL database using psycopg2
conn = psycopg2.connect(**connection, connect_timeout=5)
cur = conn.cursor()

logfile = []
start_time = datetime.now()

msg = f"Start reading csv file at {start_time.strftime('%Y-%m-%d %H:%M:%S')}"
logfile.append(msg)
try:
    new_taxa = vu.vocab_uploader(cur,conn, yml_dict, csv_file, "ndb.taxa", upload=args['upload'], logfile=logfile)
    with open("data/chiro/taxa.valid.log", "w", encoding="utf-8") as writer:
        for i in logfile:
            writer.write(i)
            writer.write("\n")
    if new_taxa:
        nh.write_csv(new_taxa, "data/chiro/new_taxa.csv")
except Exception as e:
    print(f"An error occurred: {e}")

msg = f"Finished processing at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. Total time: {datetime.now() - start_time}"
logfile.append(msg)