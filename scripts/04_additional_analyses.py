"""
Additional Spatial Analyses Script
Purpose: Implement 5 additional spatial analyses for voter characteristics
"""

import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from shapely.geometry import Point
import warnings
warnings.filterwarnings('ignore')

def analysis_1_urban_rural_classification(combined_data, output_dir):
    """
    Analysis 1: Urban vs Rural Voter Classification
    Classify voters as urban/rural based on population density and distance to city centers
    """
    print("\n" + "="*60)
    print("ANALYSIS 1: URBAN vs RURAL VOTER CLASSIFICATION")
    print("="*60)
    
    # Create density-based classification using simple distance calculations
    # Calculate local density by measuring distance to nearby voters
    print("Calculating voter density scores...")
    
    # Get coordinates
    coords = np.array([[point.x, point.y] for point in combined_data.geometry])
    
    # Simple density calculation: count voters within 2000 feet
    density_scores = []
    search_radius = 2000  # feet (appropriate for EPSG:2264)
    
    for i, coord in enumerate(coords):
        # Calculate distances to all other points
        distances = np.sqrt(np.sum((coords - coord) ** 2, axis=1))
        # Count neighbors within radius (excluding self)
        neighbors_within_radius = np.sum((distances > 0) & (distances <= search_radius))
        density_scores.append(neighbors_within_radius)
        
        # Progress indicator for large datasets
        if i % 10000 == 0:
            print(f"  Processed {i:,} of {len(coords):,} voters")
    
    density_scores = np.array(density_scores)
    
    # Classify based on density percentiles
    urban_threshold = np.percentile(density_scores, 75)  # Top 25% = Urban
    rural_threshold = np.percentile(density_scores, 25)   # Bottom 25% = Rural
    
    combined_data['density_score'] = density_scores
    combined_data['urban_rural'] = 'Suburban'  # Default
    combined_data.loc[density_scores >= urban_threshold, 'urban_rural'] = 'Urban'
    combined_data.loc[density_scores <= rural_threshold, 'urban_rural'] = 'Rural'
    
    # Analyze political affiliation by urban/rural classification
    print("\nVoter Distribution by Urban/Rural Classification:")
    classification_counts = combined_data['urban_rural'].value_counts()
    for category in classification_counts.index:
        count = classification_counts[category]
        percentage = (count / len(combined_data)) * 100
        print(f"  {category}: {count:,} voters ({percentage:.1f}%)")
    
    print(f"\nPolitical Affiliation by Urban/Rural Classification:")
    crosstab = pd.crosstab(combined_data['urban_rural'], combined_data['party_cd'], normalize='index') * 100
    print(crosstab.round(1))
    
    # Property values by classification
    print(f"\nProperty Values by Urban/Rural Classification:")
    parval_cols = [col for col in combined_data.columns if 'parval' in col.lower()]
    if parval_cols:
        parval_col = parval_cols[0]
        urban_rural_stats = combined_data.groupby('urban_rural')[parval_col].agg([
            'count', 'mean', 'median', 'std'
        ]).round(2)
        print(urban_rural_stats)
    
    # Save results
    output_file = os.path.join(output_dir, "analysis_1_urban_rural_classification.gpkg")
    combined_data.to_file(output_file, driver='GPKG')
    print(f"\nSaved: {output_file}")
    
    return combined_data

