import geopandas as gpd
import matplotlib.pyplot as plt
import os

output_dir = r"C:\Users\Peanu\OneDrive\Documents\GitHub\Final-Proj-Geospatial\outputs"

# Load school buffer and sample school data
gpkg_buffers = os.path.join(output_dir, "analysis_2_school_buffers.gpkg")
gpkg_schools = os.path.join(output_dir, "analysis_2_sample_schools.gpkg")

buffers = gpd.read_file(gpkg_buffers)
print("Buffer columns:", buffers.columns)
schools = gpd.read_file(gpkg_schools)

# Plot
fig, ax = plt.subplots(figsize=(10, 10))


# Plot all buffer geometries (if any)
buffers.boundary.plot(ax=ax, color='blue', alpha=0.5, label='School Buffer')

# Plot voters within each buffer distance
colors = {1000: 'red', 2000: 'orange', 5000: 'green'}
for dist in [1000, 2000, 5000]:
    col = f'within_{dist}ft_school'
    if col in buffers.columns:
        voters_in_buffer = buffers[buffers[col] == 1]
        if not voters_in_buffer.empty:
            voters_in_buffer.plot(ax=ax, marker='o', color=colors[dist], markersize=10, alpha=0.5, label=f'Voters within {dist} ft')

# Plot schools
schools.plot(ax=ax, color='black', marker='*', markersize=100, label='School')

# Set title and legend
ax.set_title('Voter Proximity to Schools (Buffers)', fontsize=14)
ax.legend()
plt.xlabel('Easting (ft)')
plt.ylabel('Northing (ft)')
plt.tight_layout()

# Save
out_path = r"C:\Users\Peanu\OneDrive\Documents\GitHub\Final-Proj-Geospatial\outputs\school_proximity_analysis.png"
plt.savefig(out_path, dpi=300)
plt.close()
print(f"Saved: {out_path}")
