The data used to display the geometry in a 2D plot, coloring it, or feed a 1D plot are obtained through a slave using interfaces. 

All interfaces inherit from the class **GenericInterface** that provides the tools to understand the content available:
-   **read_file** : reads a file to get the content from
-   **get_labels** : returns the list of the available fields and results
-   **get_file_input_list** : returns the list of already read files for slave saving and copy

Based on the available data, the developer inherits its interface from one or several of the following classes:

-   **Geometry2D** : Provides a 2D slice and a value at every cell;
-   **ValueAtLocation** : Provides a value at a combination of location, cell number or material;
-   **Value1DAtLocation** : Provides 1D data at a combination of location, cell number or material;
-   **OverLine** : Provides the features to gather the data along a line;

-   **IcocoInterface** : The class implements some functions of the Icoco interface to update its values during a simulation
    -   **getInputMEDDoubleFieldTemplate** : returns the mesh in which the field is stored
    -   **setInputMEDDoubleField** : sets the new field data
    