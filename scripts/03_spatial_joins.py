"""
Spatial Joins Script
Purpose: Connect geocoded voters to parcel data to get property values (PARVAL)
This enables analysis of political affiliation vs property values.
"""

import geopandas as gpd
import pandas as pd
import os
import time

def spatial_join_county(county_name, voters_file, parcels_file, output_dir):
    """Perform spatial join between voters and parcels for one county"""
    print(f"\n=== SPATIAL JOIN: {county_name.upper()} COUNTY ===")
    start_time = time.time()
    
    # Load geocoded voters
    print("Loading geocoded voters...")
    voters = gpd.read_file(voters_file)
    print(f"Loaded {len(voters)} geocoded voters")
    print(f"Voters CRS: {voters.crs}")
    
    # Load parcels
    print("Loading parcel data...")
    parcels = gpd.read_file(parcels_file)
    print(f"Loaded {len(parcels)} parcels")
    print(f"Parcels CRS: {parcels.crs}")
    
    # Check for property value fields
    parval_cols = [col for col in parcels.columns if 'parval' in col.lower() or 'value' in col.lower()]
    if parval_cols:
        parval_field = parval_cols[0]
        print(f"Found property value field: {parval_field}")
    else:
        print("Warning: No PARVAL field found. Available columns:")
        print(parcels.columns.tolist())
        parval_field = None
    
    # Ensure both datasets have same CRS (EPSG:2264)
    target_crs = 'EPSG:2264'
    if voters.crs != target_crs:
        print(f"Reprojecting voters from {voters.crs} to {target_crs}")
        voters = voters.to_crs(target_crs)
    
    if parcels.crs != target_crs:
        print(f"Reprojecting parcels from {parcels.crs} to {target_crs}")
        parcels = parcels.to_crs(target_crs)
    
    # Perform spatial join
    print("Performing spatial join (point-in-polygon)...")
    joined = gpd.sjoin(voters, parcels, how='left', predicate='within')
    print(f"Joined dataset has {len(joined)} records")
    
    # Count successful joins
    successful_joins = len(joined.dropna(subset=['index_right']))
    join_rate = (successful_joins / len(voters)) * 100
    print(f"Successful spatial joins: {successful_joins} ({join_rate:.1f}%)")
    
    # Add county identifier
    joined['county'] = county_name
    
    # Clean up duplicate columns from join
    if 'index_right' in joined.columns:
        joined = joined.drop('index_right', axis=1)
    
    # Save results
    output_file = os.path.join(output_dir, f"{county_name.lower()}_voters_with_parcels.gpkg")
    joined.to_file(output_file, driver='GPKG')
    
    elapsed = time.time() - start_time
    print(f"Processing time: {elapsed:.1f} seconds")
    print(f"Saved to: {output_file}")
    
    # Summary statistics
    if parval_field and parval_field in joined.columns:
        print(f"\nProperty value statistics:")
        valid_values = joined[parval_field].dropna()
        if len(valid_values) > 0:
            print(f"  Records with property values: {len(valid_values)}")
            print(f"  Mean property value: ${valid_values.mean():,.2f}")
            print(f"  Median property value: ${valid_values.median():,.2f}")
            print(f"  Min/Max: ${valid_values.min():,.2f} / ${valid_values.max():,.2f}")
        else:
            print("  No valid property values found")
    
    return joined

def analyze_political_property_values(joined_data, county_name):
    """Analyze property values by political party"""
    print(f"\n=== POLITICAL AFFILIATION vs PROPERTY VALUES: {county_name.upper()} ===")
    
    # Find property value field
    parval_cols = [col for col in joined_data.columns if 'parval' in col.lower() or 'value' in col.lower()]
    if not parval_cols:
        print("No property value field found for analysis")
        return
    
    parval_field = parval_cols[0]
    
    # Filter for valid property values and main parties
    valid_data = joined_data.dropna(subset=[parval_field, 'party_cd'])
    main_parties = valid_data[valid_data['party_cd'].isin(['DEM', 'REP', 'UNA'])]
    
    print(f"Analyzing {len(main_parties)} voters with valid property data")
    
    # Group by party and calculate statistics
    party_stats = main_parties.groupby('party_cd')[parval_field].agg([
        'count', 'mean', 'median', 'std', 'min', 'max'
    ]).round(2)
    
    print("\nProperty Value Statistics by Party:")
    print("=" * 60)
    for party in ['DEM', 'REP', 'UNA']:
        if party in party_stats.index:
            stats = party_stats.loc[party]
            print(f"\n{party} (n={stats['count']}):")
            print(f"  Mean:   ${stats['mean']:10,.2f}")
            print(f"  Median: ${stats['median']:10,.2f}")
            print(f"  Std:    ${stats['std']:10,.2f}")
            print(f"  Range:  ${stats['min']:,.2f} - ${stats['max']:,.2f}")
    
    return party_stats

def main():
    """Main execution for spatial joins"""
    print("=== SPATIAL JOINS: VOTERS + PARCELS ===")
    
    # Set working directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Create output directory
    output_dir = "../outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    total_start = time.time()
    all_joined_data = []
    
    # Process Pitt County
    print("\n" + "="*50)
    try:
        pitt_joined = spatial_join_county(
            "Pitt",
            "../outputs/pitt_voters_geocoded.gpkg",
            "../pitt-parcels-07-11-2025/nc_pitt_parcels_poly.shp",
            output_dir
        )
        all_joined_data.append(pitt_joined)
        
        # Analyze political affiliation vs property values
        pitt_stats = analyze_political_property_values(pitt_joined, "Pitt")
        
    except Exception as e:
        print(f"Error processing Pitt County: {e}")
    
    # Process Beaufort County
    print("\n" + "="*50)
    try:
        beaufort_joined = spatial_join_county(
            "Beaufort",
            "../outputs/beaufort_voters_geocoded.gpkg", 
            "../beaufort-parcels-06-18-2025/nc_beaufort_parcels_poly.shp",
            output_dir
        )
        all_joined_data.append(beaufort_joined)
        
        # Analyze political affiliation vs property values
        beaufort_stats = analyze_political_property_values(beaufort_joined, "Beaufort")
        
    except Exception as e:
        print(f"Error processing Beaufort County: {e}")
    
    # Combine both counties for comparison
    if len(all_joined_data) == 2:
        print("\n" + "="*50)
        print("=== COMBINED ANALYSIS: BOTH COUNTIES ===")
        
        combined_data = pd.concat(all_joined_data, ignore_index=True)
        combined_file = os.path.join(output_dir, "combined_voters_with_parcels.gpkg")
        combined_data.to_file(combined_file, driver='GPKG')
        print(f"Combined dataset saved: {combined_file}")
        
        # Cross-county comparison
        analyze_political_property_values(combined_data, "Combined")
    
    total_time = time.time() - total_start
    print(f"\n=== TOTAL PROCESSING TIME: {total_time:.1f} seconds ===")
    print("Spatial joins complete!")

if __name__ == "__main__":
    main()
