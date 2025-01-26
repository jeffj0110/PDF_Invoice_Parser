import sys, getopt, os
import glob
import pandas as pd
import pathlib

import m_logger
import pdfplumber

def PDF_MultipleFiles(Inv_Directory, logger):

    # Change to working directory
    os.chdir(Inv_Directory)
    base_directory = pathlib.Path.cwd()

    file_list = glob.glob('*.pdf', )
    file_list.sort()
    # Need to change to the config files specified location of the PDF Files
    file_counter = 0
    InvPrc_Frame = pd.DataFrame(columns = ['Invoice_Date','Invoice', 'Qty', 'Product_Code','Description', 'Qty_shipped', 'Price', 'Per', 'Unit_Prc', 'Total_Cost' ])
    InvPrc_Frame_Updated = pd.DataFrame(columns = ['Invoice_Date','Invoice', 'Qty', 'Product_Code','Description', 'Qty_shipped', 'Price', 'Per', 'Unit_Prc', 'Total_Cost'])
    Prc_Counter = 0
    for pdffile in file_list:
        logger.info(pdffile)
        Inv_Number = ''
        Inv_Date = ''
        with pdfplumber.open(pdffile) as pdf:
            try :
                pg_cnt = 0
                for page in pdf.pages:
                    pg_cnt += 1
                    tables = page.extract_tables()
                    Inv_Number, Inv_Date = Get_Inv_Num_Date(tables, logger)
                    if Inv_Number != '':
                        for table in tables:
                            if len(table) > 4:
                                if table[0] != None :
                                    row_list = table[0]
                                    if len(row_list) > 6:
                                        # lists of products and prices follow the ACCOUNT header
                                        if 'ACCOUNT' in row_list[0]:
                                            InvPrc_Frame_Updated, Parsed_Prices = Get_Prices(table, Inv_Number, Inv_Date, InvPrc_Frame)
                                            Prc_Counter = Prc_Counter + Parsed_Prices
                                            InvPrc_Frame = InvPrc_Frame_Updated

                file_counter += 1
            except Exception as e:
                print("Exception Occurred : ", e)
                logger.info("Invalid PDF File %s", pdffile)

    Stat_Update, All_Time_Values = Price_Change_Summary(InvPrc_Frame)

    return file_counter, Stat_Update, Prc_Counter, All_Time_Values

def Get_Inv_Num_Date(tables, logger) :
    Inv_Num = ''
    Inv_Date = ''
    for table in tables :
        if len(table) > 0 :
            if len(table[0]) > 0 :
                table_row = table[0]
                if len(table_row) > 0 :
                    #row_list = table_list[0]
                    if 'INVOICE NO.' in table_row[0] :
                        row_list = table[1]
                        Inv_Num = row_list[0]
                        Inv_Date = row_list[1]
                        logger.info('Invoice Number: ' + Inv_Num + ' Date: ' + Inv_Date )
                        break

    if Inv_Num == '' :
        logger.info('No Inv Number Found')

    return Inv_Num, Inv_Date

def Get_Prices(input_table, Inv_Number, Inv_Date, InvPrc_Frame) :
    # extracted input_table is from the invoice

    #if Inv_Date == '07/29/2024' :
    #    print("Problem Invoice")
    OrderedFound = False
    #Input Table is a list of products on the invoice
    # 00 = Qty Ordered
    # 01 = Product Code
    # 02 = Description
    # 08 = Qty Shipped
    # 11 = Price
    # 12 = Price Per (E=Each, C = 100, M=1000)
    # 14 = Total Cost

    # Check for the table that contains prices in the invoice
    Prc_Count = 0
    for row in input_table :
        if len(row) > 6:
            # lists of products and prices follow the Qty Ordered header
            if OrderedFound :
                if (row[0] != '') and (row[0] != None) and  ('TITLE TO MERCHANDISE' not in row[0]) :
                    qty = int(row[0])
                    product_code = row[1]
                    description = row[2]
                    qtr_shipped = int(row[8])
                    if (len(row) == 15) and is_float_digit(row[10]) :
                        price = float(row[10])
                        price_per = row[11]
                        total_cost = float(row[13])
                    else:
                        price = float(row[11])
                        price_per = row[12]
                        total_cost = float(row[14])


                    match price_per :
                        case 'E' :
                            unit_price = price
                        case 'C' :
                            unit_price = price / 100
                        case 'M' :
                            unit_price = price / 1000
                        case _:
                            unit_price = price

                    new_df_row = [Inv_Date, Inv_Number, qty, product_code, description, qtr_shipped, price, price_per, unit_price, total_cost]
                    InvPrc_Frame.loc[len(InvPrc_Frame)] = new_df_row
                    Prc_Count += 1
            elif 'ORDERED' in row[0]:
                OrderedFound = True
            else :
                continue

    return InvPrc_Frame, Prc_Count

