##############################################################################
#
# Module: data_sync.py
#
# Description:
#     Utility module for converting Excel (.xlsx) files to CSV (.csv) format.
#     Used in data recovery and synchronization workflows where IoT data
#     from different sources is processed in CSV format.
#
# Functionality:
#     - Validates file extension
#     - Reads Excel file using pandas
#     - Exports the content to a CSV file
#
# Author:
#     Vinay N, MCCI Corporation, June 2025
#
# Revision History:
#     V1.0.0  Mon June 2025  Vinay N
#         Initial version with Excel-to-CSV conversion utility
#
##############################################################################
# data_recovery_sync/data_sync.py

import pandas as pd
import os

def convert_excel_to_csv(excel_path):
    """
    Convert an Excel file to CSV format.
    """
    if not excel_path.endswith('.xlsx'):
        raise ValueError(f"Unsupported file format: {excel_path}")
    
    try:
        df = pd.read_excel(excel_path)
        csv_path = excel_path.replace('.xlsx', '.csv')
        df.to_csv(csv_path, index=False)
        print(f"[✓] Converted: {excel_path} → {csv_path}")
        return csv_path
    except Exception as e:
        print(f"[X] Error converting {excel_path}: {e}")
        return None