def analysis_2_buffer_analysis_schools(combined_data, output_dir):
    """
    Analysis 2: Buffer Analysis Around Schools
    Analyze voter characteristics within different distances of schools
    """
    print("\n" + "="*60)
    print("ANALYSIS 2: BUFFER ANALYSIS AROUND SCHOOLS")
    print("="*60)
    
    # Create sample school locations (you would normally load real school data)
    # For demonstration, we'll create schools in high-density areas
    print("Creating sample school locations based on voter density...")
    
    # Find top density areas for school placement
    high_density_voters = combined_data.nlargest(20, 'density_score')
    
    # Create schools at these locations (simulated)
    schools_data = []
    for i, (idx, voter) in enumerate(high_density_voters.iterrows()):
        if i % 4 == 0:  # Every 4th high-density location gets a school
            schools_data.append({
                'school_id': f'School_{i//4 + 1}',
                'county': voter['county'],
                'geometry': voter.geometry
            })
    
    schools_gdf = gpd.GeoDataFrame(schools_data, crs=combined_data.crs)
    print(f"Created {len(schools_gdf)} sample schools")
    
    # Create buffers around schools
    buffer_distances = [1000, 2000, 5000]  # feet (since we're using EPSG:2264)
    
    for distance in buffer_distances:
        print(f"\nAnalyzing {distance} ft buffer around schools...")
        
        # Create buffer zones
        school_buffers = schools_gdf.copy()
        school_buffers.geometry = school_buffers.geometry.buffer(distance)
        
        # Find voters within buffers
        voters_in_buffer = gpd.sjoin(combined_data, school_buffers, predicate='within')
        
        print(f"  Voters within {distance} ft of schools: {len(voters_in_buffer):,}")
        
        if len(voters_in_buffer) > 0:
            # Political breakdown
            party_breakdown = voters_in_buffer['party_cd'].value_counts()
            print(f"  Political breakdown:")
            for party in ['DEM', 'REP', 'UNA']:
                if party in party_breakdown:
                    count = party_breakdown[party]
                    percentage = (count / len(voters_in_buffer)) * 100
                    print(f"    {party}: {count:,} ({percentage:.1f}%)")
            
            # Property value analysis
            parval_cols = [col for col in voters_in_buffer.columns if 'parval' in col.lower()]
            if parval_cols:
                parval_col = parval_cols[0]
                mean_value = voters_in_buffer[parval_col].mean()
                print(f"  Mean property value: ${mean_value:,.2f}")
        
        # Add buffer indicator to main dataset
        buffer_col = f'within_{distance}ft_school'
        combined_data[buffer_col] = combined_data.index.isin(voters_in_buffer.index)
    
    # Save school locations and updated voter data
    schools_file = os.path.join(output_dir, "analysis_2_sample_schools.gpkg")
    schools_gdf.to_file(schools_file, driver='GPKG')
    
    output_file = os.path.join(output_dir, "analysis_2_school_buffers.gpkg")
    combined_data.to_file(output_file, driver='GPKG')
    print(f"\nSaved: {output_file}")
    print(f"Saved: {schools_file}")
    
    return combined_data

def analysis_3_age_demographics_spatial(combined_data, output_dir):
    """
    Analysis 3: Age Demographics Spatial Patterns
    Analyze spatial clustering of different age groups
    """
    print("\n" + "="*60)
    print("ANALYSIS 3: AGE DEMOGRAPHICS SPATIAL PATTERNS")
    print("="*60)
    
    # Calculate age from birth year (assuming current year is 2025)
    if 'birth_year' in combined_data.columns:
        combined_data['age'] = 2025 - combined_data['birth_year']
        
        # Create age groups
        combined_data['age_group'] = 'Unknown'
        combined_data.loc[combined_data['age'] < 30, 'age_group'] = 'Young (18-29)'
        combined_data.loc[(combined_data['age'] >= 30) & (combined_data['age'] < 45), 'age_group'] = 'Young Adult (30-44)'
        combined_data.loc[(combined_data['age'] >= 45) & (combined_data['age'] < 65), 'age_group'] = 'Middle Age (45-64)'
        combined_data.loc[combined_data['age'] >= 65, 'age_group'] = 'Senior (65+)'
        
        print("Age Group Distribution:")
        age_dist = combined_data['age_group'].value_counts()
        for age_group in age_dist.index:
            count = age_dist[age_group]
            percentage = (count / len(combined_data)) * 100
            print(f"  {age_group}: {count:,} ({percentage:.1f}%)")
        
        # Political affiliation by age group
        print(f"\nPolitical Affiliation by Age Group:")
        age_politics = pd.crosstab(combined_data['age_group'], combined_data['party_cd'], normalize='index') * 100
        print(age_politics.round(1))
        
        # Property values by age group
        parval_cols = [col for col in combined_data.columns if 'parval' in col.lower()]
        if parval_cols:
            parval_col = parval_cols[0]
            print(f"\nProperty Values by Age Group:")
            age_property = combined_data.groupby('age_group')[parval_col].agg([
                'count', 'mean', 'median'
            ]).round(2)
            print(age_property)
        
        # Spatial clustering analysis by county
        print(f"\nAge Distribution by County:")
        county_age = pd.crosstab(combined_data['county'], combined_data['age_group'], normalize='index') * 100
        print(county_age.round(1))
        
    else:
        print("Birth year data not available for age analysis")
        combined_data['age_group'] = 'Unknown'
    
    # Save results
    output_file = os.path.join(output_dir, "analysis_3_age_demographics.gpkg")
    combined_data.to_file(output_file, driver='GPKG')
    print(f"\nSaved: {output_file}")
    
    return combined_data

