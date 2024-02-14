import pandas as pd

def dictionaries_to_df(dictionaries):
    """Turn list of dictionaries into a pandas dataframe.
    
    Parameters:
    -----------
    dictionaries: list
        List of dictionaries.

    Returns:
    --------
    df: pandas dataframe
        A pandas dataframe
    """
    df = pd.concat(
        [pd.DataFrame(dictionaries[idx], index=[idx]) for idx in range(len(dictionaries))]
    )
    return df