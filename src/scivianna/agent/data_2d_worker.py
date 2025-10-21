
from pathlib import Path
import numpy as np
import numpy
from smolagents import tool, Tool, CodeAgent, OpenAIServerModel, ToolCallingAgent, PythonInterpreterTool
from smolagents.utils import parse_code_blobs

from scivianna.data import Data2D
from scivianna.agent.llm_coords import llm_api_base, llm_api_key, llm_model_id
from smolagents.models import (
    CODEAGENT_RESPONSE_FORMAT,
    ChatMessage,
    ChatMessageStreamDelta,
    ChatMessageToolCall,
    MessageRole,
    Model,
    agglomerate_stream_deltas,
    parse_json_if_needed,
)

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

    # try:
    #     int(final_answer)
    #     return True
    # except ValueError:
    #     return False

class Data2DWorker:
    """Worker that receives a Data2D object and works with it. """

    def __init__(self, data2d:Data2D):
        """Worker that receives a Data2D object and works with it. 

        Parameters
        ----------
        data2d : Data2D
            Data class containing geometrical properties
        """
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
            self.check_valid()

        @tool
        def get_values() -> np.ndarray:
            """Returns the value per 2D cell of the geometry

            Returns
            -------
            np.ndarray
                Numpy array with the value per cell
            """
            return self.get_values()
        
        @tool
        def set_alphas(alphas:np.ndarray) -> bool:
            """
            Sets the cells opacity values, expects a numpy array of integers between 0 and 255. return True if it's ok.

            Args:
                alphas : np.ndarray, Opacity values     

            Returns
            -------
            bool
                True if the given array is ok            
            """
            return self.set_alphas(alphas)
        
        @tool
        def get_colors() -> np.ndarray:
            """Returns the color per 2D cell of the geometry. 
            The returned object is a np.ndarray of shape (cell_count, 4), with values ranging from 0 to 255.

            Returns
            -------
            np.ndarray
                Numpy array with the value per cell
            """
            return self.get_colors()
        
        @tool
        def set_colors(colors:np.ndarray) -> bool:
            """Sets the cells color values, expects a numpy array of integers between 0 and 255 of shape (cell_count, 4). return True if it's ok.

            Args:
            colors : np.ndarray, np array containing the new per cell colors. expects a numpy array of integers between 0 and 255 of shape (cell_count, 4).

            Returns
            -------
            bool
                True if the given array is ok
            """
            return self.set_colors(colors)
        
        @tool
        def reset():
            """Returns to the data2d provided in the initialization
            """
            return self.reset()
        
        @tool
        def get_numpy() -> numpy:
            """Returns the numpy module
            """
            return self.get_numpy()
            
        @tool
        def execute_code(code_to_execute:str) -> bool:
            """Applies a code string to the current object. Used to repeat an already processed prompt.

            Args:
            code_to_execute : Code to execute in the Data2DWorker.

            Returns:
            bool : Code is valid.
            str : comment on why the code is not valid

            """
            return self.execute_code(code_to_execute)

        print(f"Building AI server with model {llm_model_id}\n")

        self.aiServer = OpenAIServerModel(model_id = llm_model_id,
                                          api_base = llm_api_base,
                                          api_key = llm_api_key)

        with open(Path(__file__).parent / "instructions.md", "r") as f:
            instructions = f.read()

        # self.smoll_agent = CodeAgent(
        #                 tools=[FinalAnswerTool(), check_valid, get_values, set_alpha, reset, get_numpy],  # List of tools available to the agent
        self.smoll_agent = CodeAgent(
                        tools=[execute_code, 
                            #    check_valid, get_values, set_alphas, get_colors, set_colors, reset, get_numpy
                               ],  # List of tools available to the agent
                        # final_answer_checks=[code_is_ok],
                        model=self.aiServer, 
                        additional_authorized_imports=["numpy"],
                        verbosity_level=2,  # Show detailed agent reasoning
                        instructions=instructions,
                        use_structured_outputs_internally=True,
                        planning_interval=None)
        
        self.python_executor = self.smoll_agent.python_executor

        # self.smoll_agent = ToolCallingAgent(
        #                 tools=[PythonInterpreterTool(authorized_imports = [check_valid, get_values, set_alpha, reset, get_numpy, "numpy"]), FinalAnswerTool()],  # List of tools available to the agent
        #                 model=self.aiServer, 
        #                 verbosity_level=2,  # Show detailed agent reasoning
        #                 instructions=instructions,
        #                 planning_interval=None)        

    def extract_exectute_code(self, text:str):
        if not "execute_code" in text:
            return
        
        last_exec = 'execute_code("""' + text.split('execute_code("""')[-1]
        last_exec = text.split('""")')[0] + '""")'

        return last_exec
    
    def __call__(self, question, reset=False, images=[], max_steps=15, additional_args={}):
        self.executed_code = None

        input_messages = question + self.smoll_agent.instructions
        self.smoll_agent.python_executor.send_tools(self.smoll_agent.tools)
        step = 0

        while self.executed_code is None and step < max_steps:
            print(f"Executing step {step}")
            chat_message: ChatMessage = self.smoll_agent.model.generate(
                [ChatMessage(
                    role=MessageRole.ASSISTANT,
                    content=[
                        {
                            "type": "text",
                            "text": input_messages
                        }
                    ],
                ),]
            )
            output_text = chat_message.content
            
            code = self.extract_exectute_code(output_text)

            if code is None:
                input_messages += 'Returned value not containing a code block respecting the format execute_code(""" your code here """)'

            else:
                try:
                    print("Executing code :\n\n\n ", code)
                    execution_output = self.smoll_agent.python_executor.__call__(code)
                except Exception as e:
                    execution_output = e
                    print(e)

                input_messages += f"\n PAST ANSWER \n{execution_output} "
            step += 1

        if self.executed_code is None:
            return False, ""
        
        print("Success")
        return True, self.executed_code
        # agent_output = self.smoll_agent.run(question,
        #                                     reset=reset,
        #                                     images=images,
        #                                     max_steps=max_steps,
        #                                     additional_args=additional_args)

        # try:
        #     print("OUTPUT", agent_output)
        #     return agent_output['code_is_ok'], agent_output['code']
        # except:
        #     print("agent fail!!!")
        #     agent_output = {"code_is_ok":False, "code":""}
        #     return agent_output['code_is_ok'], agent_output['code']

    def has_changed(self,) -> bool:
        """Tells if the data_2d was changed by the agent

        Returns
        -------
        bool
            data_2d changed
        """
        try:
            np.testing.assert_equal(np.array(self.data2d.cell_colors), np.array(self.data2d_save.cell_colors))
            np.testing.assert_equal(np.array(self.data2d.cell_ids), np.array(self.data2d_save.cell_ids))
            np.testing.assert_equal(np.array(self.data2d.cell_values), np.array(self.data2d_save.cell_values))
        except AssertionError:
            return True

        return False

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
        return np.array(self.data2d.cell_values)
    
    def get_colors(self,) -> np.ndarray:
        """Returns the color per 2D cell of the geometry. 
        The returned object is a np.ndarray of shape (cell_count, 4), with values ranging from 0 to 255.

        Returns
        -------
        np.ndarray
            Numpy array with the value per cell
        """
        return np.array(self.data2d.cell_colors)
    
    def set_colors(self, colors:np.ndarray) -> bool:
        """Sets the cells color values, expects a numpy array of integers between 0 and 255 of shape (cell_count, 4). return True if it's ok.

        Parameters
        ----------
        colors : np.ndarray
            np array containing the new per cell colors. expects a numpy array of integers between 0 and 255 of shape (cell_count, 4).

        Returns
        -------
        bool
            True if the given array is ok
        """
        assert type(colors) in (np.ndarray, list), f"A numpy array is expected, type found {type(colors)}."
        colors = np.array(colors)
        assert len(colors.shape) == 2, f"A 2D numpy array is expected, shape found {colors.shape}."
        assert colors.shape == np.array(self.data2d.cell_colors).shape, f"We expect the same number of elements as in self.data2d.cell_colors, received shape {colors.shape} instead of {self.data2d.cell_colors}."
        assert colors.flatten().max() <= 255, f"The values must be lower than 255, found in array {colors.flatten().max()}."
        assert colors.flatten().min() >= 0, f"The values must be greater than 0, found in array {colors.flatten().min()}."

        self.data2d.cell_colors = colors.tolist()

        return True
    
    def set_alphas(self, alphas:np.ndarray) -> bool:
        """
        Sets the cells opacity values, expects a numpy array of integers between 0 and 255. return True if it's ok.

        Parameters
        ----------
        alphas : np.ndarray
            Opacity values     

        Returns
        -------
        bool
            True if the given array is ok            
        """
        assert type(alphas) in (np.ndarray, list), f"A numpy array is expected, type found {type(alphas)}."
        alphas = np.array(alphas)
        assert len(alphas.shape) == 1, f"A 1D numpy array is expected, shape found {alphas.shape}."
        assert alphas.shape[0] == len(self.data2d.cell_colors), f"We expect the same number of elements as in self.data2d.cell_colors, received size {alphas.shape[0]} instead of {len(self.data2d.cell_colors)}."
        assert alphas.max() <= 255, f"The values must be lower than 255, found in array {alphas.max()}."
        assert alphas.min() >= 0, f"The values must be greater than 0, found in array {alphas.min()}."

        colors = np.array(self.data2d.cell_colors)
        colors[:, -1] = alphas.astype(int)

        self.data2d.cell_colors = colors.tolist()

        return True

    def reset(self,):
        """Returns to the data2d provided in the initialization
        """
        self.data2d = self.data2d_save.copy()
    
    def get_numpy(self,):
        """Returns the numpy module
        """
        return np
    
    def execute_code(self, code_to_execute:str):
        """Applies a code string to the current object. Used to repeat an already processed prompt.

        Parameters
        ----------
        code_to_execute : str
            Code to execute in the Data2DWorker
        """
        code_to_execute = code_to_execute.replace("import numpy as np", "np = get_numpy()")
        context_string = "\n".join(f"{e} = self.{e}" for e in [
            "check_valid", 
            "get_values", 
            "set_alphas", 
            "get_colors", 
            "set_colors", 
            "reset", 
            "get_numpy"
            ])
        exec(context_string+"\n"+code_to_execute)

        try:
            self.check_valid()
        except AssertionError as e:
            return False, f"The code was executed, but the resulting Data2D is not valid. Following problem found {e}."

        if self.has_changed():
            self.executed_code = context_string+"\n"+code_to_execute
            return True, "Success"
        else:
            return False, "The code was executed properly but did not change the Data2D."


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

    if False:
        win = 0
        ag_codes = []
        for i in range(10):
            dw = Data2DWorker(data_2d)
            code_is_ok, code = dw("highlight the highest value cell, hide zero values, dim the rest")
            # code_is_ok, code = dw("color in red the highest value cell.")
            ag_codes.append((code_is_ok, code))
            if code_is_ok:
                win +=1

        for code_is_ok, code in ag_codes:
            print(f"agent_output\n - share_code_is_ok: {code_is_ok}\n - code \n'''\n{code}\n'''")

        print(f"ratio win: {win*10}%")

    dw = Data2DWorker(data_2d)
    code_is_ok, code = dw("highlight the highest value cell, hide zero values, dim the rest")
    plotter = Matplotlib2DPolygonPlotter()
    plotter.plot_2d_frame(dw.data2d)
    plotter.figure.savefig("my_plot.png")
