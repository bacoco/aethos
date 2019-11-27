import copy
import os
import re

import ipywidgets as widgets
import numpy as np
import pandas as pd
import pandas_profiling
from IPython import get_ipython
from IPython.display import display
from ipywidgets import Layout
from pandas.io.json import json_normalize
from pandas_summary import DataFrameSummary

import pyautoml
from pyautoml.config import shell
from pyautoml.reporting.report import Report
from pyautoml.util import (CLEANING_CHECKLIST, DATA_CHECKLIST,
                           ISSUES_CHECKLIST, MULTI_ANALYSIS_CHECKLIST,
                           PREPARATION_CHECKLIST, UNI_ANALYSIS_CHECKLIST,
                           _get_columns, _set_item, label_encoder, split_data)
from pyautoml.visualizations.visualize import *


class MethodBase(object):
    def __init__(self, x_train, x_test, split, target_field, target_mapping, report_name, test_split_percentage):

        self.x_train = x_train
        self.x_test = x_test
        self.split = split
        self.target_field = target_field
        self.target_mapping = target_mapping
        self.report_name = report_name
        self.test_split_percentage = test_split_percentage

        if split and x_test is None:
            # Generate train set and test set.
            self.x_train, self.x_test = split_data(
                self.x_train, test_split_percentage
            )
            self.x_train.reset_index(drop=True, inplace=True)
            self.x_test.reset_index(drop=True, inplace=True)

        if report_name is not None:
            self.report = Report(report_name)
            self.report_name = self.report.filename
        else:
            self.report = None

    def __repr__(self):

        if shell == "ZMQInteractiveShell":
            display(self.x_train.head())  # Hack for jupyter notebooks

            return ""

        else:
            return self.x_train.to_string()

    def __getitem__(self, column):

        try:
            return self.x_train[column]

        except Exception as e:
            raise AttributeError(e)

    def __setitem__(self, column, value):

        if not self.split:
            self.x_train[column] = value

            return self.x_train.head()
        else:
            x_train_length = self.x_train.shape[0]
            x_test_length = self.x_test.shape[0]

            if isinstance(value, list):
                ## If the number of entries in the list does not match the number of rows in the training or testing
                ## set raise a value error
                if len(value) != x_train_length and len(value) != x_test_length:
                    raise ValueError(
                        f"Length of list: {str(len(value))} does not equal the number rows as the training set or test set."
                    )

                self.x_train, self.x_test = _set_item(
                    self.x_train,
                    self.x_test,
                    column,
                    value,
                    x_train_length,
                    x_test_length,
                )

            elif isinstance(value, tuple):
                for data in value:
                    if len(data) != x_train_length and len(data) != x_test_length:
                        raise ValueError(
                            f"Length of list: {str(len(value))} does not equal the number rows as the training set or test set."
                        )

                    (
                        self.x_train,
                        self.x_test,
                    ) = _set_item(
                        self.x_train,
                        self.x_test,
                        column,
                        data,
                        x_train_length,
                        x_test_length,
                    )

            else:
                self.x_train[column] = value
                self.x_test[column] = value

            return self.x_train.head()

    def __getattr__(self, key):

        if key in self.__dict__:
            return getattr(self, key)

        if key in self.x_train.columns:
            return self.x_train[key]
        else:
            if hasattr(self.x_train, key):
                return getattr(self.x_train, key)
            else:
                raise AttributeError(e)

    def __setattr__(self, item, value):

        if item not in self.__dict__ or hasattr(self, item):  # any normal attributes are handled normally
            dict.__setattr__(self, item, value)
        else:
            self.__setitem__(item, value)

    def __deepcopy__(self, memo):

        new_inst = type(self)(self)

        return new_inst

    @property
    def plot_colors(self): # pragama: no cover
        """
        Displays all plot colour names
        """

        from IPython.display import IFrame

        IFrame('https://python-graph-gallery.com/wp-content/uploads/100_Color_names_python.png')

    @property
    def plot_colorpalettes(self): # pragma: no cover
        """
        Displays color palette configuration guide.
        """

        from IPython.display import IFrame

        IFrame('https://seaborn.pydata.org/tutorial/color_palettes.html')


    @property
    def y_train(self):
        """
        Property function for the training predictor variable
        """

        return (
            self.x_train[self.target_field]
            if self.target_field
            else None
        )

    @y_train.setter
    def y_train(self, value):
        """
        Setter function for the training predictor variable
        """

        if self.target_field:
            self.x_train[self.target_field] = value
        else:
            self.target_field = "label"
            self.x_train["label"] = value
            print('Added a target (predictor) field (column) named "label".')

    @property
    def y_test(self):
        """
        Property function for the testing predictor variable
        """

        if self.x_test is not None:
            if self.target_field:
                return self.x_test[self.target_field]
            else:
                return None
        else:
            return None

    @y_test.setter
    def y_test(self, value):
        """
        Setter function for the testing predictor variable
        """

        if self.x_test is not None:
            if self.target_field:
                self.x_test[self.target_field] = value
            else:
                self.target_field = "label"
                self.x_test["label"] = value
                print('Added a target (predictor) field (column) named "label".')

    @y_test.setter
    def y_test(self, value):
        """
        Setter function for the testing predictor variable
        """

        if self.x_test is not None:
            if self.target_field:
                self.x_test[self.target_field] = value
            else:
                self.target_field = "label"
                self.x_test["label"] = value
                print('Added a target (predictor) field (column) named "label".')

    @property
    def columns(self):
        """
        Property to return columns in the dataset.
        """

        return self.x_train.columns.tolist()

    @property
    def missing_values(self):
        """
        Property function that shows how many values are missing in each column.
        """

        dataframes = list(
            filter(
                lambda x: x is not None,
                [
                    self.x_train,
                    self.x_train,
                    self.x_test,
                ],
            )
        )

        for dataframe in dataframes:
            if not dataframe.isnull().values.any():
                print("No missing values!")
            else:
                total = dataframe.isnull().sum().sort_values(ascending=False)
                percent = (
                    dataframe.isnull().sum() / dataframe.isnull().count()
                ).sort_values(ascending=False)
                missing_data = pd.concat(
                    [total, percent], axis=1, keys=["Total", "Percent"]
                )

                display(missing_data.T)

    def copy(self):
        """
        Returns deep copy of object.
        
        Returns
        -------
        Object
            Deep copy of object
        """

        return copy.deepcopy(self)

    def set_option(self, option, value):
        """
        Sets pyautoml options.
        
        Parameters
        ----------
        option : str
            Pyautoml option
        value :
            Value for the pyautoml option
        """

        pyautoml.set_option(option, value)  # pragma: no cover

    def get_option(self, option):
        """
        Gets option value for Pyautoml options
        
        Parameters
        ----------
        option : str
            Pyautoml option
        """

        pyautoml.get_option(option)  # pragma: no cover

    def reset_option(self, option):
        """
        Resets Pyautoml options back to their default values
        
        Parameters
        ----------
        option : str
            Pyautoml option
        """

        pyautoml.reset_option(option)  # pragma: no cover

    def describe_option(self, option):
        """
        Describes Pyautoml option, giving more details.
        
        Parameters
        ----------
        option : str
            Pyautoml option
        """

        pyautoml.describe_option(option)  # pragma: no cover

    def standardize_column_names(self):
        """
        Utility function that standardizes all column names to lowercase and underscores for spaces.
        """

        new_column_names = {}
        pattern = re.compile("\W+")

        for name in self.x_train.columns:
            new_column_names[name] = re.sub(pattern, "_", name.lower())

        self.col_mapping = new_column_names

        self.x_train.rename(columns=new_column_names, inplace=True)

        if self.x_test is not None:
            self.x_test.rename(columns=new_column_names, inplace=True)

        return self.copy()

    def expand_json_column(self, col):
        """
        Utility function that expands a column that has JSON elements into columns, where each JSON key is a column. 

        Parameters
        ----------
        cols: str
            Column in the data that has the nested data.
        """

        df = json_normalize(self.x_train[col], sep='_')
        self.x_train.drop(col, axis=1, inplace=True)            
        self.x_train = pd.concat([self.x_train, df], axis=1)

        if self.x_test is not None:
            df = json_normalize(self.x_test[col], sep='_')
            self.x_test.drop(col, axis=1, inplace=True)            
            self.x_test = pd.concat([self.x_test, df], axis=1)

        return self.copy()            

    def search(self, *values, not_equal=False, replace=False):
        """
        Searches the entire dataset for specified value(s) and returns rows that contain the values.
        
        Parameters
        ----------
        values : Any
            Value to search for in dataframe

        not_equal : bool, optional
            True if you want filter by values in the dataframe that are not equal to the value provided, by default False

        replace : bool, optional
            Whether to permanently transform your data, by default False
        """

        # TODO: Refactor this to take in boolean expressions

        if not values:
            return ValueError("Please provided columns to groupby.")

        if replace:
            if not_equal:
                self.x_train = self.x_train[
                    self.x_train.isin(list(values)).any(axis=1)
                ]

                if self.x_test is not None:
                    self.x_test = self.x_test[
                        self.x_test.isin(list(values)).any(axis=1)
                    ]
            else:
                self.x_train = self.x_train[
                    self.x_train.isin(list(values)).any(axis=1)
                ]

                if self.x_test is not None:
                    self.x_test = self.x_test[
                        self.x_test.isin(list(values)).any(axis=1)
                    ]

            return self.copy()
        else:
            data = self.x_train.copy()

            if not not_equal:
                data = data[data.isin(list(values))].dropna(how="all")
            else:
                data = data[~data.isin(list(values))].dropna(how="all")

            return data

    def where(self, *filter_columns, **columns):
        """
        Filters the dataframe down for highlevel analysis. 

        Can only handle '==', for more complex queries, interact with pandas.
        
        Parameters
        ----------
        filter_columns : str(s)
            Columns you want to see at the end result

        columns : key word arguments
            Columns and the associated value to filter on.
            Columns can equal a value or a list of values to include.
        
        Returns
        -------
        Dataframe
            A view of your data or training data

        Examples
        --------
        >>> clean.where('col1', col2=3, col3=4, col4=[1,2,3])
        This translates to your data where col2 is equal to 3 and col 3 is equal to 4 and column 4 is equal to 1, 2 or 3.
        The col1 specifies that this this is the only column you want to see at the output.
        """

        filtered_data = self.x_train.copy()


        for col in columns.keys():
            if isinstance(columns[col], list):
                filtered_data = filtered_data[filtered_data[col].isin(columns[col])]
            else:
                filtered_data = filtered_data[filtered_data[col] == columns[col]]

        if filter_columns:
            return filtered_data[list(filter_columns)]
        else:
            return filtered_data

    def groupby(self, *groupby, replace=False):
        """
        Groups data by the provided columns.
        
        Parameters
        ----------
        groupby : str(s)
            Columns to group the data by.

        replace : bool, optional
            Whether to permanently transform your data, by default False
        
        Returns
        -------
        Dataframe, Clean, Preprocess or Feature
            Dataframe or copy of object
        """

        if not groupby:
            return ValueError("Please provided columns to groupby.")

        if replace:
            self.x_train = self.x_train.groupby(
                list(groupby)
            )

            if self.x_test is not None:
                self.x_test = self.x_test.groupby(
                    list(groupby)
                )

            return self.copy()
        else:
            data = self.x_train.copy()

            return data.groupby(list(groupby))

    def groupby_analysis(self, groupby: list, *cols, data_filter=None):
        """
        Groups your data and then provides descriptive statistics for the other columns on the grouped data.

        For numeric data, the descriptive statistics are:

            - count
            - min
            - max
            - mean
            - standard deviation
            - variance
            - median
            - most common
            - sum
            - Median absolute deviation
            - number of unique values

        For other types of data:

            - count
            - most common
            - number of unique values
        
        Parameters
        ----------
        groupby : list
            List of columns to groupby.

        cols : str(s)
            Columns you want statistics on, if none are provided, it will provide statistics for every column.

        data_filter : Dataframe, optional
            Filtered dataframe, by default None
        
        Returns
        -------
        Dataframe
            Dataframe of grouped columns and statistics for each column.
        """

        analysis = {}
        numeric_analysis = [
            "count",
            "min",
            "max",
            "mean",
            "std",
            "var",
            "median",
            ("most_common", lambda x: pd.Series.mode(x)[0]),
            "sum",
            "mad",
            "nunique",
        ]
        other_analysis = [
            "count",
            ("most_common", lambda x: pd.Series.mode(x)[0]),
            "nunique",
        ]

        list_of_cols = _get_columns(list(cols), self.x_train)

        if isinstance(data_filter, pd.DataFrame):
            data = data_filter
        else:
            data = self.x_train.copy()

        for col in list_of_cols:
            if col not in groupby:
                # biufc - bool, int, unsigned, float, complex
                if data[col].dtype.kind in "biufc":
                    analysis[col] = numeric_analysis
                else:
                    analysis[col] = other_analysis

        analyzed_data = data.groupby(groupby).agg(analysis)

        return analyzed_data

    def data_report(self, title="Profile Report", output_file="", suppress=False):
        """
        Generates a full Exploratory Data Analysis report using Pandas Profiling.

        Credits: https://github.com/pandas-profiling/pandas-profiling
        
        For each column the following statistics - if relevant for the column type - are presented in an interactive HTML report:

        - Essentials: type, unique values, missing values
        - Quantile statistics like minimum value, Q1, median, Q3, maximum, range, interquartile range
        - Descriptive statistics like mean, mode, standard deviation, sum, median absolute deviation, coefficient of variation, kurtosis, skewness
        - Most frequent values
        - Histogram
        - Correlations highlighting of highly correlated variables, Spearman, Pearson and Kendall matrices
        - Missing values matrix, count, heatmap and dendrogram of missing values
        
        Parameters
        ----------
        title : str, optional
            Title of the report, by default 'Profile Report'

        output_file : str, optional
            File name of the output file for the report, by default ''

        suppress : bool, optional
            True if you do not want to display the report, by default False
        
        Returns
        -------
        HTML display of Exploratory Data Analysis report
        """

        if shell == "ZMQInteractiveShell":
            report = self.x_train.profile_report(
                title=title, style={"full_width": True}
            )
        else:
            report = self.x_train.profile_report(title=title)

        if output_file:
            report.to_file(output_file=output_file)

        if not suppress:
            return report

    def describe(self, dataset="train"):
        """
        Describes your dataset using the DataFrameSummary library with basic descriptive info.
        Extends the DataFrame.describe() method to give more info.

        Credits go to @mouradmourafiq for his pandas-summary library.
        
        Parameters
        ----------
        dataset : str, optional
            Type of dataset to describe. Can either be `train` or `test`.
            If you are using the full dataset it will automatically describe
            your full dataset no matter the input, 
            by default 'train'
        
        Returns
        -------
        DataFrame
            Dataframe describing your dataset with basic descriptive info
        """

        if dataset == "train":
            x_train_summary = DataFrameSummary(self.x_train)

            return x_train_summary.summary()
        else:
            x_test_summary = DataFrameSummary(self.x_test)

            return x_test_summary.summary()

    def column_info(self, dataset="train"):
        """
        Describes your columns using the DataFrameSummary library with basic descriptive info.

        Credits go to @mouradmourafiq for his pandas-summary library.

        Info
        ----
        counts
        uniques
        missing
        missing_perc
        types
        
        Parameters
        ----------
        dataset : str, optional
            Type of dataset to describe. Can either be `train` or `test`.
            If you are using the full dataset it will automatically describe
            your full dataset no matter the input, 
            by default 'train'
        
        Returns
        -------
        DataFrame
            Dataframe describing your columns with basic descriptive info
        """

        if dataset == "train":
            x_train_summary = DataFrameSummary(self.x_train)

            return x_train_summary.columns_stats
        else:
            x_test_summary = DataFrameSummary(self.x_test)

            return x_test_summary.columns_stats

    def describe_column(self, column, dataset="train"):
        """
        Analyzes a column and reports descriptive statistics about the columns.

        Credits go to @mouradmourafiq for his pandas-summary library.

        Statistics
        ----------
        std                                      
        max                                      
        min                                      
        variance                                 
        mean
        mode                                     
        5%                                       
        25%                                      
        50%                                      
        75%                                      
        95%                                      
        iqr                                      
        kurtosis                                 
        skewness                                 
        sum                                      
        mad                                      
        cv                                       
        zeros_num                                
        zeros_perc                               
        deviating_of_mean                        
        deviating_of_mean_perc                   
        deviating_of_median                      
        deviating_of_median_perc                 
        top_correlations                         
        counts                                   
        uniques                                  
        missing                                  
        missing_perc                             
        types                            
        
        Parameters
        ----------
        column : str
            Column in your dataset you want to analze.

        dataset : str, optional
            Type of dataset to describe. Can either be `train` or `test`.
            If you are using the full dataset it will automatically describe
            your full dataset no matter the input, 
            by default 'train'
        
        Returns
        -------
        dict
            Dictionary mapping a statistic and its value for a specific column
        """

        if dataset == "train":
            x_train_summary = DataFrameSummary(self.x_train)

            return x_train_summary[column]
        else:
            x_test_summary = DataFrameSummary(self.x_test)

            return x_test_summary[column]

    def drop(self, *drop_columns, keep=[], regexp="", reason=""):
        """
        Drops columns from the dataframe.
        
        Parameters
        ----------
        keep : list: optional
            List of columns to not drop, by default []

        regexp : str, optional
            Regular Expression of columns to drop, by default ''

        reason : str, optional
            Reasoning for dropping columns, by default ''

        Column names must be provided as strings that exist in the data.
        
        Returns
        -------
        self : Object
            Return deep copy of itself.

        Examples
        --------
        >>> clean.drop('A', 'B', reason="Columns were unimportant")
        >>> clean.drop('col1', keep=['col2'], regexp=r"col*") # Drop all columns that start with "col" except column 2
        >>> preprocess.drop(keep=['A']) # Drop all columns except column 'A'
        >>> preprocess.drop(regexp=r'col*') # Drop all columns that start with 'col'       
        """

        if not isinstance(keep, list):
            raise TypeError("Keep parameter must be a list.")

        # Handles if columns do not exist in the dataframe
        data_columns = self.x_train.columns
        regex_columns = []

        if regexp:
            regex = re.compile(regexp)
            regex_columns = list(filter(regex.search, data_columns))

        drop_columns = set(drop_columns).union(regex_columns)

        # If there are columns to be dropped, exclude the ones in the keep list
        # If there are no columns to be dropped, drop everything except the keep list
        if drop_columns:
            drop_columns = list(drop_columns.difference(keep))
        else:
            keep = set(data_columns).difference(keep)
            drop_columns = list(drop_columns.union(keep))

        self.x_train = self.x_train.drop(drop_columns, axis=1)

        if self.x_test is not None:
            self.x_test = self.x_test.drop(drop_columns, axis=1)

        if self.report is not None:
            self.report.log(f'Dropped columns: {", ".join(drop_columns)}. {reason}')

        return self.copy()

    def encode_target(self):
        """
        Encodes target variables with value between 0 and n_classes-1.

        Running this function will automatically set the corresponding mapping for the target variable mapping number to the original value.

        Note that this will not work if your test data will have labels that your train data does not.        

        Returns
        -------
        Clean, Preprocess, Feature or Model
            Copy of object
        """

        if not self.target_field:
            raise ValueError(
                "Please set the `target_field` field variable before encoding."
            )

        (
            self.x_train,
            self.x_test,
            self.target_mapping,
        ) = label_encoder(
            x_train=self.x_train,
            x_test=self.x_test,
            list_of_cols=self.target_field,
            target=True,
        )

        if self.report is not None:
            self.report.log("Encoded the target variable as numeric values.")

        return self.copy()

    def to_csv(self, name: str, index=False, **kwargs):
        """
        Write data to csv with the name and path provided.

        The function will automatically add '.csv' to the end of the name.

        By default it writes 10000 rows at a time to file to consider memory on different machines.

        Training data will end in '_train.csv' andt test data will end in '_test.csv'.

        For a full list of keyword args for writing to csv please see the following link: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.to_csv.html
        
        Parameters
        ----------
        name : str
            File path
        index : bool, optional
            True to write 'index' column, by default False
        """

        index = kwargs.pop("index", index)
        chunksize = kwargs.pop("chunksize", 10000)

        self.x_train.to_csv(
            name + "_train.csv", index=index, chunksize=chunksize, **kwargs
        )

        if self.x_test is not None:
            self.x_test.to_csv(
                name + "_test.csv", index=index, chunksize=chunksize, **kwargs
            )

    def checklist(self):
        """
        Displays a checklist dashboard with reminders for a Data Science project.
        """

        data_checkboxes = []
        clean_checkboxes = []
        analysis_checkboxes = [
            [widgets.Label(value="Univariate Analysis")],
            [widgets.Label(value="Multivariate Analysis")],
            [widgets.Label(value="Timeseries Analysis")],
        ]
        issue_checkboxes = []
        preparation_checkboxes = []

        for item in DATA_CHECKLIST:
            data_checkboxes.append(
                widgets.Checkbox(description=item, layout=Layout(width="100%"))
            )
        data_box = widgets.VBox(data_checkboxes)

        for item in CLEANING_CHECKLIST:
            clean_checkboxes.append(
                widgets.Checkbox(description=item, layout=Layout(width="100%"))
            )
        clean_box = widgets.VBox(clean_checkboxes)

        for item in UNI_ANALYSIS_CHECKLIST:
            analysis_checkboxes[0].append(
                widgets.Checkbox(description=item, layout=Layout(width="100%"))
            )
        uni_box = widgets.VBox(analysis_checkboxes[0])

        for item in MULTI_ANALYSIS_CHECKLIST:
            analysis_checkboxes[1].append(
                widgets.Checkbox(description=item, layout=Layout(width="100%"))
            )

        multi_box = widgets.VBox(analysis_checkboxes[1])

        analysis_box = widgets.HBox([uni_box, multi_box])

        for item in ISSUES_CHECKLIST:
            issue_checkboxes.append(
                widgets.Checkbox(description=item, layout=Layout(width="100%"))
            )
        issue_box = widgets.VBox(issue_checkboxes)

        for item in PREPARATION_CHECKLIST:
            preparation_checkboxes.append(
                widgets.Checkbox(description=item, layout=Layout(width="100%"))
            )
        prep_box = widgets.VBox(preparation_checkboxes)

        tab_list = [data_box, clean_box, analysis_box, issue_box, prep_box]

        tab = widgets.Tab()
        tab.children = tab_list
        tab.set_title(0, "Data")
        tab.set_title(1, "Cleaning")
        tab.set_title(2, "Analysis")
        tab.set_title(3, "Issues")
        tab.set_title(4, "Preparation")

        display(tab)

    def to_df(self):
        """
        Return Dataframes for x_train and x_test if it exists.

        Returns
        -------
        Dataframe, *Dataframe
            Transformed dataframe with rows with a missing values in a specific column are missing

        Returns 2 Dataframes test if x_test is provided.  
        """

        if self.x_test is None:
            return self.x_train
        else:
            return self.x_train, self.x_test

    def raincloud(self, x=None, y=None, **params):
        """
        Combines the box plot, scatter plot and split violin plot into one data visualization.
        This is used to offer eyeballed statistical inference, assessment of data distributions (useful to check assumptions),
        and the raw data itself showing outliers and underlying patterns.

        A raincloud is made of:
        1) "Cloud", kernel desity estimate, the half of a violinplot.
        2) "Rain", a stripplot below the cloud
        3) "Umberella", a boxplot
        4) "Thunder", a pointplot connecting the mean of the different categories (if `pointplot` is `True`)

        Useful parameter documentation
        ------------------------------
        https://seaborn.pydata.org/generated/seaborn.boxplot.html

        https://seaborn.pydata.org/generated/seaborn.violinplot.html

        https://seaborn.pydata.org/generated/seaborn.stripplot.html

        Parameters
        ----------
        x : str
            X axis data, reference by column name, any data

        y : str
            Y axis data, reference by column name, measurable data (numeric)
            by default target_field

        hue : Iterable, np.array, or dataframe column name if 'data' is specified
            Second categorical data. Use it to obtain different clouds and rainpoints

        orient : str                  
            vertical if "v" (default), horizontal if "h"

        width_viol : float            
            width of the cloud

        width_box : float             
            width of the boxplot

        palette : list or dict        
            Colours to use for the different levels of categorical variables

        bw : str or float
            Either the name of a reference rule or the scale factor to use when computing the kernel bandwidth,
            by default "scott"

        linewidth : float             
            width of the lines

        cut : float
            Distance, in units of bandwidth size, to extend the density past the extreme datapoints.
            Set to 0 to limit the violin range within the range of the observed data,
            by default 2

        scale : str
            The method used to scale the width of each violin.
            If area, each violin will have the same area.
            If count, the width of the violins will be scaled by the number of observations in that bin.
            If width, each violin will have the same width.
            By default "area"

        jitter : float, True/1
            Amount of jitter (only along the categorical axis) to apply.
            This can be useful when you have many points and they overlap,
            so that it is easier to see the distribution. You can specify the amount of jitter (half the width of the uniform random variable support),
            or just use True for a good default.

        move : float                  
            adjust rain position to the x-axis (default value 0.)

        offset : float                
            adjust cloud position to the x-axis

        color : matplotlib color
            Color for all of the elements, or seed for a gradient palette.

        ax : matplotlib axes
            Axes object to draw the plot onto, otherwise uses the current Axes.

        figsize : (int, int)    
            size of the visualization, ex (12, 5)

        pointplot : bool   
            line that connects the means of all categories, by default False

        dodge : bool 
            When hue nesting is used, whether elements should be shifted along the categorical axis.

        Source: https://micahallen.org/2018/03/15/introducing-raincloud-plots/
        
        Examples
        --------
        >>> clean.raincloud('col1') # Will plot col1 values on the x axis and your target variable values on the y axis
        >>> clean.raincloud('col1', 'col2') # Will plot col1 on the x and col2 on the y axis
        """

        if y is None:
            y_col = self.target_field

        raincloud(y, x, self.x_train)

    def barplot(
        self,
        x: str,
        y=None,
        groupby=None,
        method=None,
        orient="v",
        stacked=False,
        output_file="",
        **barplot_kwargs,
    ):
        """
        Plots a bar plot for the given columns provided using Bokeh.

        If `groupby` is provided, method must be provided for example you may want to plot Age against survival rate,
        so you would want to `groupby` Age and then find the `mean` as the method.

        For a list of group by methods please checkout the following pandas link:
        https://pandas.pydata.org/pandas-docs/stable/reference/groupby.html#computations-descriptive-stats

        For a list of possible arguments for the bar plot please checkout the following links:
        https://github.com/PatrikHlobil/Pandas-Bokeh#barplot and

        https://bokeh.pydata.org/en/latest/docs/reference/plotting.html#bokeh.plotting.figure.Figure.vbar or

        https://bokeh.pydata.org/en/latest/docs/reference/plotting.html#bokeh.plotting.figure.Figure.hbar for horizontal
        
        Parameters
        ----------
        x : str
            Column name for the x axis.

        y : list
            Columns you would like to see plotted against the x_col

        method : str
            Method to aggregate groupy data
            Examples: min, max, mean, etc., optional
            by default None

        orient : str, optional
            Orientation of graph, 'h' for horizontal
            'v' for vertical, by default 'v',

        stacked : bool
            Whether to stack the different columns resulting in a stacked bar chart,
            by default False
        """

        barplot(
            x,
            y,
            self.x_train,
            method=method,
            orient=orient,
            stacked=stacked,
            **barplot_kwargs,
        )

    def scatterplot(
        self,
        x=None,
        y=None,
        z=None,
        category=None,
        title="Scatter Plot",
        size=8,
        output_file="",
        **scatterplot_kwargs,
    ):
        """
        Plots a scatterplot for the given x and y columns provided using Bokeh.

        For a list of possible scatterplot_kwargs for 2 dimensional data please check out the following links:

        https://bokeh.pydata.org/en/latest/docs/reference/plotting.html#bokeh.plotting.figure.Figure.scatter

        https://bokeh.pydata.org/en/latest/docs/user_guide/styling.html#userguide-styling-line-properties 

        For more information on key word arguments for 3d data, please check them out here:

        https://www.plotly.express/plotly_express/#plotly_express.scatter_3d
        
        Parameters
        ----------
        x : str
            X column name

        y : str
            Y column name

        z : str
            Z column name, 

        category : str, optional
            Category to group your data, by default None

        title : str, optional
            Title of the plot, by default 'Scatter Plot'

        size : int or str, optional
            Size of the circle, can either be a number
            or a column name to scale the size, by default 8

        output_file : str, optional
            Output html file name for image

        **scatterplot_kwargs : optional
            See above links for list of possible scatterplot options.

        Examples
        --------
        >>> clean.scatterplot(x='x', y='y') #2d
        >>> clean.scatterplot(x='x', y='y', z='z') #3d
        """

        scatterplot(
            x,
            y,
            z=z,
            data=self.x_train,
            title=title,
            category=category,
            size=size,
            output_file=output_file,
            **scatterplot_kwargs,
        )

    def lineplot(
        self, x: str, y: list, title="Line Plot", output_file="", **lineplot_kwargs
    ):
        """
        Plots a lineplot for the given x and y columns provided using Bokeh.

        For a list of possible lineplot_kwargs please check out the following links:

        https://github.com/PatrikHlobil/Pandas-Bokeh#lineplot

        https://bokeh.pydata.org/en/latest/docs/reference/plotting.html#bokeh.plotting.figure.Figure.line 
        
        Parameters
        ----------
        x : str
            X column name

        y : list
            Column names to plot on the y axis.

        title : str, optional
            Title of the plot, by default 'Line Plot'

        output_file : str, optional
            Output html file name for image

        color : str, optional
            Define a single color for the plot

        colormap : list or Bokeh color palette, optional
            Can be used to specify multiple colors to plot.
            Can be either a list of colors or the name of a Bokeh color palette : https://bokeh.pydata.org/en/latest/docs/reference/palettes.html

        rangetool : bool, optional
            If true, will enable a scrolling range tool.

        xlabel : str, optional
            Name of the x axis

        ylabel : str, optional
            Name of the y axis

        xticks : list, optional
            Explicitly set ticks on x-axis

        yticks : list, optional
            Explicitly set ticks on y-axis

        xlim : tuple (int or float), optional
            Set visible range on x axis

        ylim : tuple (int or float), optional
            Set visible range on y axis.

        **lineplot_kwargs : optional
            For a list of possible keyword arguments for line plot please see https://github.com/PatrikHlobil/Pandas-Bokeh#lineplot
            and https://bokeh.pydata.org/en/latest/docs/reference/plotting.html#bokeh.plotting.figure.Figure.line

        Examples
        --------
        >>> clean.line_plot(x='x', y='y')
        """

        lineplot(
            x,
            y,
            self.x_train,
            title=title,
            output_file=output_file,
            **lineplot_kwargs,
        )

    def correlation_matrix(self, data_labels=False, hide_mirror=False, **kwargs):
        """
        Plots a correlation matrix of all the numerical variables.

        For more information on possible kwargs please see: https://seaborn.pydata.org/generated/seaborn.heatmap.html
        
        Parameters
        ----------
        data_labels : bool, optional
            True to display the correlation values in the plot, by default False

        hide_mirror : bool, optional
            Whether to display the mirroring half of the correlation plot, by default False

        Examples
        --------
        >>> clean.correlation_matrix(data_labels=True)
        """

        correlation_matrix(
            self.x_train,
            data_labels=data_labels,
            hide_mirror=hide_mirror,
            **kwargs,
        )

    def pairplot(self, kind="scatter", diag_kind="auto", hue=None, **kwargs):
        """
        Plots pairplots of the variables from the training data.

        If hue is not provided and a target variable is set, the data will separated and highlighted by the classes in that column.

        For more info and kwargs on pair plots, please see: https://seaborn.pydata.org/generated/seaborn.pairplot.html
        
        Parameters
        ----------
        df : DataFrame
                Data

        kind : {'scatter', 'reg'}, optional
            Type of plot for off-diag plots, by default 'scatter'

        diag_kind : {'auto', 'hist', 'kde'}, optional
            Type of plot for diagonal, by default 'auto'

        hue : str, optional
            Column to colour points by, by default None

        {x, y}_vars : lists of variable names, optional
            Variables within data to use separately for the rows and columns of the figure; i.e. to make a non-square plot.

        palette : dict or seaborn color palette
            Set of colors for mapping the hue variable. If a dict, keys should be values in the hue variable.

        Examples
        --------
        >>> clean.pairplot(kind='kde')
        """

        if self.target_field and not hue:
            hue = self.target_field
        elif not self.target_field and hue:
            hue = hue

        pairplot(
            self.x_train,
            kind=kind,
            diag_kind=diag_kind,
            hue=hue,
            **kwargs,
        )

    def jointplot(self, x: str, y: str, kind="scatter", **kwargs):
        """
        Plots joint plots of 2 different variables.

        Scatter ('scatter'): Scatter plot and histograms of x and y.

        Regression ('reg'): Scatter plot, with regression line and histograms with kernel density fits.

        Residuals ('resid'): Scatter plot of residuals and histograms of residuals.

        Kernel Density Estimates ('kde'): Density estimate plot and histograms.

        Hex ('hex'): Replaces scatterplot with joint histogram using hexagonal bins and histograms on the axes.

        For more info and kwargs for joint plots, see https://seaborn.pydata.org/generated/seaborn.jointplot.html
        
        Parameters
        ----------
        x : str
            X axis column

        y : str
            y axis column

        kind : { “scatter” | “reg” | “resid” | “kde” | “hex” }, optional
            Kind of plot to draw, by default 'scatter'

        color : matplotlib color, optional
            Color used for the plot elements.

        dropna : bool, optional
            If True, remove observations that are missing from x and y.

        {x, y}lim : two-tuples, optional
            Axis limits to set before plotting.

        {joint, marginal, annot}_kws : dicts, optional
            Additional keyword arguments for the plot components.            

        Examples
        --------
        >>> clean.jointplot(x='x', y='y', kind='kde', color='crimson')
        """

        jointplot(x=x, y=y, df=self.x_train, kind=kind, **kwargs)

    def histogram(self, *x, **kwargs):
        """
        Plots a histogram of the given column(s).

        For more histogram key word arguments, please see https://seaborn.pydata.org/generated/seaborn.distplot.html

        Parameters
        ----------
        x: str or str(s)
            Column(s) to plot histograms for.

        bins : argument for matplotlib hist(), or None, optional
            Specification of hist bins, or None to use Freedman-Diaconis rule.

        hist : bool, optional
            Whether to plot a (normed) histogram.

        kde : bool, optional
            Whether to plot a gaussian kernel density estimate.

        rug : bool, optional
            Whether to draw a rugplot on the support axis.

        fit : random variable object, optional
            An object with fit method, returning a tuple that can be passed to a pdf method a positional arguments following an grid of values to evaluate the pdf on.

        Examples
        --------
        >>> clean.histogram('col1')
        >>> clean.histogram('col1', 'col2')
        >>> clean.histogram('col1', kde=False)
        >>> clean.histogram('col1', 'col2', hist=False)
        >>> clean.histogram('col1', kde=False, fit=stat.normal)
        """

        histogram(list(x), data=self.x_train, **kwargs)
