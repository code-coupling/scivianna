#   Europe grid example

This example shows how to define a custom 2D geometry based on a Europe shapely polygons map. The following files are present:

-   **europe_grid.py** provides an example of how to make a class EuropeGridInterface that provides the visualizer polygons to display (applied to an Europe map) and how to associate the polygons (countries) to values.
-   **country_time_series.py** gives an example of result that associates a 1D value to a polygone/location to display in a 1D plot
-   **plot_api.py** plots an europe map as provided by the EuropeGridInterface in a .png file using the scivianna API.

![img](europe_grid_app.png)