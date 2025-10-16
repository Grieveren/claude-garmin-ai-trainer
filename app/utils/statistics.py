"""
Statistical utility functions for data processing and analysis.

This module provides core statistical functions used across the training
optimization system, including moving averages, standard deviation, percentiles,
and outlier detection.

All functions handle missing data (NaN values) gracefully and use numpy/pandas
for efficient calculations.
"""

from typing import List, Optional, Union, Tuple
import numpy as np
import pandas as pd
from numpy.typing import NDArray


def moving_average(
    data: Union[List[float], NDArray, pd.Series],
    window: int = 7,
    min_periods: Optional[int] = None
) -> NDArray:
    """
    Calculate moving average (rolling mean) with configurable window.

    Uses pandas rolling window for efficient calculation. Handles NaN values
    by requiring minimum number of valid observations per window.

    Args:
        data: Input time series data (list, numpy array, or pandas Series)
        window: Size of the moving window in periods (default: 7 days)
        min_periods: Minimum number of valid observations required per window.
                    If None, defaults to window size (no partial windows).
                    Set to 1 to calculate from first value.

    Returns:
        numpy array of moving averages (same length as input)

    Example:
        >>> data = [10, 20, 30, 40, 50]
        >>> moving_average(data, window=3)
        array([nan, nan, 20., 30., 40.])

        >>> moving_average(data, window=3, min_periods=1)
        array([10., 15., 20., 30., 40.])

    Notes:
        - Returns NaN for positions where min_periods is not met
        - Maintains original data length with leading NaN values
        - For ACWR: use window=7 for acute, window=28 for chronic
    """
    if min_periods is None:
        min_periods = window

    series = pd.Series(data)
    result = series.rolling(window=window, min_periods=min_periods).mean()
    return result.to_numpy()


def exponentially_weighted_moving_average(
    data: Union[List[float], NDArray, pd.Series],
    span: int = 7,
    min_periods: int = 1
) -> NDArray:
    """
    Calculate exponentially weighted moving average (EWMA).

    EWMA gives more weight to recent observations, making it more responsive
    to changes than simple moving average. Useful for fitness-fatigue modeling.

    Args:
        data: Input time series data
        span: Decay in terms of span (larger = slower decay). Related to
              half-life by: span = (half-life - 1) / ln(2) ≈ 1.44 * half-life
        min_periods: Minimum number of observations to calculate first value

    Returns:
        numpy array of exponentially weighted moving averages

    Example:
        >>> data = [100, 110, 105, 115, 120]
        >>> exponentially_weighted_moving_average(data, span=3)
        array([100. , 105. , 105. , 110. , 115. ])

    Notes:
        - For fitness-fatigue model: span=42 for fitness, span=7 for fatigue
        - More responsive to recent changes than simple moving average
    """
    series = pd.Series(data)
    result = series.ewm(span=span, min_periods=min_periods, adjust=False).mean()
    return result.to_numpy()


def standard_deviation(
    data: Union[List[float], NDArray, pd.Series],
    ddof: int = 1,
    skipna: bool = True
) -> float:
    """
    Calculate standard deviation of a dataset.

    Args:
        data: Input data array
        ddof: Delta degrees of freedom (default: 1 for sample std dev)
        skipna: If True, exclude NaN values from calculation

    Returns:
        Standard deviation as float, or NaN if insufficient data

    Example:
        >>> data = [10, 20, 30, 40, 50]
        >>> standard_deviation(data)
        15.811388300841896

    Notes:
        - ddof=1 gives sample standard deviation (unbiased estimator)
        - ddof=0 gives population standard deviation
        - Used in training monotony calculation: mean / std
    """
    series = pd.Series(data)
    return series.std(ddof=ddof, skipna=skipna)


def percentile(
    data: Union[List[float], NDArray, pd.Series],
    p: float = 95,
    method: str = 'linear'
) -> float:
    """
    Calculate percentile of a dataset.

    Args:
        data: Input data array
        p: Percentile to calculate (0-100)
        method: Interpolation method ('linear', 'lower', 'higher', 'midpoint', 'nearest')

    Returns:
        Percentile value as float

    Example:
        >>> data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        >>> percentile(data, p=90)
        9.1

    Notes:
        - Useful for establishing baseline thresholds
        - Common uses: 95th percentile for max capacity estimation
    """
    arr = np.array(data)
    arr = arr[~np.isnan(arr)]  # Remove NaN values

    if len(arr) == 0:
        return np.nan

    return np.percentile(arr, p, method=method)