def analysis_4_distance_to_county_centers(combined_data, output_dir):
    """
    Analysis 4: Distance to County Centers Analysis
    Analyze voter characteristics by distance to county administrative centers
    """
    print("\n" + "="*60)
    print("ANALYSIS 4: DISTANCE TO COUNTY CENTERS")
    print("="*60)
    
    # Calculate county centers (centroids of voter distributions)
    county_centers = {}
    
    for county in combined_data['county'].unique():
        county_voters = combined_data[combined_data['county'] == county]
        
        # Calculate centroid
        coords = np.array([[point.x, point.y] for point in county_voters.geometry])
        center_x = coords[:, 0].mean()
        center_y = coords[:, 1].mean()
        center_point = Point(center_x, center_y)
        
        county_centers[county] = center_point
        print(f"{county} County center: ({center_x:.0f}, {center_y:.0f})")
    
    # Calculate distance to county center for each voter
    def calc_distance_to_center(row):
        county = row['county']
        voter_point = row.geometry
        center_point = county_centers[county]
        return voter_point.distance(center_point)
    
    combined_data['distance_to_center'] = combined_data.apply(calc_distance_to_center, axis=1)
    
    # Create distance categories
    combined_data['distance_category'] = 'Unknown'
    distance_percentiles = combined_data['distance_to_center'].quantile([0.25, 0.5, 0.75])
    
    combined_data.loc[combined_data['distance_to_center'] <= distance_percentiles[0.25], 'distance_category'] = 'Very Close (0-25%)'
    combined_data.loc[(combined_data['distance_to_center'] > distance_percentiles[0.25]) & 
                     (combined_data['distance_to_center'] <= distance_percentiles[0.5]), 'distance_category'] = 'Close (25-50%)'
    combined_data.loc[(combined_data['distance_to_center'] > distance_percentiles[0.5]) & 
                     (combined_data['distance_to_center'] <= distance_percentiles[0.75]), 'distance_category'] = 'Far (50-75%)'
    combined_data.loc[combined_data['distance_to_center'] > distance_percentiles[0.75], 'distance_category'] = 'Very Far (75-100%)'
    
    print(f"\nDistance Categories:")
    dist_counts = combined_data['distance_category'].value_counts()
    for category in dist_counts.index:
        count = dist_counts[category]
        percentage = (count / len(combined_data)) * 100
        print(f"  {category}: {count:,} ({percentage:.1f}%)")
    
    # Political patterns by distance
    print(f"\nPolitical Affiliation by Distance to County Center:")
    distance_politics = pd.crosstab(combined_data['distance_category'], combined_data['party_cd'], normalize='index') * 100
    print(distance_politics.round(1))
    
    # Property values by distance
    parval_cols = [col for col in combined_data.columns if 'parval' in col.lower()]
    if parval_cols:
        parval_col = parval_cols[0]
        print(f"\nProperty Values by Distance to County Center:")
        distance_property = combined_data.groupby('distance_category')[parval_col].agg([
            'count', 'mean', 'median'
        ]).round(2)
        print(distance_property)
    
    # Save results with county centers
    centers_data = []
    for county, center_point in county_centers.items():
        centers_data.append({
            'county': county,
            'geometry': center_point
        })
    
    centers_gdf = gpd.GeoDataFrame(centers_data, crs=combined_data.crs)
    centers_file = os.path.join(output_dir, "analysis_4_county_centers.gpkg")
    centers_gdf.to_file(centers_file, driver='GPKG')
    
    output_file = os.path.join(output_dir, "analysis_4_distance_to_centers.gpkg")
    combined_data.to_file(output_file, driver='GPKG')
    print(f"\nSaved: {output_file}")
    print(f"Saved: {centers_file}")
    
    return combined_data

