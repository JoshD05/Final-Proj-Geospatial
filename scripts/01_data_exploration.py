"""
Data Exploration Script
Purpose: Examine the structure of voter registration data and address datasets
to identify appropriate fields for geocoding.
"""

import geopandas as gpd
import pandas as pd
import os

def explore_voter_data():
    """Examine voter registration data structure"""
    print("=== VOTER REGISTRATION DATA EXPLORATION ===")
    
    # Pitt County voter data
    pitt_voter_dir = "../ncvoterPitt"
    if os.path.exists(pitt_voter_dir):
        print(f"\n--- Pitt County Voter Data ---")
        print(f"Files in {pitt_voter_dir}:")
        for file in os.listdir(pitt_voter_dir):
            print(f"  - {file}")
            if file.endswith('.txt'):
                pitt_voter_path = os.path.join(pitt_voter_dir, file)
                # Read first few lines to understand structure
                with open(pitt_voter_path, 'r') as f:
                    lines = f.readlines()[:5]
                    for i, line in enumerate(lines):
                        print(f"Line {i+1}: {line.strip()}")
                
                # Try to read as tab-delimited
                try:
                    pitt_voters = pd.read_csv(pitt_voter_path, sep='\t', nrows=1000)
                    print(f"\nColumns in Pitt County voter data:")
                    for col in pitt_voters.columns:
                        print(f"  - {col}")
                    print(f"\nData shape: {pitt_voters.shape}")
                    print(f"\nFirst few address-related columns:")
                    address_cols = [col for col in pitt_voters.columns if any(addr in col.lower() for addr in ['addr', 'street', 'zip', 'city'])]
                    for col in address_cols:
                        print(f"  {col}: {pitt_voters[col].iloc[0]}")
                except Exception as e:
                    print(f"Error reading Pitt voter data: {e}")
                break
    
    # Beaufort County voter data
    beaufort_voter_dir = "../ncvoterBeaufort"
    if os.path.exists(beaufort_voter_dir):
        print(f"\n--- Beaufort County Voter Data ---")
        print(f"Files in {beaufort_voter_dir}:")
        for file in os.listdir(beaufort_voter_dir):
            print(f"  - {file}")
            if file.endswith('.txt'):
                beaufort_voter_path = os.path.join(beaufort_voter_dir, file)
                try:
                    beaufort_voters = pd.read_csv(beaufort_voter_path, sep='\t', nrows=1000)
                    print(f"Columns in Beaufort County voter data:")
                    for col in beaufort_voters.columns:
                        print(f"  - {col}")
                    print(f"\nData shape: {beaufort_voters.shape}")
                except Exception as e:
                    print(f"Error reading Beaufort voter data: {e}")
                break

def explore_address_data():
    """Examine address datasets structure"""
    print("\n=== ADDRESS DATA EXPLORATION ===")
    
    # Pitt County addresses
    pitt_addr_dir = "../PITT-addresses-06-11-2025"
    if os.path.exists(pitt_addr_dir):
        print(f"\n--- Pitt County Address Data ---")
        print(f"Files in {pitt_addr_dir}:")
        for file in os.listdir(pitt_addr_dir):
            print(f"  - {file}")
        
        try:
            # Look for geodatabase or shapefiles
            for file in os.listdir(pitt_addr_dir):
                if file.endswith('.gdb'):
                    gdb_path = os.path.join(pitt_addr_dir, file)
                    print(f"Found geodatabase: {file}")
                    layers = gpd.list_layers(gdb_path)
                    print(f"Layers: {layers}")
                    if len(layers) > 0:
                        addresses = gpd.read_file(gdb_path, layer=layers['name'].iloc[0])
                        print(f"Shape: {addresses.shape}")
                        print(f"CRS: {addresses.crs}")
                        print(f"Columns: {list(addresses.columns)}")
                        print(f"Sample data:")
                        print(addresses.head())
                    break
                elif file.endswith('.shp'):
                    shp_path = os.path.join(pitt_addr_dir, file)
                    print(f"Found shapefile: {file}")
                    addresses = gpd.read_file(shp_path)
                    print(f"Shape: {addresses.shape}")
                    print(f"CRS: {addresses.crs}")
                    print(f"Columns: {list(addresses.columns)}")
                    print(f"Sample data:")
                    print(addresses.head())
                    break
        except Exception as e:
            print(f"Error reading Pitt address data: {e}")
    
    # Beaufort County addresses
    beaufort_addr_dir = "../BEAUFORT-addresses-06-11-2025"
    if os.path.exists(beaufort_addr_dir):
        print(f"\n--- Beaufort County Address Data ---")
        print(f"Files in {beaufort_addr_dir}:")
        for file in os.listdir(beaufort_addr_dir):
            print(f"  - {file}")
        
        try:
            # Look for geodatabase or shapefiles
            for file in os.listdir(beaufort_addr_dir):
                if file.endswith('.gdb'):
                    gdb_path = os.path.join(beaufort_addr_dir, file)
                    print(f"Found geodatabase: {file}")
                    layers = gpd.list_layers(gdb_path)
                    print(f"Layers: {layers}")
                    if layers:
                        addresses = gpd.read_file(gdb_path, layer=0)
                        print(f"Shape: {addresses.shape}")
                        print(f"CRS: {addresses.crs}")
                        print(f"Columns: {list(addresses.columns)}")
                    break
                elif file.endswith('.shp'):
                    shp_path = os.path.join(beaufort_addr_dir, file)
                    print(f"Found shapefile: {file}")
                    addresses = gpd.read_file(shp_path)
                    print(f"Shape: {addresses.shape}")
                    print(f"CRS: {addresses.crs}")
                    print(f"Columns: {list(addresses.columns)}")
                    break
        except Exception as e:
            print(f"Error reading Beaufort address data: {e}")

