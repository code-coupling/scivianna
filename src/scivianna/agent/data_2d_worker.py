
from pathlib import Path
import os
import numpy as np
from scivianna.data import Data2D
from smolagents import tool, Tool, CodeAgent, OpenAIServerModel

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

class FinalAnswerTool(Tool):
    name = "final_answer"
    description = """Return only the code (which must be self-contained) allowing the user to re-execute it to obtain the answer to their question. If the code is OK and answers the user's question, return True to code_is_ok."""
    inputs = {
        "code_is_ok": {"type": "boolean", "description": "If the code is OK and answers the user's question, return True."},
        "code": {"type": "string", "description": "Code to answer to the user problem."},
    }
    output_type = "object"
    
    def forward(
        self,
        code_is_ok: bool,
        code: str
    ) -> dict[bool, str]:
        """
        Code to the given problem.
        """
        return {"code_is_ok": code_is_ok, "code": code}

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
        self.data2d_save = data2d.copy()

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

        with open(Path(__file__).parent / "instructions.md", "r") as f:
            instructions = f.read()

        self.smoll_agent = CodeAgent(
                        tools=[FinalAnswerTool(), check_valid, get_values, set_alpha, reset],  # List of tools available to the agent
                        model=self.aiServer, 
                        additional_authorized_imports=["numpy"],
                        verbosity_level=2,  # Show detailed agent reasoning
                        instructions=instructions,
                        use_structured_outputs_internally=True,
                        planning_interval=None)
    
    def __call__(self, question, reset=False, images=[], max_steps=15, additional_args={}):

        agent_output = self.smoll_agent.run(question,
                                            reset=reset,
                                            images=images,
                                            max_steps=max_steps,
                                            additional_args=additional_args)

        try:
            return agent_output['code_is_ok'], agent_output['code']
        except:
            print("agent fail!!!")
            agent_output = {"code_is_ok":False, "code":""}

    def has_changed(self,) -> bool:
        """Tells if the data_2d was changed by the agent

        Returns
        -------
        bool
            data_2d changed
        """
        if not np.testing.assert_equal(np.array(self.data2d.cell_colors), np.array(self.data2d_save.cell_colors)):
            return True
        if not np.testing.assert_equal(np.array(self.data2d.cell_ids), np.array(self.data2d_save.cell_ids)):
            return True
        if not np.testing.assert_equal(np.array(self.data2d.cell_values), np.array(self.data2d_save.cell_values)):
            return True

        return False



if __name__ == "__main__":
    from pathlib import Path

    # Field example
    import scivianna
    from scivianna.constants import GEOMETRY, X, Y
    from scivianna.interface.med_interface import MEDInterface
    from scivianna.slave import set_colors_list
    from scivianna.data import Data2D
    from scivianna.agent.data_2d_worker import Data2DWorker
    from scivianna.plotter_2d.polygon.matplotlib import Matplotlib2DPolygonPlotter

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

    win = 0
    ag_codes = []
    for i in range(10):
        dw = Data2DWorker(data_2d)
        code_is_ok, code = dw("highlight the highest value cell, hide zero values, dim the rest")
        ag_codes.append((code_is_ok, code))
        if code_is_ok:
            win +=1

    print(f"ratio win: {win*10}%")

    for code_is_ok, code in ag_codes:
        print(f"agent_output\n - share_code_is_ok: {code_is_ok}\n - code \n'''\n{code}\n'''")

    """     data_2d est maintenant parfait
    """

    plotter = Matplotlib2DPolygonPlotter()
    plotter.plot_2d_frame(dw.data2d)
    plotter.figure.savefig("my_plot.png")
