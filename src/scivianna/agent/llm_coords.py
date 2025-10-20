"""This file contains the variables used to call the LLM: 

-   LLM_MODEL_ID: Identifier for the specific large language model being used.
-   LLM_API_BASE: Base URL endpoint for the LLM's API service.
-   LLM_API_KEY: Authentication key used to access the LLM API, required for authorization and usage tracking.

This file can be overwriten to hard write the values.
"""
import os

def get_env_variable(var_name: str) -> str:
    """Retrieves an environment variable with error if it does not exist.

    Parameters
    ----------
    var_name : str
        Name of the environment variable

    Returns
    -------
    str
        Value of the environment variable or default value

    Raises
    ------
    ValueError
        If the variable is missing
    """
    try:
        return os.environ[var_name]
    except KeyError:
        raise ValueError(f"Environment variable '{var_name}' not found.")


llm_model_id = get_env_variable("LLM_MODEL_ID")
llm_api_base = get_env_variable("LLM_API_BASE")
llm_api_key = get_env_variable("LLM_API_KEY")
