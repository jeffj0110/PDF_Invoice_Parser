import platform
import logging
import glob
import os
import pandas as pd
from os.path import exists

from datetime import datetime
def Get_Base_Prices(CWD, base_price_dir, logger) :
    PrcCount = 0

    logger.info("Imported %s prices", str(PrcCount))

    return PrcCount