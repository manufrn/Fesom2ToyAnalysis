import numpy as np
import xarray as xr
from matplotlib.tri import Triangulation
from pathlib import Path


def get_triangulation(mesh_path, soufflet=False):  
    nodes = np.loadtxt(mesh_path + 'nod2d.out', skiprows=1, usecols=[1, 2]).T #2d array of node coords
    lon_nodes, lat_nodes = nodes 
    
    elems = np.loadtxt(mesh_path + 'elem2d.out', skiprows=1) - 1


    if soufflet:
        # works for me, may have to be addapted depending on mesh generation strategy? 
        ny = len(lat_nodes[:np.where(lat_nodes == lat_nodes.max())[0][0]+1])
        nx = len(lon_nodes[::ny]) + 1 # in case we need it later
        last_elems_idx = len(elems) - (ny * 2 - 2)
        elems = elems[:last_elems_idx]

    tri = Triangulation(lon_nodes, lat_nodes, elems)
    return tri


def get_mesh_coordinates(mesh_path, soufflet=False):
    '''
    Returns arrays for the coordinates of the nodes and the elements of a Soufflet configuration FESOM2 mesh.
    The coordinates for the elements are taking directly from the nod2d.out file, and for the elements are 
    computed as the centroid of the triangle (defined in elem2d.out). Works nice for plotting the output in 
    lat-lon coordinates using tricolorp (see plotting.py). Don't even know if it would make sense with 
    properly unstructured grids. The lat lon variables in the mesh.diag file for the Soufflet runs have 
    confusing values for the soufflet run, that's why we need this function for the moment.

    Parameters
    ----------
    mesh_path : str
        Path to folder where nod2d.out and elem2d.out files for the mesh are located. 
    soufflet : bool
        Wheter the mesh file is for the Soufflet configuration. Needed to take into acount periodicty.

    Returns
    -------
    lon_nodes, lat_nodes : ndarray
        x and y coordinates for the mesh nodes. 
    lon_elems, lat_elems : ndarray
        x and y coordinates for the mesh elements as a 1d array. Computed as the centroid of the triangles.

    '''
    
    nodes = np.loadtxt(mesh_path + 'nod2d.out', skiprows=1, usecols=[1, 2]).T #2d array of node coords
    elems = np.loadtxt(mesh_path + 'elem2d.out', skiprows=1, dtype=int) 

    # compute coordinates of elements as centroid of triangle
    coords_elems = []
    for elem in elems:
        lon_nodes = nodes[0, elem - 1] 
        lat_nodes = nodes[1, elem - 1]
        lon_elem = lon_nodes.sum()/3
        lat_elem = lat_nodes.sum()/3
        coords_elems.append([lon_elem, lat_elem])
        
    lon_elems, lat_elems = np.asarray(coords_elems).T
    lon_nodes, lat_nodes = nodes 
     
    # The following adjustment is necessary for soufflet. In the elem2d.out file
    # the triangles that have either 1 or 2 nodes in the western limit of the channel
    # are defined using the indices for those nodes at the eastern limit. In reality,
    # for a 13.5 degree setup with 0.09 degrees resolution (20 km), the westernmost 
    # nodes are located at 13.41 degrees longitude, and two vertical rows of elements
    # conect those nodes with the first row of nodes at 0 degrees. This ensures the
    # zonal cyclicity. We need to get rid of those two last rows of elements to correctly 
    # plot using the maptlotlib tools. We loose that info, but the other option is adding
    # that westernmost row of nodes at 13.5 to calculate the centroids of those last two 
    # rows of elements, but it's not worth the hastle. It was enough figuring this out and
    # writing this 11 line comment :) 
    
    if soufflet:
        # works for me, may have to be addapted depending on mesh generation strategy? 
        ny = len(lat_nodes[:np.where(lat_nodes == lat_nodes.max())[0][0]+1])
        nx = len(lon_nodes[::ny]) + 1 # in case we need it later
        last_elems_idx = len(lat_elems) - (ny * 2 - 2)
        lon_elems, lat_elems = lon_elems[:last_elems_idx], lat_elems[:last_elems_idx]

    return lon_nodes, lat_nodes, lon_elems, lat_elems


def load_variable(data_path, variable, year_1=None, year_f=None, zerostonan=True):
    '''
    Loads a given variable from a results folder. Output is a xr.DataArray containing
    the years of simulation starting from year_1 up to year_f. If year_1 and year_f are
    not set, all the years present in data_path are returned.

    Parameters
    ----------
    data_path : str
        Path to results folder.
    variable : str
        Variable to load.
    year_1 : int, optional
        Initial year to load into the DataArray. Prior years won't be loaded.
    year_f : int, optional
        Initial year to load into the DataArray. Later years won't be loaded.
    zerostonan : bool, optional
        If True, zero value in the DataArray are set to np.nan. Useful to mask topography.

    Returns
    -------
    DataArray
        Contains selected years of variable.
    '''

    path = Path(data_path)
    file_list = list(path.glob(f'{variable}.*'))

    if year_1 is not None:
        file_list = [f for f in file_list if int(f.stem.split('.')[-1]) >= year_1]

    if year_f is not None:
        file_list = [f for f in file_list if int(f.stem.split('.')[-1]) <= year_f]
    
    ds = xr.open_mfdataset(file_list)

    if variable in ds.data_vars:
        dataarray = ds[variable]

    # had to do the following to make it easy working with diferent file names comming
    # from applying cdo but without changing the variable names.
    else:
        if len(ds.data_vars) == 1:
            dataarray = ds[list(ds.data_vars)[0]]
        else:
            raise KeyError("The selected files have more than one data variable and I don't know how to handle this.")

    if zerostonan:
        dataarray = dataarray.where(dataarray!=0)

    return dataarray


def get_mesh_diagnostics(data_path, variables=None):
    '''
    Get FESOM2 mesh diagnostics from fesom.mesh.diag.nc file.
    If a variable id string or list of variable ids is passed
    to the variables argument, the function returns a list. The
    respective diagnostics are numpy Arrays. 

    Parameters
    ----------
    data_path : str
        Path to results folder.
    
    variables : list, optional
        List of variables from the mesh_diag file to be returned.

    Returns
    -------
    xr.Dataset, list or xr.DataArray

    '''

    file_path = data_path + 'fesom.mesh.diag.nc' 
    mesh_diag = xr.open_dataset(file_path)

    if variables is not None:
        if isinstance(variables, str):
            output = mesh_diag[variables]

        elif isinstance(variables, (list, tuple)):
            output = []
            for var in variables:
                output.append(mesh_diag[var])

        else:
            raise ValueError("'variables' must be None, str, list or tuple")

    else:
        output = mesh_diag
        
    return output
