###############################################################################
# Name: ingest_data.py
# Description: This script fetches the Melbourne Airbnb listing data via API
#              and loads into the bronze layer of the ADLS gen2.
# Author: Travis Hong
# Repository: https://github.com/TravisH0301/azure_airbnb_host_analytics
###############################################################################
import requests
import shutil
import gzip
import yaml
import io

import pandas as pd
from azure.storage.filedatalake import DataLakeServiceClient


# Function to fetch Airbnb data
def fetch_data(url): 
    """This function fetches Airbnb data using
    the given URL, and returns it as a dataframe.
    
    Parameters
    ----------
    url: str
        Airbnb data API URL
        
    Returns
    -------
    df: pandas dataframe
        Fetched dataset
    """
    # Download data file
    response = requests.get(url)

    # Use BytesIO for in-memory file handling
    gzip_file = io.BytesIO(response.content)

    # Unzip file and load into a DataFrame
    with gzip.open(gzip_file, 'rb') as f_in:
        df = pd.read_csv(f_in)

    return df


# Function to create Data Lake directory client
def create_dir_client(
        account_name,
        account_key,
        container_name,
        directory_name
):
    """This function returns the Data Lake directory client.
    
    Parameters
    ----------
    account_name: str
        Azure storage account name
    account_key: str
        Azure storage account key
    container_name: str
        ADLS gen2 container name
    directory_name: str
        ADLS gen2 directory name
    
    Returns
    -------
    object
        Data Lake directory client
    """
    service_client = DataLakeServiceClient(
        account_url=f"https://{account_name}.dfs.core.windows.net",
        credential=account_key
    )

    file_system_client = service_client.get_file_system_client(file_system=container_name)

    return file_system_client.get_directory_client(directory=directory_name)
            

# Function to upload data to ADLS
def upload_file(file, file_name, directory_client):
    """This uploads the given bytes file into the
    ADLS directory.
    
    Parameters
    ----------
    file: bytes
        File to upload in bytes
    file_name: str
        File name
    directory_client: object
        Data Lake directory client
        
    Returns
    -------
    None
    """
    file_client = directory_client.create_file(file_name)
    file_client.upload_data(data=file, overwrite=True) #Either of the lines works
    file_client.flush_data(len(file))


def main():
    # Load Azure storage account credentials
    with open("./src/azure-function/cred.yaml") as f:
        conf = yaml.safe_load(f)
        account_name = conf["account_name"]
        account_key = conf["account_key"]

    # Fetch Airbnb listing dataset via API
    url = 'http://data.insideairbnb.com/australia/vic/melbourne/2023-03-13/data/listings.csv.gz'
    df = fetch_data(url)

    # Create Data Lake directory client
    container_name = "airbnb-host-analytics"
    directory_name = "bronze"
    directory_client = create_dir_client(
        account_name,
        account_key,
        container_name,
        directory_name
    )

    # Upload dataset to ADLS as a parquet file
    file_name = "raw_dataset.parquet"
    parquet_file = df.to_parquet()
    upload_file(parquet_file, file_name, directory_client)


if __name__ == "__main__":
    main()

    

    