def analysis_5_voter_registration_date_patterns(combined_data, output_dir):
    """
    Analysis 5: Voter Registration Date Spatial Patterns
    Analyze when voters registered and spatial patterns of registration timing
    """
    print("\n" + "="*60)
    print("ANALYSIS 5: VOTER REGISTRATION DATE PATTERNS")
    print("="*60)
    
    # Analyze registration date if available
    if 'registr_dt' in combined_data.columns:
        # Convert registration date
        combined_data['registration_date'] = pd.to_datetime(combined_data['registr_dt'], errors='coerce')
        combined_data['registration_year'] = combined_data['registration_date'].dt.year
        
        # Create registration period categories
        combined_data['registration_period'] = 'Unknown'
        combined_data.loc[combined_data['registration_year'] < 2000, 'registration_period'] = 'Before 2000'
        combined_data.loc[(combined_data['registration_year'] >= 2000) & (combined_data['registration_year'] < 2010), 'registration_period'] = '2000-2009'
        combined_data.loc[(combined_data['registration_year'] >= 2010) & (combined_data['registration_year'] < 2020), 'registration_period'] = '2010-2019'
        combined_data.loc[combined_data['registration_year'] >= 2020, 'registration_period'] = '2020-Present'
        
        print("Voter Registration Periods:")
        reg_dist = combined_data['registration_period'].value_counts()
        for period in reg_dist.index:
            count = reg_dist[period]
            percentage = (count / len(combined_data)) * 100
            print(f"  {period}: {count:,} ({percentage:.1f}%)")
        
        # Political affiliation by registration period
        print(f"\nPolitical Affiliation by Registration Period:")
        reg_politics = pd.crosstab(combined_data['registration_period'], combined_data['party_cd'], normalize='index') * 100
        print(reg_politics.round(1))
        
        # Registration patterns by county
        print(f"\nRegistration Periods by County:")
        county_reg = pd.crosstab(combined_data['county'], combined_data['registration_period'], normalize='index') * 100
        print(county_reg.round(1))
        
        # Recent registration (2020+) spatial patterns
        recent_registrants = combined_data[combined_data['registration_year'] >= 2020]
        if len(recent_registrants) > 0:
            print(f"\nRecent Registrants (2020+): {len(recent_registrants):,}")
            print("Political breakdown of recent registrants:")
            recent_politics = recent_registrants['party_cd'].value_counts()
            for party in ['DEM', 'REP', 'UNA']:
                if party in recent_politics:
                    count = recent_politics[party]
                    percentage = (count / len(recent_registrants)) * 100
                    print(f"  {party}: {count:,} ({percentage:.1f}%)")
    
    else:
        print("Registration date data not available")
        combined_data['registration_period'] = 'Unknown'
    
    # Additional analysis: Voting frequency patterns if available
    if 'total_voters' in combined_data.columns or 'voter_status_desc' in combined_data.columns:
        print(f"\nVoter Status Distribution:")
        status_dist = combined_data['voter_status_desc'].value_counts()
        for status in status_dist.index:
            count = status_dist[status]
            percentage = (count / len(combined_data)) * 100
            print(f"  {status}: {count:,} ({percentage:.1f}%)")
    
    # Save results
    output_file = os.path.join(output_dir, "analysis_5_registration_patterns.gpkg")
    combined_data.to_file(output_file, driver='GPKG')
    print(f"\nSaved: {output_file}")
    
    return combined_data