def explore_parcel_data():
    """Examine parcel datasets structure"""
    print("\n=== PARCEL DATA EXPLORATION ===")
    
    # Pitt County parcels
    pitt_parcel_dir = "../pitt-parcels-07-11-2025"
    if os.path.exists(pitt_parcel_dir):
        print(f"\n--- Pitt County Parcel Data ---")
        print(f"Files in {pitt_parcel_dir}:")
        for file in os.listdir(pitt_parcel_dir):
            print(f"  - {file}")
        
        try:
            for file in os.listdir(pitt_parcel_dir):
                if file.endswith('.shp'):
                    shp_path = os.path.join(pitt_parcel_dir, file)
                    print(f"Found shapefile: {file}")
                    parcels = gpd.read_file(shp_path)
                    print(f"Shape: {parcels.shape}")
                    print(f"CRS: {parcels.crs}")
                    print(f"Columns: {list(parcels.columns)}")
                    
                    # Look for PARVAL field
                    parval_cols = [col for col in parcels.columns if 'parval' in col.lower() or 'value' in col.lower()]
                    if parval_cols:
                        print(f"Property value fields found: {parval_cols}")
                        for col in parval_cols:
                            print(f"{col} sample values:")
                            print(parcels[col].describe())
                    else:
                        print("No obvious property value field found. All columns:")
                        for col in parcels.columns:
                            print(f"  - {col}")
                    break
        except Exception as e:
            print(f"Error reading Pitt parcel data: {e}")
    
    # Beaufort County parcels
    beaufort_parcel_dir = "../beaufort-parcels-06-18-2025"
    if os.path.exists(beaufort_parcel_dir):
        print(f"\n--- Beaufort County Parcel Data ---")
        print(f"Files in {beaufort_parcel_dir}:")
        for file in os.listdir(beaufort_parcel_dir):
            print(f"  - {file}")
        
        try:
            for file in os.listdir(beaufort_parcel_dir):
                if file.endswith('.shp'):
                    shp_path = os.path.join(beaufort_parcel_dir, file)
                    print(f"Found shapefile: {file}")
                    parcels = gpd.read_file(shp_path)
                    print(f"Shape: {parcels.shape}")
                    print(f"CRS: {parcels.crs}")
                    print(f"Columns: {list(parcels.columns)}")
                    
                    # Look for PARVAL field
                    parval_cols = [col for col in parcels.columns if 'parval' in col.lower() or 'value' in col.lower()]
                    if parval_cols:
                        print(f"Property value fields found: {parval_cols}")
                        for col in parval_cols:
                            print(f"{col} sample values:")
                            print(parcels[col].describe())
                    break
        except Exception as e:
            print(f"Error reading Beaufort parcel data: {e}")

if __name__ == "__main__":
    # Set working directory to script location
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("Exploring data structure to identify fields for geocoding...")
    
    explore_voter_data()
    explore_address_data()
    explore_parcel_data()
    
    print("\n=== NEXT STEPS ===")
    print("Based on the exploration above, identify:")
    print("1. Address fields in voter data (street, city, zip)")
    print("2. Address fields in address datasets for matching")
    print("3. Coordinate fields in address datasets")
    print("4. PARVAL field in parcel data for property value analysis")
