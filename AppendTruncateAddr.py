import os
from dotenv import load_dotenv
from dotenv import dotenv_values
env="\\\\APNSDS4\Projects\MontCo_E911\Scripts\SDE_ScriptRPC\.env"
print(env)
load_dotenv(dotenv_path=env,verbose=True)
#print("dotenv_values:", dotenv_values("C:/Python/testingArcpy/SDE_ScriptRPC/.env"))
from datetime import datetime
import csv
LOG_FILE = r'\\APNSDS4\Projects\MontCo_E911\Scripts\automation_status.csv'

# Check if paths exist
def check_path_exists(path, path_name="Path"):
    """Print whether a path exists"""
    if os.path.exists(path):
        print(f"✓ {path_name} exists: {path}")
        return True
    else:
        print(f"✗ {path_name} does NOT exist: {path}")
        return False

if not check_path_exists(env, ".env file"):
    print ("EXITING NOW\n\nGOODBYE :'(")
    exit(1)

import arcpy
errorlogname = os.getenv("ERROR_LOG_NAME")
prod_egdb    = os.getenv("PROD_EGDB")
ProdFeatureClass1 = os.getenv("PROD_FEATURE_CLASS_1")
local_fgdb   = os.getenv("LOCAL_FGDB")
StageFeatureClass = os.getenv("STAGE_FEATURE_CLASS")
xl_Templet   = os.getenv("XL_TEMPLET")#NOT BEING USED
monthly_gdb  = os.getenv("MONTHLY_GDB")#NOT BEING USED
monthly_fc   = os.getenv("MONTHLY_FC")#NOT BEING USED
safe_fgdb    = os.getenv("SAFE_FGDB")
df=xl_Templet
fieldName = "label"

##Define Functions
def logError(e):
    """
    Function to log errors to a specified log file.

    Parameters
    ----------
    e : Exception
        The exception to log.

    Returns
    -------
    None
    """
    if not os.path.exists(errorlogname):
        with open(errorlogname, 'w') as logFile:
            logFile.write('Error Log\n')
            logFile.write('=========\n')
    with open(errorlogname, 'a') as logFile:
        logFile.write('\n')
        logFile.write('Error: {}\n'.format(e))


def tableRowCounts(gdb, table_name, field_name):
    """
    Function is to return the numbers and types in a specified DB field

    Parameters
    ----------
    gdb : raw string
        gdb connection
    table_name : str
        name of table or in this case feature class
    field_name : str
        name of field to search

    Returns
    -------
    list
        field types and counts
     """
    try:
        gdb_conn = arcpy.ArcSDESQLExecute(gdb)

        sql = '''
        SELECT {0}, COUNT({0}) AS f_count FROM {1}
        GROUP BY {0}
        ORDER BY f_count DESC
        '''.format(field_name, table_name)
        rowCount = []
        gdb_return = gdb_conn.execute(sql)
        for i in gdb_return:
            print('{}: {}'.format(*i))
            rowCount.append('{}: {}'.format(*i))
        return rowCount
    except Exception as e:
        success='F'
        logError(e)


def TruncOrTreat(prod_egdb, prod_table_name):
    """_summary_

    Args:
        prod_egdb (str): production enterprise geodatabase 
        prod_table_name (str): name of the feature class i.e. "cmc_updates.sde.AddressPoints"

    Returns:
        bool: if the table has more than one row it will return true so that later on, it will truncate the table. If it returns false, it will skip the truncate process.
    """
    prod = os.path.join(prod_egdb, prod_table_name)
    try:
        # Get the count of rows in the table
        result = arcpy.GetCount_management(prod)
        count = int(result.getOutput(0))
        
        # Return True if count is greater than 1, otherwise False
        return count > 1
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    
def attempt_disconnect(sde_connection_file, max_retries):
    """
    Function to attempt disconnecting users from an SDE database.
    
    Parameters
    ----------
    sde_connection_file : str
        Path to the SDE connection file (.sde).
    max_retries : int
        Number of times to retry disconnecting if it fails.
    
    Returns
    -------
    bool
        True if disconnecting was successful, False otherwise.
    """
    attempts = 0

    while attempts < max_retries:
        try:
            # Attempt to disconnect all users
            arcpy.DisconnectUser(sde_connection_file, "ALL")
            print("Disconnect: T")
            return True  # Return True if disconnect was successful
        except Exception as e:
            attempts += 1
            print(f'Attempt {attempts}: Disconnect: F')
            print(f"Error: {e}")
            if attempts < max_retries:
                print('Retrying...')
    
    return False  # Return False if all attempts fail

