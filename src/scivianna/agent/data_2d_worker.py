
import os
import numpy as np
from scivianna.data import Data2D
from smolagents import tool, CodeAgent, OpenAIServerModel

def get_env_variable(var_name: str) -> str:
    """
    Retrieves an environment variable with error if it does not exist.

    :param var_name: Name of the environment variable
    :return: Value of the environment variable or default value
    :raises ValueError: If the variable is missing
    """
    try:
        return os.environ[var_name]
    except KeyError:
        raise ValueError(f"Environment variable '{var_name}' not found.")

class Data2DWorker:
    """Worker that receives a Data2D object and works with it. """

    def __init__(self, data2d:Data2D):
        """Worker that receives a Data2D object and works with it. 

        Parameters
        ----------
        data2d : Data2D
            Data class containing geometrical properties
        """

        llm_model_id = get_env_variable("LLM_MODEL_ID")
        llm_api_base = get_env_variable("LLM_API_BASE")
        llm_api_key = get_env_variable("LLM_API_KEY")

        self.data2d = data2d.copy()
        # self.data2d_save = data2d.copy()

        @tool
        def check_valid():
            """Check if the Data2D is valid

            Raises
            ------
            AssertionError
                Current Data2D is not valid
            """
            self.data2d.check_valid()

        @tool
        def get_values() -> np.ndarray:
            """Returns the value per 2D cell of the geometry

            Returns
            -------
            np.ndarray
                Numpy array with the value per cell
            """
            return self.data2d.cell_values
        
        @tool
        def set_alpha(alphas:np.ndarray) -> bool:
            """
            Sets the cells opacity values, expects a numpy array of integers between 0 and 255. return True if it's ok.

            Args:
                alphas: opacity values                
            """
            assert type(alphas) == np.ndarray, f"A numpy array is expected, type found {type(alphas)}."
            assert len(alphas.shape) == 1, f"A 1D numpy array is expected, shape found {alphas.shape}."
            assert alphas.shape[0] == len(self.data2d.cell_colors), f"We expect the same number of elements as in self.data2d.cell_colors, received size {alphas.shape[0]} instead of {len(self.data2d.cell_colors)}."
            assert alphas.max() <= 255, f"The values must be lower than 255, found in array {alphas.max()}."
            assert alphas.min() >= 0, f"The values must be greater than 0, found in array {alphas.min()}."

            colors = np.array(self.data2d.cell_colors)
            colors[:, -1] = alphas.astype(int)

            self.data2d.cell_colors = colors.tolist()

            return True

        @tool
        def reset():
            """Returns to the data2d provided in the initialization
            """
            self.data2d = self.data2d_save.copy()
        
        self.aiServer = OpenAIServerModel(model_id = llm_model_id,
                                          api_base = llm_api_base,
                                          api_key = llm_api_key)

        # Initialize the agent with our retriever tool
        self.smollAg = CodeAgent(
                        tools=[check_valid, get_values, set_alpha, reset],  # List of tools available to the agent
                        model=self.aiServer, 
                        max_steps=5,  # Limit the number of reasoning steps
                        additional_authorized_imports=["numpy"],
                        verbosity_level=2,  # Show detailed agent reasoning
                        instructions=None, #"TO_DO -> détailler ce qu'on veux"
                        use_structured_outputs_internally=True,
                        planning_interval=None)
    
    def __call__(self, question, reset=False, images=[], max_steps=5, additional_args={}):

        agent_output = self.smollAg.run(question,
                                        reset=reset,
                                        images=images,
                                        max_steps=max_steps,
                                        additional_args=additional_args)
        print("agent_output", agent_output)


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

    dw = Data2DWorker(data_2d)
    dw("For test, run get_values function")
    dw("tu peux essayer de mettre une opacité nulle pour les valeus nulles?")