def is_float_digit(n: str) -> bool:
     try:
         float(n)
         return True
     except ValueError:
         return False

#columns = ['Invoice_Date','Invoice', 'Qty', 'Product_Code','Description', 'Qty_shipped', 'Price', 'Per', 'Unit_Prc', 'Total_Cost' ])
def Price_Change_Summary(df) :
    # Convert string dates to Date Values
    df['Invoice_Date'] = pd.to_datetime(df['Invoice_Date']).dt.date
    df.sort_values(by=['Product_Code','Invoice_Date'], ascending=[True, True],ignore_index=True, inplace=True)

    # Calc Percentage Changes Since Last Invoice And All Time
    per_of_change_latest = []
    per_of_change_alltime = []
    total_cost_alltime = []
    count = 0
    prev_pc = next_pc = ''
    while count < len(df) :
        if count == 0 :
            per_of_change_latest.append(0)
            per_of_change_alltime.append(0)
            total_cost_alltime.append(df['Total_Cost'][count])
            product_all_time_index = 0
            prev_pc = next_pc = df['Product_Code'][count]
        else:
            prev_pc = next_pc
            next_pc = df['Product_Code'][count]
            if next_pc == prev_pc :
                total_cost_alltime.append(df['Total_Cost'][count] + total_cost_alltime[-1])
                if df['Unit_Prc'][count-1] != 0 :
                    per_of_change_latest.append(round(((df['Unit_Prc'][count]-df['Unit_Prc'][count-1])/df['Unit_Prc'][count-1])*100,3))
                else :
                    per_of_change_latest.append(0)

                if df['Unit_Prc'][product_all_time_index] != 0 :
                    per_of_change_alltime.append(round(((df['Unit_Prc'][count]-df['Unit_Prc'][product_all_time_index])/df['Unit_Prc'][product_all_time_index])*100,3))
                else :
                    per_of_change_alltime.append(0)
            else :
                product_all_time_index = count
                per_of_change_latest.append(0)
                per_of_change_alltime.append(0)
                total_cost_alltime.append(df['Total_Cost'][count])

        count += 1

    df['Latest_Chg'] = pd.Series(per_of_change_latest).values
    df['All_Time_Chg'] = pd.Series(per_of_change_alltime).values
    df['TC_Alltime'] = pd.Series(total_cost_alltime).values

    result_df = df[['Product_Code', 'Description', 'Invoice_Date', 'Unit_Prc', 'Latest_Chg', 'All_Time_Chg',  'Qty_shipped', 'Price', 'Per', 'Invoice', 'Total_Cost', 'TC_Alltime']]
    return_df = result_df.sort_values(by=['Product_Code','Invoice_Date', 'Latest_Chg'], ascending=[True, True, False], ignore_index=True)
    # Sort by all time cost per product and then just save the row with the highest total cost for each product
    all_time_df = result_df.sort_values(by=['Product_Code','TC_Alltime'], ascending=[True, False], ignore_index=True)
    all_time_df.drop_duplicates(subset=['Product_Code'], keep='first', inplace=True)
    all_time_df.sort_values(by=['TC_Alltime'], ascending=[False], inplace=True, ignore_index=True)
    # get rid of the columns which are not pertinent to all time spend per product
    all_time_df.drop(['Invoice_Date', 'Unit_Prc', 'Latest_Chg',  'Qty_shipped', 'Invoice', 'Total_Cost'], axis=1, inplace=True)
    return return_df, all_time_df