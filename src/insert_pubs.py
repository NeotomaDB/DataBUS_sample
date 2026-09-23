import json
import os
import psycopg2
from dotenv import load_dotenv
import pandas as pd
import math

load_dotenv()
data = json.loads(os.getenv('PGDB_TANK'))

conn = psycopg2.connect(**data, connect_timeout = 5)
cur = conn.cursor()

data = pd.read_csv('missing_publications.csv')
data = data.rename(columns=lambda x: x.strip().lower())


query = """SELECT ts.insertpublication(_pubtypeid := %(pubtypeid)s,
                                       _year := %(year)s,
                                       _citation := %(citation)s,
                                       _title := %(title)s,
                                       _journal := %(journal)s,
                                       _vol := %(vol)s,
                                       _issue := %(issue)s,
                                       _pages := %(pages)s,
                                       _citnumber := %(citnumber)s,
                                       _doi := %(doi)s,
                                       _booktitle := %(booktitle)s,
                                       _numvol := %(numvol)s,
                                       _edition := %(edition)s,
                                       _voltitle := %(voltitle)s,
                                       _sertitle := %(sertitle)s,
                                       _servol := %(servol)s,
                                       _publisher := %(publisher)s,
                                       _url := %(url)s,
                                       _city := %(city)s,
                                       _state := %(state)s,
                                       _country := %(country)s,
                                       _origlang := %(origlang)s,
                                       _notes := %(notes)s)
                                       """

search_query = """SELECT publicationid FROM ndb.publications
                  WHERE citation = %(citation)s"""

search_id = """SELECT pubtypeid FROM ndb.publicationtypes
               WHERE LOWER(pubtype) = %(pubtype)s"""
for index, row in data.iterrows():
    cur.execute(search_query, {'citation': row['citation']})
    result = cur.fetchone()
    if result is None:
        if isinstance(row['pubtypeid'], str):
            cur.execute(search_id, {'pubtype': row['pubtypeid'].lower().strip()})
            pubtypeid = cur.fetchone()
            if pubtypeid:
                pubtypeid = int(pubtypeid[0])
            else:
                print(f"Publication type not found: {row['pubtypeid']}")
                continue
        elif isinstance(row['pubtypeid'], float) and math.isnan(row['pubtypeid']):
            pubtypeid = None
        row['pubtypeid'] = pubtypeid
        
        if isinstance(row['year'], float) and  not math.isnan(row['year']):
            row['year'] = str(int(row['year']))
        row['vol'] = str(int(row['vol'])) if not pd.isna(row['vol']) else None
        row['issue'] = str(int(row['issue'])) if not pd.isna(row['issue']) else None
        record = row.to_dict()
        record = {k: (None if isinstance(v, float) and math.isnan(v) else v)
                for k, v in record.items()}
        try:
            cur.execute(query, record)
            conn.commit()
            #conn.rollback()
            print(f"Inserted: {record['citation']}")
        except Exception as e:
            conn.rollback()
            continue
    else:
        print(f"Exists: {row['citation']}")