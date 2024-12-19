from data_loader import *
from vertical_diagnostics import *
import xarray as xr


def vertical_diagnostics_all(results_path, year_1=None, year_f=None, verbose=False):
    '''
    Compute all vertical diagnostics for a run and return them in a xr.Dataset.
    
    '''

    u = load_variable(results_path, 'u', year_1=year_1, year_f=year_f)
    v = load_variable(results_path, 'v', year_1=year_1, year_f=year_f)

    diag_variables = ['elem_area', 'nod_area']
    elem_area, nod_area = get_mesh_diagnostics(results_path, diag_variables)
    nod_area = nod_area.isel(nz=0)


    if verbose:
        print('Computing eke...')
    eke = mean_EKE(u, v, elem_area).compute()

    del u, v

    temp = load_variable(results_path, 'temp', year_1=year_1, year_f=year_f)
    w = load_variable(results_path, 'w', year_1=year_1, year_f=year_f)
    
    if verbose:
        print('Computing buoy_flux...')
    buoy_flux = mean_buyoancy(w, temp, nod_area).compute()

    del temp

    if verbose:
        print('Computing w_rms...')
    w_rms = RMS_vertical_velocity(w, nod_area).compute()

    ds_diags = xr.merge([{'w_rms': w_rms}, {'eke': eke}, {'buoy_flux': buoy_flux}]) 

    return ds_diags