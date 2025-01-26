
import sys, getopt, os
import glob
import pandas as pd
import pytz
from datetime import datetime

import m_logger

import csv
from os.path import exists
import logging

from GetBasePrice_Info import Get_Base_Prices
from Extract_Data_From_PDF_Tables import Get_Prices, Get_Inv_Num_Date, Price_Change_Summary, PDF_MultipleFiles
from functions import setup_func


# Check to see if this file is being executed as the "Main" python
# script instead of being used as a module by some other python script
# This allows us to use the module which ever way we want.
def main(argv):
   global Prc_Counter
   #inputfile = 'Ticker_CIK_List.csv'
   Prc_Counter = 0
   outputfile = ''
   try:
      opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
   except getopt.GetoptError:
      print('Ref_PrcTracker -c <config file>')
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print('Ref_PrcTracker -c <config file>')
         sys.exit()
      elif opt in ("-c", "-C"):
         inputfile = arg


   # J. Jones
   # Setting up a logging service for the bot to be able to retrieve
   # runtime messages from a log file
   est_tz = pytz.timezone('US/Eastern')
   now = datetime.now(est_tz).strftime("%Y_%m_%d-%H%M%S")
   logfilename = "{}_logfile_{}".format("Amperage", now)
   logfilename = logfilename + ".txt"
   logger = m_logger.getlogger(logfilename)
   file_counter = 0
   invoice_path = ''
   base_price_dir = ''
   Output_Dir = ''

   invoice_path, base_price_dir, Output_Dir = setup_func(logger)

   CWD = os.getcwd()

   Inv_Prc_Counter = 0

   # Read the base price information, if available
   if base_price_dir != '' :
       Prc_Counter = Get_Base_Prices(invoice_path, base_price_dir, logger)
   else :
       logger.info("No base price information found")

   logger.info("Invoice Path : {}".format(invoice_path))
   logger.info("Base Price Dir : {}".format(base_price_dir))
   logger.info("Output Dir : {}".format(Output_Dir))

   if invoice_path != '' :
       file_counter, InvPrc_Frame, Inv_Prc_Counter, Total_Cost_Alltime = PDF_MultipleFiles(invoice_path, logger)
   else :
       logger.info("No invoice directory defined, no invoices processed")


   if file_counter > 0 :
       logger.info("Processed %s Invoices With %s Prices", str(file_counter), str(Inv_Prc_Counter))
       Sheetname = "{}_InvPrices_{}".format("Amperage", now)
       Sheetname = Sheetname + ".xlsx"
       os.makedirs(Output_Dir, exist_ok=True)
       os.chdir(Output_Dir)
       InvPrc_Frame.to_excel(Sheetname)
       Sheetname = "{}_AllTimeSpend_{}".format("Amperage", now)
       Sheetname = Sheetname + ".xlsx"
       Total_Cost_Alltime.to_excel(Sheetname)
   else:
       logger.info("No Invoices Found ")
       return False

   return True

if __name__ == "__main__":
   main(sys.argv[1:])