def detect_outliers(
    data: Union[List[float], NDArray, pd.Series],
    method: str = 'iqr',
    threshold: float = 1.5
) -> Tuple[NDArray, NDArray]:
    """
    Detect outliers in a dataset using statistical methods.

    Args:
        data: Input data array
        method: Detection method ('iqr' or 'zscore')
        threshold: Threshold for outlier detection
                  - For IQR: multiplier of IQR (default: 1.5)
                  - For Z-score: number of standard deviations (default: 3.0)

    Returns:
        Tuple of (outlier_mask, outlier_indices)
        - outlier_mask: Boolean array (True for outliers)
        - outlier_indices: Array of indices where outliers occur

    Example:
        >>> data = [10, 12, 11, 13, 100, 12, 11]
        >>> mask, indices = detect_outliers(data, method='iqr')
        >>> indices
        array([4])

    Notes:
        - IQR method: outliers are < Q1-1.5*IQR or > Q3+1.5*IQR
        - Z-score method: outliers are abs(z-score) > threshold
        - IQR is more robust to existing outliers
    """
    arr = np.array(data, dtype=float)
    n = len(arr)

    if method == 'iqr':
        # Interquartile Range method
        q1 = np.nanpercentile(arr, 25)
        q3 = np.nanpercentile(arr, 75)
        iqr = q3 - q1

        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr

        outlier_mask = (arr < lower_bound) | (arr > upper_bound)

    elif method == 'zscore':
        # Z-score method
        mean = np.nanmean(arr)
        std = np.nanstd(arr, ddof=1)

        if std == 0:
            outlier_mask = np.zeros(n, dtype=bool)
        else:
            z_scores = np.abs((arr - mean) / std)
            outlier_mask = z_scores > threshold

    else:
        raise ValueError(f"Unknown method: {method}. Use 'iqr' or 'zscore'")

    # Handle NaN values (don't mark them as outliers)
    outlier_mask = outlier_mask & ~np.isnan(arr)
    outlier_indices = np.where(outlier_mask)[0]

    return outlier_mask, outlier_indices


def rolling_standard_deviation(
    data: Union[List[float], NDArray, pd.Series],
    window: int = 7,
    min_periods: Optional[int] = None
) -> NDArray:
    """
    Calculate rolling standard deviation with configurable window.

    Used for training monotony and variability analysis.

    Args:
        data: Input time series data
        window: Size of the rolling window
        min_periods: Minimum observations required per window

    Returns:
        numpy array of rolling standard deviations

    Example:
        >>> data = [10, 20, 30, 40, 50, 60, 70]
        >>> rolling_standard_deviation(data, window=3)
        array([nan, nan, 10., 10., 10., 10., 10.])

    Notes:
        - Used in training monotony: rolling_mean / rolling_std
        - High std = high variability in training load
        - Low std = monotonous training (injury risk)
    """
    if min_periods is None:
        min_periods = window

    series = pd.Series(data)
    result = series.rolling(window=window, min_periods=min_periods).std(ddof=1)
    return result.to_numpy()


def coefficient_of_variation(
    data: Union[List[float], NDArray, pd.Series],
    skipna: bool = True
) -> float:
    """
    Calculate coefficient of variation (CV).

    CV = (standard deviation / mean) * 100

    Expresses variability as a percentage of the mean, allowing comparison
    of variability across different scales.

    Args:
        data: Input data array
        skipna: If True, exclude NaN values

    Returns:
        Coefficient of variation as percentage

    Example:
        >>> data = [100, 110, 90, 105, 95]
        >>> coefficient_of_variation(data)
        7.637626158259734

    Notes:
        - Useful for comparing variability of HRV across different athletes
        - Lower CV = more consistent/stable metric
    """
    series = pd.Series(data)
    mean = series.mean(skipna=skipna)
    std = series.std(skipna=skipna, ddof=1)

    if mean == 0 or np.isnan(mean):
        return np.nan

    return (std / mean) * 100


def rate_of_change(
    data: Union[List[float], NDArray, pd.Series],
    periods: int = 1,
    fill_method: Optional[str] = None
) -> NDArray:
    """
    Calculate rate of change (percentage change) over specified periods.

    Args:
        data: Input time series data
        periods: Number of periods to shift for comparison
        fill_method: Method to fill NaN values ('ffill', 'bfill', None)

    Returns:
        numpy array of percentage changes

    Example:
        >>> data = [100, 110, 105, 115, 120]
        >>> rate_of_change(data, periods=1)
        array([nan, 0.1, -0.04545455, 0.0952381, 0.04347826])

    Notes:
        - Useful for detecting rapid training load changes
        - Ramp rate = week-over-week change (periods=7 for daily data)
    """
    series = pd.Series(data)
    if fill_method:
        series = series.fillna(method=fill_method)

    result = series.pct_change(periods=periods)
    return result.to_numpy()


