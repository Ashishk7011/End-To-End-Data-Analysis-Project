import pandas as pd
from sqlalchemy import create_engine
import os
import time
from logger import get_logger

logging = get_logger(__name__, 'ingestion_db.log')

engine= create_engine('sqlite:///inventory.db')

def ingest_db(df, table_name, engine):
    # this function will convert pandas dataframes into database table
    logging.info(f'Ingesting {table_name} table into Database')
    df.to_sql(table_name, con= engine, if_exists= 'replace', 
              index= False
              )
    logging.info(f'{table_name} table ingested successfully in Database')

def load_raw_data():
    # this function will load csv as dataframe and ingest data into database
    start= time.time()
    for file in os.listdir('data'):
        if '.csv' in file:
            df = pd.read_csv('data/'+file, engine='python', on_bad_lines='warn')
            logging.info(f'ingesting {file} in Database')
            ingest_db(df, file[:-4], engine)
    end= time.time()
    total_time= (end-start)/60
    logging.info('-'*10+'ingestion complete'+'-'*10)
    logging.info(f'Total time taken in {total_time} minutes.')

if __name__ == '__main__':
    load_raw_data()