def attempt_truncate(table_path, max_retries):
    """
    Function to attempt truncating a table.
    
    Parameters
    ----------
    table_path : str
        Path to the table to be truncated.
    max_retries : int
        Number of times to retry truncating if it fails.
    
    Returns
    -------
    bool
        True if truncating was successful, False otherwise.
    """
    attempts = 0

    while attempts < max_retries:
        try:
            # Attempt to truncate the table
            arcpy.TruncateTable_management(table_path)
            print('Truncate: T')
            return True  # Return True if truncation was successful
        except Exception as e:
            attempts += 1
            print(f'Attempt {attempts}: Truncate: F')
            print(f"Error: {e}")
            if attempts < max_retries:
                print('Retrying...')
    
    return False  # Return False if all attempts fail

def attempt_append(stage_table, prod_table, max_retries):
    """
    Function to attempt appending data to a table.
    
    Parameters
    ----------
    stage_table : str
        Path to the staging table.
    prod_table : str
        Path to the production table.
    max_retries : int
        Number of times to retry appending if it fails.
    
    Returns
    -------
    bool
        True if appending was successful, False otherwise.
    """
    attempts = 0

    while attempts < max_retries:
        try:
            # Attempt to append the data
            arcpy.management.Append(stage_table, prod_table, "NO_TEST")
            print('Append: T')
            return True  # Return True if append was successful
        except Exception as e:
            attempts += 1
            print(f'Attempt {attempts}: Append: F')
            print(f"Error: {e}")
            if attempts < max_retries:
                print('Retrying...')
    
    return False  # Return False if all attempts fail


def copy_geodatabase(source_gdb, destination_gdb):
    """
    Copy a file or enterprise geodatabase to a destination path, replacing any
    existing geodatabase at that location.

    Parameters
    ----------
    source_gdb : str
        Path to the geodatabase to copy.
    destination_gdb : str
        Path where the copied geodatabase should be written.

    Returns
    -------
    bool
        True when the copy succeeds; False otherwise.
    """
    try:
        if not arcpy.Exists(source_gdb):
            raise FileNotFoundError(f"Source geodatabase not found: {source_gdb}")

        dest_parent = os.path.dirname(destination_gdb)
        if dest_parent and not os.path.exists(dest_parent):
            os.makedirs(dest_parent, exist_ok=True)

        if arcpy.Exists(destination_gdb):
            print(f"Removing existing geodatabase at {destination_gdb}")
            arcpy.management.Delete(destination_gdb)

        print(f"Copying {source_gdb} -> {destination_gdb}")
        arcpy.management.Copy(source_gdb, destination_gdb)
        print("Geodatabase copy completed.")
        return True
    except Exception as e:
        logError(e)
        print(f"Failed to copy geodatabase: {e}")
        return False

def appendTruncate(stage_gdb, prod_gdb, stage_table_name, prod_table_name, max_retries, truncate):
    """
    Function to perform disconnect, truncate (if needed), and append operations with retry logic.
    
    Parameters
    ----------
    stage_gdb : str
        ArcGIS Pro staging workspace.
    prod_gdb : str
        ArcGIS Pro production workspace.
    stage_table_name : str
        Name of the staging table.
    prod_table_name : str
        Name of the production table.
    max_retries : int
        Number of times to retry each operation if it fails.
    truncate : bool
        Whether to truncate the production table before appending.
    
    Returns
    -------
    None
    """
    prod = os.path.join(prod_gdb, prod_table_name)
    stage = os.path.join(stage_gdb, stage_table_name)
    
    # Attempt to disconnect users
    if attempt_disconnect(prod_gdb, max_retries):
        # Optionally truncate the table
        if not truncate or attempt_truncate(prod, max_retries):
            # Attempt to append the data
            if not attempt_append(stage, prod, max_retries):
                print("Failed to append data after several attempts.")
        else:
            print("Failed to truncate the production table after several attempts.")
    else:
        print("Failed to disconnect users after several attempts.")

def log_script_status(script_name, status):
    """
    Appends execution status to a shared CSV.
    Creates the file with headers if it doesn't exist.
    """
    fieldnames = ['date', 'script_name', 'status']
    today = datetime.now().strftime('%Y-%m-%d')
    
    file_exists = os.path.isfile(LOG_FILE)
    
    try:
        # Use 'a' for append mode. 
        with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                'date': today,
                'script_name': script_name,
                'status': status.upper()
            })
    except Exception as e:
        print(f"Failed to log status for {script_name}: {e}")


if __name__ == "__main__":
    try:
        appendTruncate(local_fgdb, prod_egdb, StageFeatureClass, ProdFeatureClass1, 7, TruncOrTreat(prod_egdb, ProdFeatureClass1))
        copy_geodatabase(local_fgdb, safe_fgdb)
        # ...
        log_script_status("nightly_import", "PASS")
    except Exception as e:
        log_script_status("nightly_import", "FAIL")
        print(f"Script failed: {e}")
#execute the functions