def cumulative_sum(
    data: Union[List[float], NDArray, pd.Series],
    skipna: bool = True
) -> NDArray:
    """
    Calculate cumulative sum of a time series.

    Args:
        data: Input time series data
        skipna: If True, skip NaN values

    Returns:
        numpy array of cumulative sums

    Example:
        >>> data = [10, 20, 30, 40, 50]
        >>> cumulative_sum(data)
        array([ 10,  30,  60, 100, 150])

    Notes:
        - Useful for total training load accumulation
    """
    series = pd.Series(data)
    result = series.cumsum(skipna=skipna)
    return result.to_numpy()


def z_score(
    data: Union[List[float], NDArray, pd.Series],
    population_mean: Optional[float] = None,
    population_std: Optional[float] = None
) -> NDArray:
    """
    Calculate z-scores (standard scores) for data.

    Z-score = (x - mean) / std

    Args:
        data: Input data array
        population_mean: Use specific population mean (if None, calculate from data)
        population_std: Use specific population std (if None, calculate from data)

    Returns:
        numpy array of z-scores

    Example:
        >>> data = [10, 20, 30, 40, 50]
        >>> z_score(data)
        array([-1.26491106, -0.63245553,  0.        ,  0.63245553,  1.26491106])

    Notes:
        - Useful for comparing metrics across different scales
        - Can detect how unusual a value is (e.g., HRV drop)
    """
    arr = np.array(data, dtype=float)

    if population_mean is None:
        population_mean = np.nanmean(arr)
    if population_std is None:
        population_std = np.nanstd(arr, ddof=1)

    if population_std == 0:
        return np.full_like(arr, np.nan, dtype=float)

    return (arr - population_mean) / population_std


def linear_regression(
    x: Union[List[float], NDArray],
    y: Union[List[float], NDArray]
) -> Tuple[float, float, float]:
    """
    Calculate simple linear regression: y = mx + b

    Args:
        x: Independent variable data
        y: Dependent variable data

    Returns:
        Tuple of (slope, intercept, r_squared)

    Example:
        >>> x = [1, 2, 3, 4, 5]
        >>> y = [2, 4, 6, 8, 10]
        >>> slope, intercept, r2 = linear_regression(x, y)
        >>> slope, intercept, r2
        (2.0, 0.0, 1.0)

    Notes:
        - Useful for trend analysis (HRV trends, load trends)
        - R² measures goodness of fit (0 = no fit, 1 = perfect fit)
    """
    x_arr = np.array(x, dtype=float)
    y_arr = np.array(y, dtype=float)

    # Remove NaN values
    mask = ~(np.isnan(x_arr) | np.isnan(y_arr))
    x_clean = x_arr[mask]
    y_clean = y_arr[mask]

    if len(x_clean) < 2:
        return np.nan, np.nan, np.nan

    # Calculate regression coefficients
    slope, intercept = np.polyfit(x_clean, y_clean, 1)

    # Calculate R²
    y_pred = slope * x_clean + intercept
    ss_res = np.sum((y_clean - y_pred) ** 2)
    ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)

    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else np.nan

    return slope, intercept, r_squared


def smooth_data(
    data: Union[List[float], NDArray, pd.Series],
    method: str = 'savgol',
    window: int = 7,
    **kwargs
) -> NDArray:
    """
    Smooth noisy time series data.

    Args:
        data: Input time series data
        method: Smoothing method ('savgol', 'lowess', 'rolling_mean')
        window: Window size for smoothing
        **kwargs: Additional arguments for specific methods

    Returns:
        numpy array of smoothed data

    Example:
        >>> data = [10, 15, 12, 18, 14, 20, 17]
        >>> smooth_data(data, method='rolling_mean', window=3)
        array([nan, nan, 12.33..., 15., 14.66..., 17.33..., 17.])

    Notes:
        - Savitzky-Golay filter preserves peaks better than moving average
        - LOWESS is more robust but slower
    """
    series = pd.Series(data)

    if method == 'rolling_mean':
        result = series.rolling(window=window, center=True).mean()
    elif method == 'savgol':
        from scipy.signal import savgol_filter
        polyorder = kwargs.get('polyorder', min(3, window - 1))
        result = pd.Series(savgol_filter(series.dropna(), window, polyorder))
    elif method == 'lowess':
        from statsmodels.nonparametric.lowess import lowess
        frac = kwargs.get('frac', window / len(series))
        smoothed = lowess(series.dropna(), range(len(series.dropna())), frac=frac)
        result = pd.Series(smoothed[:, 1])
    else:
        raise ValueError(f"Unknown smoothing method: {method}")

    return result.to_numpy()
