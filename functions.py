import platform
import logging
import glob
import os
import pandas as pd
from os.path import exists

from datetime import datetime
import pytz
from pytz import timezone
from configparser import ConfigParser


def setup_func(logger_hndl=None):
    # Get credentials

    invoice_path, base_price_dir, Output_Dir  = import_credentials(log_hndl=logger_hndl)
    logger_hndl.info("Established Working Directories.")

    return invoice_path, base_price_dir, Output_Dir

def import_credentials(log_hndl=None):
    system = platform.system()
    config = ConfigParser()
    currWorkingDirectory = os.getcwd()
    log_hndl.info("Working from default directory %s ", currWorkingDirectory)
    if exists('./config/config.ini') :
        config_str = config.read(r'./config/config.ini')
        log_hndl.info("Reading ./config/config.ini file ")
    else :
        log_hndl.info("No ./config/config.ini file found in %s", currWorkingDirectory)
        exit(-1)

    if config.has_option('main', 'input_invoices_path') :
        invoice_path = config.get('main', 'input_invoices_path')
    else:
        log_hndl.info("No invoice path found in config.ini file")
        exit(-1)

    if config.has_option('main', 'Base_Prices') :
        base_price_dir = config.get('main', 'Base_Prices')
    else:
        base_price_dir = ''
    if config.has_option('main', 'Output_Directory'):
        Output_Dir = config.get('main', 'Output_Directory')
    else:
        Output_Dir = ''


    return invoice_path, base_price_dir, Output_Dir