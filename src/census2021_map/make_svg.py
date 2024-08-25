import svgwrite
import csv

# A0 dimensions in millimeters (landscape)
width_mm = 1189
height_mm = 841

# Create an SVG drawing object with A0 dimensions in landscape orientation
dwg = svgwrite.Drawing('/home/juju/Bureau/map.svg', size=(f'{width_mm}mm', f'{height_mm}mm'))

# Set the background color to white
dwg.add(dwg.rect(insert=(0, 0), size=(f'{width_mm}mm', f'{height_mm}mm'), fill='white'))

# Calculate positions for shapes to be centered
center_x = width_mm / 2
center_y = height_mm / 2

# Draw a yellow circle with a 10 cm (100 mm) radius at the center
circle_radius_mm = 100
dwg.add(dwg.circle(center=(center_x, center_y), r=f'{circle_radius_mm}mm', fill='yellow'))

# Coordinates for a red triangle centered around the middle
triangle_points = [
    (center_x, center_y - 100),  # Top point of the triangle
    (center_x - 86.6, center_y + 50),  # Bottom left (forming an equilateral triangle)
    (center_x + 86.6, center_y + 50)  # Bottom right
]
dwg.add(dwg.polygon(points=triangle_points, fill='red'))

#read CSV file
cells = []
with open('/home/juju/geodata/census/csv_export.csv', mode='r', newline='') as file:
    csv_reader = csv.DictReader(file)

    for row in csv_reader:
        if row['T'] == '0': continue
        del row['fid']
        del row['M']
        del row['F']
        del row['EMP']
        del row['NAT']
        del row['EU_OTH']
        del row['OTH']
        del row['SAME']
        del row['CHG_IN']
        del row['CHG_OUT']
        id = row['GRD_ID']

        #CRS3035RES1000mN1000000E1966000
        id = id.replace("CRS3035RES1000mN", "")
        del row['GRD_ID']
        id = id.split("E")
        row['y'] = int(id[0])
        row['x'] = int(id[1])

        cells.append(row)


print(len(cells))
print(cells[0])

#TODO rank by x,y



# Save the SVG file
dwg.save()

print("SVG file created successfully.")