def create_summary_report(combined_data, output_dir):
    """Create a comprehensive summary report of all analyses"""
    print("\n" + "="*60)
    print("COMPREHENSIVE SUMMARY REPORT")
    print("="*60)
    
    summary_file = os.path.join(output_dir, "spatial_analysis_summary_report.txt")
    
    with open(summary_file, 'w') as f:
        f.write("\SPATIAL ANALYSIS SUMMARY\n")
        f.write("="*60 + "\n\n")
        
        f.write(f"Total Voters Analyzed: {len(combined_data):,}\n")
        f.write(f"Counties: {', '.join(combined_data['county'].unique())}\n\n")
        
        # Overall political breakdown
        f.write("OVERALL POLITICAL BREAKDOWN:\n")
        party_dist = combined_data['party_cd'].value_counts()
        for party in party_dist.index:
            count = party_dist[party]
            percentage = (count / len(combined_data)) * 100
            f.write(f"  {party}: {count:,} ({percentage:.1f}%)\n")
        f.write("\n")
        
        # Property value summary
        parval_cols = [col for col in combined_data.columns if 'parval' in col.lower()]
        if parval_cols:
            parval_col = parval_cols[0]
            f.write("PROPERTY VALUE SUMMARY:\n")
            f.write(f"  Mean: ${combined_data[parval_col].mean():,.2f}\n")
            f.write(f"  Median: ${combined_data[parval_col].median():,.2f}\n")
            f.write(f"  Min: ${combined_data[parval_col].min():,.2f}\n")
            f.write(f"  Max: ${combined_data[parval_col].max():,.2f}\n\n")
        
        # Key findings from each analysis
        f.write("KEY FINDINGS BY ANALYSIS:\n\n")
        
        f.write("1. URBAN/RURAL CLASSIFICATION:\n")
        if 'urban_rural' in combined_data.columns:
            urban_rural_dist = combined_data['urban_rural'].value_counts()
            for category in urban_rural_dist.index:
                count = urban_rural_dist[category]
                percentage = (count / len(combined_data)) * 100
                f.write(f"   - {category}: {count:,} ({percentage:.1f}%)\n")
        f.write("\n")
        
        f.write("2. SCHOOL BUFFER ANALYSIS:\n")
        for distance in [1000, 2000, 5000]:
            buffer_col = f'within_{distance}ft_school'
            if buffer_col in combined_data.columns:
                within_count = combined_data[buffer_col].sum()
                percentage = (within_count / len(combined_data)) * 100
                f.write(f"   - Within {distance} ft of schools: {within_count:,} ({percentage:.1f}%)\n")
        f.write("\n")
        
        f.write("3. AGE DEMOGRAPHICS:\n")
        if 'age_group' in combined_data.columns:
            age_dist = combined_data['age_group'].value_counts()
            for age_group in age_dist.index:
                count = age_dist[age_group]
                percentage = (count / len(combined_data)) * 100
                f.write(f"   - {age_group}: {count:,} ({percentage:.1f}%)\n")
        f.write("\n")
        
        f.write("4. DISTANCE TO COUNTY CENTERS:\n")
        if 'distance_category' in combined_data.columns:
            dist_dist = combined_data['distance_category'].value_counts()
            for category in dist_dist.index:
                count = dist_dist[category]
                percentage = (count / len(combined_data)) * 100
                f.write(f"   - {category}: {count:,} ({percentage:.1f}%)\n")
        f.write("\n")
        
        f.write("5. REGISTRATION PATTERNS:\n")
        if 'registration_period' in combined_data.columns:
            reg_dist = combined_data['registration_period'].value_counts()
            for period in reg_dist.index:
                count = reg_dist[period]
                percentage = (count / len(combined_data)) * 100
                f.write(f"   - {period}: {count:,} ({percentage:.1f}%)\n")
        f.write("\n")
        
        f.write("FILES CREATED:\n")
        f.write("- analysis_1_urban_rural_classification.gpkg\n")
        f.write("- analysis_2_school_buffers.gpkg\n")
        f.write("- analysis_2_sample_schools.gpkg\n")
        f.write("- analysis_3_age_demographics.gpkg\n")
        f.write("- analysis_4_distance_to_centers.gpkg\n")
        f.write("- analysis_4_county_centers.gpkg\n")
        f.write("- analysis_5_registration_patterns.gpkg\n")
        f.write("- spatial_analysis_summary_report.txt\n")
    
    print(f"Summary report saved: {summary_file}")

def main():
    """Main execution for additional spatial analyses"""
    print("=== ADDITIONAL SPATIAL ANALYSES ===")    
    # Set working directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Create output directory
    output_dir = "../outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Load combined voter data with parcels
    combined_file = os.path.join(output_dir, "combined_voters_with_parcels.gpkg")
    if not os.path.exists(combined_file):
        print(f"Error: {combined_file} not found!")
        print("Please run spatial joins script first.")
        return
    
    print(f"Loading combined data from: {combined_file}")
    combined_data = gpd.read_file(combined_file)
    print(f"Loaded {len(combined_data):,} voters with parcel data")
    
    # Run all 5 analyses
    try:
        combined_data = analysis_1_urban_rural_classification(combined_data, output_dir)
        combined_data = analysis_2_buffer_analysis_schools(combined_data, output_dir)
        combined_data = analysis_3_age_demographics_spatial(combined_data, output_dir)
        combined_data = analysis_4_distance_to_county_centers(combined_data, output_dir)
        combined_data = analysis_5_voter_registration_date_patterns(combined_data, output_dir)
        
        # Create comprehensive summary
        create_summary_report(combined_data, output_dir)
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
