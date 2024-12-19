import sys
from pathlib import Path
import xarray as xr
from high_level_functions import compute_vertical_diagnostics

# modify values in this block
data_path = '/gxfs_work/geomar/smomw649/results/souff_lvl4/souff_20_0005_03_dyn/'
output_path = '../processed_data/souff_lvl4/souff_20_0005_03_dyn/profile_diags.nc'
year_1 = 1902
year_f = None

output_path = Path(output_path)
output_path.parent.mkdir(parents=True, exist_ok=True)

if output_path.exists():
    while True:
        answer = input('File exists. Do you want to overwrite [Y/n]? ').strip().lower()
        if answer=='y' or answer=='':
            break

        elif answer=='n':
            print('Exiting...')
            sys.exit()
        
        else:
            print('Invalid option, please enter "y" for yes or "n" for no.')
    

ds_diags = vertical_diagnostics_all(data_path, year_1, year_f, verbose=True)

print('Saving results to file.')
ds_diags.to_netcdf(output_path)
