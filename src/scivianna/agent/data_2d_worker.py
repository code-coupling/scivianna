
import numpy as np
from scivianna.data import Data2D

class Data2DWorker:
    """Worker that receives a Data2D object and works with it. """

    def __init__(self, data2d:Data2D):
        """Worker that receives a Data2D object and works with it. 

        Parameters
        ----------
        data2d : Data2D
            Data class containing geometrical properties
        """
        self.data2d = data2d
        self.data2d_save = data2d.copy()

    def check_valid(self,):
        """Check if the Data2D is valid

        Raises
        ------
        AssertionError
            Current Data2D is not valid
        """
        self.data2d.check_valid()

    def get_values(self,) -> np.ndarray:
        """Returns the value per 2D cell of the geometry

        Returns
        -------
        np.ndarray
            Numpy array with the value per cell
        """
        return self.data2d.cell_values
    
    def set_alpha(self, alphas:np.ndarray):
        """Sets the cells opacity values, expects a numpy array of integers between 0 and 255

        Parameters
        ----------
        alphas : np.ndarray
            opacities values

        Raises
        ------
        AssertionError
            Provided alphas array is not valid
        """
        assert type(alphas) == np.ndarray, f"A numpy array is expected, type found {type(alphas)}."
        assert len(alphas.shape) == 1, f"A 1D numpy array is expected, shape found {alphas.shape}."
        assert alphas.shape[0] == len(self.data2d.cell_colors), f"We expect the same number of elements as in self.data2d.cell_colors, received size {alphas.shape[0]} instead of {len(self.data2d.cell_colors)}."
        assert alphas.max() <= 255, f"The values must be lower than 255, found in array {alphas.max()}."
        assert alphas.min() >= 0, f"The values must be greater than 0, found in array {alphas.min()}."

        colors = np.array(self.data2d.cell_colors)
        colors[:, -1] = alphas.astype(int)

        self.data2d.cell_colors = colors.tolist()

    def reset(self,):
        """Returns to the data2d provided in the initialization
        """
        self.data2d = self.data2d_save.copy()


if __name__ == "__main__":
    from pathlib import Path

    # Field example
    import scivianna
    from scivianna.constants import GEOMETRY, X, Y
    from scivianna.interface.med_interface import MEDInterface
    from scivianna.slave import set_colors_list
    from scivianna.data import Data2D
    from scivianna.agent.data_2d_worker import Data2DWorker

    med = MEDInterface()
    med.read_file(
        str(Path(scivianna.__file__).parent / "default_jdd" / "power.med"),
        GEOMETRY,
    )
    data_2d:Data2D
    data_2d, _ = med.compute_2D_data(
        X,
        Y, 
        0, 1, 0, 1, 0, 0, # values not used
        0., 
        None,
        {}
    )
    set_colors_list(data_2d, med, "INTEGRATED_POWER", "viridis", False, {})

    worker = Data2DWorker(data_2d)

    worker.set_alpha(np.ones((len(data_2d.cell_colors)))*0.5)