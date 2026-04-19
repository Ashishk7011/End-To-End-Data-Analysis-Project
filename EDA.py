import pandas as pd
import sqlite3
import numpy as np

from sqlalchemy import create_engine
from logger import get_logger
from ingestion_db import ingest_db

logging = get_logger(__name__, 'vendor_sales_summary.log')

engine= create_engine('sqlite:///inventory.db')

def create_vendor_sales_summary_table(conn):
    import time
    start = time.time()
    vendor_sales_summary= pd.read_sql_query('''with FreightSummary AS (
    SELECT
    VendorNumber,
    SUM(Freight) AS FreightCost
    FROM vendor_invoice
    GROUP BY VendorNumber
    ),
    PurchaseSummary AS (
    SELECT
    p.VendorNumber,
    p.VendorName,
    p.Brand,
    p.Description,
    p.PurchasePrice,
    pp.Price AS ActualPrice,
    pp.Volume,
    SUM(p.Quantity) AS TotalPurchaseQuantity,
    SUM(p.Dollars) AS TotalPurchaseDollars
    FROM purchases p
    JOIN purchase_prices pp
    ON p.Brand= pp.Brand
    WHERE p.PurchasePrice > 0
    GROUP BY p.VendorNumber, p.VendorName, p.Brand, p.Description, p.PurchasePrice, pp.Price, pp.Volume
    ),
    SalesSummary AS (
    SELECT
    VendorNo,
    Brand,
    sum(SalesQuantity) AS TotalSalesQuantity,
    sum(SalesDollars) AS TotalSalesDollars,
    sum(SalesPrice) AS TotalSalesPrice,
    sum(ExciseTax) AS TotalExciseTax    
    from sales
    group by VendorNo, Brand)

    SELECT
    ps.VendorNumber,
    ps.VendorName,
    ps.Brand,
    ps.Description,
    ps.PurchasePrice,
    ps.ActualPrice,
    ps.Volume,
    ps.TotalPurchaseQuantity,
    ps.TotalPurchaseDollars,
    ss.TotalSalesQuantity,
    ss.TotalSalesDollars,
    ss.TotalSalesPrice,
    ss.TotalExciseTax,
    fs.FreightCost
    FROM PurchaseSummary ps
    LEFT JOIN SalesSummary ss
    ON ps.VendorNumber = ss.VendorNo AND ps.Brand = ss.Brand
    LEFT JOIN FreightSummary fs
    ON ps.VendorNumber = fs.VendorNumber
    ORDER BY ps.TotalPurchaseDollars DESC''', conn
    )
    end = time.time()
    print('Execution time:', (end - start)/60, 'minutes')

    return vendor_sales_summary

def clean_vendor_sales_summary(vendor_sales_summary):

    vendor_sales_summary.fillna(0, inplace=True)

    vendor_sales_summary['VendorName']= vendor_sales_summary['VendorName'].str.strip()

    vendor_sales_summary['Description']= vendor_sales_summary['Description'].str.strip()

    vendor_sales_summary['Volume']= vendor_sales_summary['Volume'].astype('float64')

    vendor_sales_summary['GrossProfit'] = vendor_sales_summary['TotalSalesDollars'] - vendor_sales_summary['TotalPurchaseDollars']

    vendor_sales_summary['ProfitMargin'] = np.where(vendor_sales_summary['TotalSalesDollars'] == 0, np.nan,
                    (vendor_sales_summary['GrossProfit'] / vendor_sales_summary['TotalSalesDollars']) * 100)

    vendor_sales_summary['StockTurnover'] = vendor_sales_summary['TotalSalesQuantity'] / vendor_sales_summary['TotalPurchaseQuantity']

    vendor_sales_summary['SalesToPurchaseRatio'] = vendor_sales_summary['TotalSalesDollars'] / vendor_sales_summary['TotalPurchaseDollars']

    return vendor_sales_summary

import sqlite3

if __name__ == '__main__':

    try:
        # Step 1: Connect to DB
        conn = sqlite3.connect('inventory.db')
        logging.info('Connection to database established')

        # Step 2: Create summary table
        logging.info('Creating vendor_sales_summary table in Database')
        summary_df = create_vendor_sales_summary_table(conn)
        logging.info(f'vendor_sales_summary table created successfully\n{summary_df.head()}')

        # Step 3: Clean data
        logging.info('Cleaning vendor_sales_summary table')
        clean_summary_df = clean_vendor_sales_summary(summary_df)
        logging.info(f'vendor_sales_summary table cleaned successfully\n{clean_summary_df.head()}')

        # Step 4: Ingest into DB
        logging.info('Ingesting cleaned vendor_sales_summary table into Database')
        ingest_db(clean_summary_df, 'vendor_sales_summary', engine)
        logging.info('vendor_sales_summary table ingested successfully in Database')

    except Exception as e:
        logging.error(f'Error occurred: {e}', exc_info=True)

    finally:
        if conn:
            conn.close()
            logging.info('Database connection closed')