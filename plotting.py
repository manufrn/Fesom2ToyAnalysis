import matplotlib.pyplot as plt
import xarray as xr


def plot_2d_field_triangular(field, x, y, cmap=None, cbar_label=None, robust=False, soufflet=False, **kwargs):
    '''
    Plots a 2d field defined over mesh elements or nodes and returns the Figure and Axes
    objects for further customization. Recommended to add plt.show() after calling this
    function. Only tested in Soufflet and double gyre meshes. 

    Parametres
    ----------
    field : xr.DataArray or array_like
        Defines a 2d field over mesh elements or nodes. So it actually is a 1d array.

    x, y : array_like 
        x and ycoordinates for the nodes or the centroids of the elements. Computed 
        through get_mesh_coordinates() from data_loader.py. Important to pass the
        correct coordinates (either for nodes or elements) depending on where the 
        variable is defined.
    cmap: str, optional
        Colormap to be used.
    cbar_label: str, optional
        Label of the colorbar.
    soufflet : bool
        Set to True if the data is form a Soufflet toy model run. This ensures that the
        periodicity of the mesh doesn't distort the plots. This asumes that the coordinate 
        arrays for the elements were loaded using the function get_mesh_coordinates from
        plotting.py. See the comments therein for a detailed explanation. 

    Returns
    -------
    fig : Figure
    ax : Axes

    '''

    if soufflet:
        # remove westernmost triangles if field is defined over elements (see data_loader.py)
        if isinstance(field, xr.DataArray) and 'elem' in field.dims:
            field = field[:len(y)]

        # hopefully the same as above if field is not dataarray, but less obvious what is going on
        elif field.size > x.size:
            field = field[:len(y)]
    
    if robust:
        vmin = np.quantile(field, 0.01)
        vmax = np.quantile(field, 0.99)
        if np.sign(vmin) != np.sign(vmax):
            if -vmin > vmax:
                vmax = -vmin
            else:
                vmin = -vmax
        extend = 'both'
        
    else:
        extend = 'neither'
    
    fig, ax = plt.subplots()
    if robust:
        im = ax.tripcolor(x, y, field, shading='flat', cmap=cmap, vmin=vmin, vmax=vmax, **kwargs)
    else:
        im = ax.tripcolor(x, y, field, shading='flat', cmap=cmap, **kwargs)
    cbar = fig.colorbar(im, shrink=0.9, label=cbar_label, extend=extend)
    ax.set_xlabel(r'Longitude [$^{\circ}$]')
    ax.set_ylabel(r'Latitude [$^{\circ}$]')

    ax.set_xlim(x.min(), x.max())
    ax.set_ylim(y.min(), y.max())
    
    ax.set_aspect('equal')
    
    return fig, ax


def plot_2d_field_interpolated(field, xx, yy, cmap=None, cbar_label=None):
    fig, ax = plt.subplots()
    im = ax.pcolormesh(xx, yy, field)
    cbar = fig.colorbar(im, shrink=0.9, label=cbar_label)
    ax.set_xlabel(r'Longitude ($^{\circ}$)')
    ax.set_ylabel(r'Latitude ($^{\circ}$)')

    ax.set_xlim(xx.min(), xx.max())
    ax.set_ylim(yy.min(), yy.max())

    for axis in ['top','bottom','left','right']:
        ax.spines[axis].set_linewidth(1.1)
        
    ax.set_aspect('equal')

    return fig, ax 


def plot_vertical_profile(profile, depth=None):
    fig, ax = plt.subplots(figsize=(4.8, 6.4))
    if isinstance(profile, xr.DataArray) and 'nz1' or 'nz' in profile.dims:
        if 'nz' in profile.dims:
            y = 'nz'
        elif 'nz1' in profile.dims:
            y = 'nz1'
        profile.plot.line(ax=ax, y=y, _labels=False)

    elif depth is not None:
        ax.plot(profile, depth)

    else: 
        raise ValueError('If profile is not a DataArray defining a vertical\
                         profile, "depth" must be provided')
    ax.invert_yaxis()
    ax.set_ylabel('Depth [m]')

    return fig, ax


def plot_mutiple_vertical_diagnostics(list_ds, labels, coefs=[1e2, 1e5, 1e9], legend_title=None, colors=None):
    var = ['eke', 'w_rms', 'buoy_flux']
    coefs_dict = dict(zip(var, coefs))
    
    fig, axs = plt.subplots(1, 3, figsize=(4.8*1.8, 6.4), sharey=True)

    for v, ax in zip(var, axs):
    
        if v in ['eke', 'buoy_flux']: 
            y_var = 'nz1'
        
        else: 
            y_var = 'nz'
        
        for i, (ds, label) in enumerate(zip(list_ds, labels)):
            if colors is None:
                (coefs_dict[v]*ds[v]).plot.line(ax=ax, y=y_var, _labels=False, label=label, lw=1.4)
            else:
                (coefs_dict[v]*ds[v]).plot.line(ax=ax, y=y_var, _labels=False, label=label, color=colors[i], lw=1.4)

        ax.set_ylim(4000, 0)

    
    axs[0].set_ylabel('Depth [m]')

    axs[0].set_title('Mean EKE')
    axs[1].set_title(r'${w}_{rms}$')
    axs[2].set_title(r"$\overline{w' b'}$")

    exps = ["{:e}".format(coef).split('+')[1].lstrip('0') for coef in coefs]
    axs[0].set_xlabel(rf'$10^{{{exps[0]}}}$ m$^{{2}}$ s$^{{-2}}$')
    axs[1].set_xlabel(rf'$10^{{{exps[1]}}}$ m s$^{{-1}}$')
    axs[2].set_xlabel(rf'$10^{{{exps[2]}}}$ m$^{{2}}$ s$^{{-3}}$')


    axs[0].legend(title=legend_title, 
                  prop={'family': 'monospace', 'size': 10})
    
    return fig, axs
    