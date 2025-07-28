"""
Ultra-Fast Geocoding Script for Voter Addresses
Purpose: Extremely fast geocoding using exact matching and simple preprocessing
"""

import geopandas as gpd
import pandas as pd
import os
import re
import time

def ultra_fast_geocode_county(county_name, voter_file, address_gdb, output_dir, limit_voters=None):
    """Ultra fast geocoding using exact string matching"""
    print(f"\n=== ULTRA-FAST GEOCODING: {county_name.upper()} COUNTY ===")
    start_time = time.time()
    
    # Load voter data
    print("Loading voter data...")
    # Try different encodings for the full dataset
    encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    voters = None
    
    for encoding in encodings_to_try:
        try:
            if limit_voters:
                voters = pd.read_csv(voter_file, sep='\t', encoding=encoding, nrows=limit_voters)
                print(f"Loaded {len(voters)} voters (limited sample) using {encoding} encoding")
            else:
                voters = pd.read_csv(voter_file, sep='\t', encoding=encoding)
                print(f"Loaded {len(voters)} voters (ALL VOTERS) using {encoding} encoding")
            break
        except UnicodeDecodeError:
            print(f"Failed with {encoding} encoding, trying next...")
            continue
    
    if voters is None:
        raise Exception("Could not read voter file with any encoding")
    
    # Filter active voters only
    active_voters = voters[voters['voter_status_desc'] == 'ACTIVE'].copy()
    print(f"Active voters: {len(active_voters)}")
    
    # Load address data
    print("Loading address data...")
    addresses = gpd.read_file(address_gdb, layer=0)
    print(f"Loaded {len(addresses)} addresses")
    
    # Enhanced address cleaning function
    def enhanced_clean(addr):
        if pd.isna(addr):
            return ""
        
        # Convert to uppercase and strip
        addr = str(addr).upper().strip()
        
        # Remove common punctuation
        addr = re.sub(r'[,.\-#]', ' ', addr)
        
        # Standardize common abbreviations
        replacements = {
            r'\bSTREET\b': 'ST',
            r'\bAVENUE\b': 'AVE',
            r'\bROAD\b': 'RD', 
            r'\bDRIVE\b': 'DR',
            r'\bLANE\b': 'LN',
            r'\bCOURT\b': 'CT',
            r'\bCIRCLE\b': 'CIR',
            r'\bPLACE\b': 'PL'
        }
        
        for pattern, replacement in replacements.items():
            addr = re.sub(pattern, replacement, addr)
        
        # Remove extra spaces
        addr = re.sub(r'\s+', ' ', addr).strip()
        
        return addr
    
    # Clean addresses
    print("Cleaning addresses...")
    active_voters['clean_address'] = active_voters['res_street_address'].apply(enhanced_clean)
    
    # Debug: show sample voter addresses
    print("Sample voter addresses:")
    for i, addr in enumerate(active_voters['clean_address'].head(5)):
        if addr:
            print(f"  Voter {i+1}: '{addr}'")
    
    # Find address column in geodatabase
    addr_cols = [col for col in addresses.columns if any(x in col.upper() for x in ['ADDR', 'STREET', 'FULL'])]
    if not addr_cols:
        print("No address column found! Available columns:", addresses.columns.tolist())
        return None
    
    addr_col = addr_cols[0]
    print(f"Using address column: {addr_col}")
    addresses['clean_address'] = addresses[addr_col].apply(enhanced_clean)
    
    # Debug: show sample reference addresses
    print("Sample reference addresses:")
    for i, addr in enumerate(addresses['clean_address'].head(5)):
        if addr:
            print(f"  Ref {i+1}: '{addr}'")
    
    # Create lookup dictionary for instant matching
    print("Creating address lookup...")
    addr_lookup = {}
    for idx, row in addresses.iterrows():
        clean_addr = row['clean_address']
        if clean_addr and clean_addr not in addr_lookup:
            addr_lookup[clean_addr] = {
                'x': row.geometry.x,
                'y': row.geometry.y,
                'geometry': row.geometry
            }
    
    print(f"Created lookup with {len(addr_lookup)} unique addresses")
    
    # Match addresses instantly
    print("Matching addresses...")
    matches = []
    matched_count = 0
    
    for idx, voter in active_voters.iterrows():
        clean_addr = voter['clean_address']
        if clean_addr in addr_lookup:
            match = addr_lookup[clean_addr]
            voter_dict = voter.to_dict()
            voter_dict.update({
                'x': match['x'],
                'y': match['y'],
                'matched': True
            })
            matches.append(voter_dict)
            matched_count += 1
    
    if matches:
        # Create GeoDataFrame
        matched_df = pd.DataFrame(matches)
        geometry = gpd.points_from_xy(matched_df['x'], matched_df['y'])
        voters_gdf = gpd.GeoDataFrame(matched_df, geometry=geometry, crs=addresses.crs)
        
        # Ensure CRS is EPSG:2264
        if voters_gdf.crs != 'EPSG:2264':
            voters_gdf = voters_gdf.to_crs('EPSG:2264')
        
        # Save results
        output_file = os.path.join(output_dir, f"{county_name.lower()}_voters_geocoded.gpkg")
        voters_gdf.to_file(output_file, driver='GPKG')
        
        # Results
        total_voters = len(active_voters)
        success_rate = (matched_count / total_voters) * 100 if total_voters > 0 else 0
        elapsed = time.time() - start_time
        
        print(f"\n=== RESULTS ===")
        print(f"Total voters: {total_voters}")
        print(f"Geocoded: {matched_count}")
        print(f"Success rate: {success_rate:.1f}%")
        print(f"Time: {elapsed:.1f} seconds")
        print(f"Saved to: {output_file}")
        
        return voters_gdf
    else:
        print("No matches found!")
        return None
    
    # FAST MATCHING with lower threshold
    print("=== Fast Fuzzy Matching (threshold: 70) ===")
    matched_voters = []
    batch_size = 100  # Smaller batches
    
    start_time = time.time()
    
    for i in range(0, min(1000, len(active_voters)), batch_size):  # Limit to 1000 for demo
        batch = active_voters.iloc[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1} ({len(batch)} voters)...")
        
        for idx, voter in batch.iterrows():
            voter_addr = voter['clean_address']
            if not voter_addr or voter_addr.strip() == '':
                continue
                
            # Quick fuzzy match with lower threshold for speed
            best_match = None
            best_score = 0
            
            for addr_idx, addr_row in addresses.iterrows():
                addr_str = addr_row['clean_address']
                if not addr_str or addr_str.strip() == '':
                    continue
                    
                # Use faster ratio method
                score = fuzz.ratio(voter_addr, addr_str)
                
                if score > 70 and score > best_score:  # Lower threshold = faster
                    best_score = score
                    best_match = addr_row
                    
                # Early exit for exact matches
                if score > 95:
                    break
            
            if best_match is not None:
                # Create matched voter record
                matched_voter = voter.copy()
                matched_voter['match_score'] = best_score
                matched_voter['geometry'] = best_match['geometry']
                matched_voter['matched_address'] = best_match['clean_address']
                matched_voters.append(matched_voter)
        
        # Progress update
        elapsed = time.time() - start_time
        print(f"  Matched: {len(matched_voters)} | Time: {elapsed:.1f}s")
    
    if not matched_voters:
        print("No matches found!")
        return
    
    # Create GeoDataFrame
    print("Creating GeoDataFrame...")
    matched_gdf = gpd.GeoDataFrame(matched_voters)
    matched_gdf.crs = addresses.crs
    
    # Save results
    output_file = os.path.join(output_dir, f"{county_name.lower()}_geocoded_voters.gpkg")
    matched_gdf.to_file(output_file, driver="GPKG")
    
    # Calculate success rate
    total_active = len(active_voters)
    matched_count = len(matched_gdf)
    success_rate = (matched_count / total_active) * 100
    
    print(f"\n=== {county_name.upper()} RESULTS ===")
    print(f"Total active voters processed: {total_active}")
    print(f"Successfully geocoded: {matched_count}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Output saved: {output_file}")
    
    return matched_gdf

