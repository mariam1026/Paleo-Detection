from ij import IJ, ImagePlus
from ij.measure import ResultsTable
import os
import csv

# === CONFIGURABLE PATHS ===
input_folder = r"D:\Aldo-slices\MD_high_res_slices"         
output_folder = r"D:\Aldo-slices\output_aldo_high_res_slices"      

# Ensure output folder exists
if not os.path.exists(output_folder):
    os.makedirs(output_folder)


# === SLICE RANGE TO ANALYZE ===
start_index = 1
end_index = 741


# === GET ALL .CZI FILES ===
all_files = sorted([f for f in os.listdir(input_folder) if f.endswith(".czi")])
files_to_process = all_files[start_index - 1:end_index]

# Store all summary data
summary_data = []

for i, filename in enumerate(files_to_process, start=start_index):
    full_path = os.path.join(input_folder, filename)
    print("Processing file {}: {}".format(i, filename))

    # Open image
    imp = IJ.openImage(full_path)
    if imp is None:
        print("Failed to open: " + filename)
        continue

    imp.show()  # Required for some commands to work

    # Preprocessing
    IJ.run(imp, "8-bit", "")
    IJ.run(imp, "Gaussian Blur...", "sigma=2")
    IJ.run(imp, "Subtract Background...", "rolling=50 stack") # Stack ensures per-slice background removal
    
    
    # Thresholding
    imp.setAutoThreshold("Default dark no-reset")
    IJ.setThreshold(imp, 15, 255)

    # Convert to mask and analyze
    IJ.run(imp, "Convert to Mask", "")
    IJ.run("Clear Results")
    IJ.run("Set Measurements...", "area mean min centroid center shape redirect=None decimal=3")
    IJ.run(imp, "Analyze Particles...", "size=0-Infinity pixel show=Outlines clear label record starts summarize")

    # Save individual slice results
    result_filename = "results_slice_{}.csv".format(i)
    result_path = os.path.join(output_folder, result_filename)
    IJ.saveAs("Results", result_path)

    # Collect summary data
    summary_table = ResultsTable.getResultsTable()
    row_data = {"Slice": i}
    print(summary_table)

    particle_count = summary_table.getCounter()
    row_data["Particle Count"] = particle_count
    
    print("Particles in slice {}: {}".format(i,particle_count))

    if particle_count > 0:
        headings = summary_table.getHeadings()
        for heading in headings:
            try:
                value = summary_table.getValue(heading, 0)
                # print("heading :",heading)
                row_data[heading] = value
                if heading == "Area":
                    row_data["Area (micron^2)"] = value * pixel_area
            except:
                row_data[heading] = None
    else:
        print("No summary data found for slice {}".format(i))
        row_data["Note"] = "No data"

    summary_data.append(row_data)

    # Close image and results table
    imp.changes = False
    # Uncomment these lines when running over all slices:
    imp.close()
    IJ.run("Close")  # Close results window


# Write summary to a CSV file
summary_csv_path = os.path.join(output_folder, "summary_all_slices.csv")
if summary_data:
    headers = set()
    for row in summary_data:
        headers.update(row.keys())
    headers = list(headers)

    with open(summary_csv_path, 'wb') as f:  # Jython requires binary mode to avoid blank lines
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in summary_data:
            writer.writerow(row)

print("All slices processed. Summary saved to: " + summary_csv_path)