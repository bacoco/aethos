"""
This file contains the following methods:

remove_columns_threshold
remove_rows_threshold
remove_duplicate_rows
remove_duplicate_columns
"""
import pandas as pd
from pyautoml.util import _function_input_validation


def remove_columns_threshold(threshold, **datasets):
    """
    Remove columns from the dataframe that have more than the threshold value of missing rows.
    Example: Remove columns where > 50% of the data is missing
    
    Args:
        threshold (int or float, optional): Threshold value between 0 and 1 that if the column
        has more than the specified threshold of missing values, it is removed. 
    
        Either the full data or training data plus testing data MUST be provided, not both.

        data {DataFrame}: Full dataset. Defaults to None.
        train_data {DataFrame}: Training dataset. Defaults to None.
        test_data {DataFrame}: Testing dataset. Defaults to None.
    
    Returns:
        Dataframe, *Dataframe: Transformed dataframe with rows with a missing values in a specific column are missing

        * Returns 2 Dataframes if Train and Test data is provided.
    """

    data = datasets.pop('data', None)
    train_data = datasets.pop('train_data', None)
    test_data = datasets.pop('test_data', None)

    if datasets:
        raise TypeError(f"Invalid parameters passed: {str(datasets)}")

    if not _function_input_validation(data, train_data, test_data):
        raise ValueError("Function input is incorrectly provided.")

    if data is not None:
        criteria_meeting_columns = data.columns[data.isnull().mean() < threshold]

        return data[criteria_meeting_columns]

    else:
        criteria_meeting_columns = train_data.columns(train_data.isnull().mean() < threshold)

        return train_data[criteria_meeting_columns], test_data[criteria_meeting_columns]

def remove_rows_threshold(threshold, **datasets):
    """
    Remove rows from the dataframe that have more than the threshold value of missing rows.
    Example: Remove rows where > 50% of the data is missing
    
    Args:
        threshold (int or float, optional): Threshold value between 0 and 1 that if the row
        has more than the specified threshold of missing values, it is removed. 
    
        Either the full data or training data plus testing data MUST be provided, not both.

        data {DataFrame}: Full dataset. Defaults to None.
        train_data {DataFrame}: Training dataset. Defaults to None.
        test_data {DataFrame}: Testing dataset. Defaults to None.
    
    Returns:
        Dataframe, *Dataframe: Transformed dataframe with rows with a missing values in a specific column are missing

        * Returns 2 Dataframes if Train and Test data is provided.
    """

    data = datasets.pop('data', None)
    train_data = datasets.pop('train_data', None)
    test_data = datasets.pop('test_data', None)

    if datasets:
        raise TypeError(f"Invalid parameters passed: {str(datasets)}")

    if not _function_input_validation(data, train_data, test_data):
        raise ValueError("Function input is incorrectly provided.")

    if data is not None:

        return data.dropna(thresh=round(data.shape[1] * threshold), axis=0)

    else:

        train_data = train_data.dropna(thresh=round(train_data.shape[1] * threshold), axis=0)
        test_data = test_data.dropna(thresh=round(test_data.shape[1] * threshold), axis=0)

        return train_data, test_data

def remove_duplicate_rows(list_of_cols=[], **datasets):
    """
    Removes rows that are exact duplicates of each other.
    
    Args:
        list_of_cols (list, optional): Columns to check if their values are duplicated. Defaults to [].
    
        Either the full data or training data plus testing data MUST be provided, not both.

        data {DataFrame}: Full dataset. Defaults to None.
        train_data {DataFrame}: Training dataset. Defaults to None.
        test_data {DataFrame}: Testing dataset. Defaults to None.
    
    Returns:
        Dataframe, *Dataframe: Transformed dataframe with rows with a missing values in a specific column are missing

        * Returns 2 Dataframes if Train and Test data is provided.
    """

    data = datasets.pop('data', None)
    train_data = datasets.pop('train_data', None)
    test_data = datasets.pop('test_data', None)

    if datasets:
        raise TypeError(f'Invalid parameters passed: {str(datasets)}')

    if not _function_input_validation(data, train_data, test_data):
        raise ValueError('Function input is incorrectly provided.')

    if data is not None:        
        return data.drop_duplicates(list_of_cols)

    else:
        train_data = train_data.drop_duplicates(list_of_cols)
        test_data = test_data.drop_duplicates(list_of_cols)

        return train_data, test_data

def remove_duplicate_columns(**datasets):
    """
    Removes columns whose values are exact duplicates of each other.
    
    Args:    
        Either the full data or training data plus testing data MUST be provided, not both.

        data {DataFrame}: Full dataset. Defaults to None.
        train_data {DataFrame}: Training dataset. Defaults to None.
        test_data {DataFrame}: Testing dataset. Defaults to None.
    
    Returns:
        Dataframe, *Dataframe: Transformed dataframe with rows with a missing values in a specific column are missing

        * Returns 2 Dataframes if Train and Test data is provided.
    """

    data = datasets.pop('data', None)
    train_data = datasets.pop('train_data', None)
    test_data = datasets.pop('test_data', None)

    if datasets:
        raise TypeError(f'Invalid parameters passed: {str(datasets)}')

    if not _function_input_validation(data, train_data, test_data):
        raise ValueError('Function input is incorrectly provided.')

    if data is not None:
        return data.T.drop_duplicates().T

    else:
        train_data = train_data.T.drop_duplicates().T
        test_data = test_data.T.drop_duplicates().T

        return train_data, test_data
