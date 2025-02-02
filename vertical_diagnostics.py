import numpy as np
import xarray as xr


def RMS_vertical_velocity(w, nod_area):
    '''
    Compute the average RMS vertical velocity anomaly for the given
    w DataArray. 

    Parameters
    ----------
    w : DataArray
        3d DataArray with dimensions ['time', 'nz1', 'nod2']. The
        time extent has already been selected 
    nod_area : array_like
        1d array containing the area of each node. Obtained from the
        mesh_diag output file. For the Soufflet configuration all 
        depth layers have the same node areas, so the nod_area variable
        from mesh_diag must be collapsed to 

    Returns
    -------
    DataArray
        Average RMS vertical velocity anomaly for each layer. Dimensions
        of ['nz1'].

    '''
    w_squared_weighted = (w**2).weighted(nod_area).mean('nod2')
    w_rms = np.sqrt(w_squared_weighted.mean('time'))

    return w_rms


def mean_EKE(u, v, elem_area):
    '''
    Compute the mean Eddy Kinetic Energy vertical profile for given 
    velocity inputs. 

    Parameters
    ----------
    u : DataArray
        Zonal velocity DataArray with dimensions ['time', 'nz1', 'elem']. 
    v : DataArray
        Meridional velocity DataArray. Same dimensions and time range as
        u. 
    elem_area : array_like
        1d array containing the area of each element. Obtained from the
        mesh_diag output file.

    Returns
    -------
    DataArray
    '''
    
    u_mean = u.mean('time')
    v_mean = v.mean('time')
    eke = ((u - u_mean) ** 2 + (v - v_mean) ** 2 ) / 2
    eke_weighted = eke.weighted(elem_area).mean('elem')
    eke_mean = eke_weighted.mean('time')

    return eke_mean


def mean_buyoancy(w, temp, nod_area, alpha=0.00025, density_0=1030.0, temp_0=10.0):
    '''
    Compute the mean turbulent buoyancy flux profile for given the temperature 
    and vertical velocity.

    Parameters
    ----------
    temp : DataArray
       3d DataArray of temperature with dimensions ['time', 'nz1', 'nod2']. 
    w : DataArray
       3d DataArray of vertical velocity with dimensions ['time', 'nz', 'nod2'].
    nod_area : array_like
        1d array containing the area of each node. Obtained from the
        mesh_diag output file. For the Soufflet configuration all 
        depth layers have the same node areas, so you can define nod_area
        as the nod_area for the first depthnod_area variable
        from mesh_diag 
    alpha : float, default=0.00025
        Thermal coefficient used in the calculation of buoyancy from temperature.
    density_0 : float, default=1030.0
        Reference density.
    
    Returns
    -------
    DataArray
        Mean turbulent buoyancy flux profile for the whole domain, time averaged
        for the complete time period that the input variables cover. 
        
    ''' 

    temp_mean = temp.mean('time')
    g = -9.81

    buoy_mean = - g * alpha * (temp_mean - temp_0) + g
    buoy = -g * alpha * (temp - temp_0) + g
    buoy_dash = buoy - buoy_mean

    w_dash = w - w.mean('time') # vertical velocity anomaly

    # average w_dash into vertical levels where temp is defined, rename z coord
    w_dash = w_dash.interp(nz=temp.nz1.data, method='linear') 
    w_dash = w_dash.rename(dict(nz='nz1'))
    
    # compute area weighted mean and time mean of buoyancy flux (w'·b')
    buoy_flux = w_dash * buoy_dash
    buoy_flux = buoy_flux.weighted(nod_area).mean('nod2')
    buoy_flux = buoy_flux.mean('time')

    return buoy_flux