def main():
    """Main execution with option to process all voters"""
    print("=== FAST VOTER GEOCODING ===")
    
    # Ask user for processing preference  
    print("\nChoose processing mode:")
    print("1. Quick test (1000 voters per county)")
    print("2. Process ALL voters (recommended for final analysis)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        limit_voters = 1000
        print("Processing limited samples for speed...")
    elif choice == "2": 
        limit_voters = None
        print("Processing ALL voters...")
    else:
        print("Invalid choice. Using quick test mode.")
        limit_voters = 1000
    
    # Set working directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Create output directory
    output_dir = "../outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    total_start = time.time()
    
    # Process Pitt County
    try:
        pitt_gdf = ultra_fast_geocode_county(
            "Pitt",
            "../ncvoterPitt/ncvoter74.txt",
            "../PITT-addresses-06-11-2025/PITT.gdb",
            output_dir,
            limit_voters
        )
    except Exception as e:
        print(f"Error processing Pitt County: {e}")
    
    # Process Beaufort County
    try:
        beaufort_gdf = ultra_fast_geocode_county(
            "Beaufort", 
            "../ncvoterBeaufort/ncvoter7.txt",
            "../BEAUFORT-addresses-06-11-2025/BEAUFORT.gdb",
            output_dir,
            limit_voters
        )
    except Exception as e:
        print(f"Error processing Beaufort County: {e}")
    
    total_time = time.time() - total_start
    print(f"\n=== TOTAL PROCESSING TIME: {total_time:.1f} seconds ===")
    print("Geocoding complete!")

if __name__ == "__main__":
    main()
