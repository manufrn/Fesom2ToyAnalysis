import numpy as np
import xarray as xr
from scipy.interpolate import griddata
from multiprocessing import Pool
from tqdm.auto import tqdm

from scipy.spatial import Delaunay
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator, CloughTocher2DInterpolator


def interpolate_to_grid(field, xx0, yy0, XX1, YY1, days, lvls, method):
    """
    Description: 
        Interpolates field from a grid of xx0, yy0 coordinates to a target grid of XX1, YY1 coordinates
        using a specified method (nearest, linear, cubic).
    Parameters: 
        field (np.array): quantity to interpolate, shape:(days, lvl, elem)
        xx0, yy0 (np.array): Coordinates of the original grid, shape: (elem,)
        XX1, YY1 (np.array): Coordinates of the target grid, shape: (ny, nx) or (ny, nx), 
        days (int): Last day to interpolate to starting from day=0
        lvls (int): Number of Levels in z-direction to analyze. Starting from lvl=0.
        method (str): Interpolation method (nearest, linear, cubic)
    Returns:
        u_interp (np.array): Interpolated quantity at target grid, shape:(day, ny, nx) """


    if isinstance(field, xr.DataArray) and 'elem' in field.dims:
        field = field.isel(elem=slice(None, len(yy0)))

    # this asumes shape is days, lvl, elem
    elif not isinstance(field, xr.DataArray) and field.size > xx0.size:
        field = field[:, :, :len(yy0)]

    #- Parameters
    ny = XX1.shape[0]
    nx = XX1.shape[1]
    field_interp = np.zeros(shape=(days, ny, nx, lvls))
    
    #- Interpolation
    for day in tqdm(range(days), desc='Interpolating days', leave=False):
        for lvl in range(lvls):
            field_interp[day,:,:, lvl] = griddata(points=(xx0, yy0), 
                                                  values=field[day, lvl, :], 
                                                  xi=(XX1, YY1),
                                                  method=method)
        
    return field_interp



def interpolate_to_grid_fast(field, xx0, yy0, xx1, yy1, days, lvls, method):
    """
    Description: 
        Interpolates field from a grid of xx0, yy0 coordinates to a target grid of XX1, YY1 coordinates
        using a specified method (nearest, linear, cubic).
    Parameters: 
        field (np.array): quantity to interpolate, shape:(days, lvl, elem)
        xx0, yy0 (np.array): Coordinates of the original grid, shape: (elem,)
        XX1, YY1 (np.array): Coordinates of the target grid, shape: (ny, nx) or (ny, nx), 
        days (int): Last day to interpolate to starting from day=0
        lvls (int): Number of Levels in z-direction to analyze. Starting from lvl=0.
        method (str): Interpolation method (nearest, linear, cubic)
    Returns:
        u_interp (np.array): Interpolated quantity at target grid, shape:(day, ny, nx)
    """


    if isinstance(field, xr.DataArray) and 'elem' in field.dims:
        field = field.isel(elem=slice(None, len(yy0)))

    # this asumes shape is days, lvl, elem
    elif not isinstance(field, xr.DataArray) and field.shape[2] > xx0.size:
        field = field[:, :, :len(yy0)]

    #- Parameters
    ny = yy1.shape[0]
    nx = xx1.shape[1]
    field_interp = np.zeros(shape=(days, ny, nx, lvls))
    mesh1 = np.vstack((xx0, yy0)).T
    mesh2 = np.vstack((xx1.ravel(), yy1.ravel())).T
    print(mesh1)
    print(mesh2)
    tri = Delaunay(mesh1)
    
    #- Interpolation
    for day in tqdm(range(days), desc='Interpolating days', leave=False):
        for lvl in range(lvls):
            interpolator = CloughTocher2DInterpolator(tri, field[day, lvl, :])
            field_interp[day, :, :, lvl] = interpolator(mesh2).reshape((ny, nx))
        
    return field_interp


### BELLOW THIS I'M TESTING ###



def interp2d_np(field, mesh_triangulation, xx1, yy1):
    interpolator = CloughTocher2DInterpolator(mesh_triangulation, field)
    mesh2 = np.vstack((zz1.ravel(), yy1.ravel())).T.shape
    field_interp = interpolator(mesh_2)
    

def interpolate_to_grid_day(u, xx0, yy0, XX1, YY1, lvls, method):
    u_interp = np.zeros(shape=(ny, nx, lvls))
    for lvl in range(lvls):
        u_interp[:,:, lvl] = griddata(points=(xx0, yy0), 
                               values=u[lvl, :], 
                               xi=(XX1, YY1),
                               method=method
                                )
    return u_interp


def interpolate_to_grid_mp(u, xx0, yy0, XX1, YY1, days, lvls, method, n_process=2):
    """
    Description: 
        Interpolates u from a grid of xx0, yy0 coordinates to a target grid of XX1, YY1 coordinates
        using a specified method (nearest, linear, cubic).
    Parameters: 
        u (np.array): quantity to interpolate, shape:(days, lvl, elem)
        xx0, yy0 (np.array): Coordinates of the original grid, shape: (elem,)
        XX1, YY1 (np.array): Coordinates of the target grid, shape: (ny, nx) or (ny, nx), 
        days (int): Last day to interpolate to starting from day=0
        lvls (int): Number of Levels in z-direction to analyze. Starting from lvl=0.
        method (str): Interpolation method (nearest, linear, cubic)
    Returns:
        field_interp (np.array): Interpolated quantity at target grid, shape:(day, ny, nx)
    """

    #- Parameters
    ny = XX1.shape[0]
    nx = XX1.shape[1]
    u_interp = np.zeros(shape=(days, ny, nx, lvls))

    def interpolate_day(day):
        u_day = u[day]
        u_day_interp = np.zeros(shape=(ny, nx, lvls))
        for lvl in range(lvls):
            u_day_interp[:,:, lvl] = griddata(points=(xx0, yy0), 
                                   values=u_day[lvl, :], 
                                   xi=(XX1, YY1),
                                   method=method
                                    )
        return u_day_interp
    
    #- Interpolation
    with Pool(n_process) as p:
        result = p.starmap(interpolate_day, tqdm(range(days), total=days), chunksize=1)
        
    return result
