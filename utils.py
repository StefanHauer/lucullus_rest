"""Utility functions to perform easy tasks."""

import pandas as pd

def dictionaries_to_df(dictionaries):
    """Turn list of dictionaries into a pandas dataframe.

    Parameters:
    -----------
    dictionaries: list
        List of dictionaries.

    Returns:
    --------
    df_from_dict: pandas dataframe
        A pandas dataframe
    """
    df_from_dict = pd.concat(
        [pd.DataFrame(dictionaries[idx], index=[idx]) for idx in range(len(dictionaries))]
    )
    return df_from_dict
