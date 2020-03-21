"""Module for the computation of Twiss functions from transfer matrices.

The standard uncoupled Twiss parametrization (including off-momentum effects, aka. dispersion) is the default option.
Additional formalisms for the parametrization of fully coupled transfer matrices are also available (Teng, Ripken,
etc.).
"""
from typing import Optional, Tuple, Union
from logging import warning
import warnings
import numpy as _np
import pandas as _pd
from . import ureg as _ureg
from .sequences import BetaBlock as _BetaBlock


def _get_parameters(m: _pd.DataFrame, twiss: Optional[_BetaBlock], plane: int = 1) -> Tuple:
    """Extract parameters from the DataFrame."""
    p = 1 if plane == 1 else 3
    v = 1 if plane == 1 else 2
    r11: _pd.Series = m[f"R{p}{p}"]
    r12: _pd.Series = m[f"R{p}{p + 1}"]
    r21: _pd.Series = m[f"R{p + 1}{p}"]
    r22: _pd.Series = m[f"R{p + 1}{p + 1}"]
    if twiss is not None:
        alpha: float = twiss[f"ALPHA{v}{v}"]
        beta: float = twiss[f"BETA{v}{v}"].m_as('m')
        gamma: float = twiss[f"GAMMA{v}{v}"].m_as('m**-1')
        return r11, r12, r21, r22, alpha, beta, gamma
    else:
        return r11, r12, r21, r22


def compute_alpha_from_matrix(m: _pd.DataFrame, twiss: _BetaBlock, plane: int = 1) -> _pd.Series:
    """
    Computes the Twiss alpha values at every steps of the input step-by-step transfer matrix.

    Args:
        m: the step-by-step transfer matrix for which the alpha values should be computed
        twiss: the initial Twiss values
        plane: an integer representing the plane (1 or 2)

    Returns:
        a Pandas Series with the alpha values computed at all steps of the input step-by-step transfer matrix
    """
    r11, r12, r21, r22, alpha, beta, gamma = _get_parameters(m, twiss, plane)
    return -r11 * r21 * beta + (r11 * r22 + r12 * r21) * alpha - r12 * r22 * gamma


def compute_beta_from_matrix(m: _pd.DataFrame, twiss: _BetaBlock, plane: int = 1,
                             strict: bool = False) -> _pd.Series:
    """
    Computes the Twiss beta values at every steps of the input step-by-step transfer matrix.

    Args:
        m: the step-by-step transfer matrix for which the beta values should be computed
        twiss: the initial Twiss values
        plane: an integer representing the plane (1 or 2)
        strict: flag to activate the strict mode: checks and ensures that all computed beta are positive

    Returns:
        a Pandas Series with the beta values computed at all steps of the input step-by-step transfer matrix
    """
    r11, r12, r21, r22, alpha, beta, gamma = _get_parameters(m, twiss, plane)
    _ = r11 ** 2 * beta - 2.0 * r11 * r12 * alpha + r12 ** 2 * gamma
    if strict:
        assert (_ > 0).all(), "Not all computed beta are positive."
    return _


def compute_gamma_from_matrix(m: _pd.DataFrame, twiss: _BetaBlock, plane: int = 1) -> _pd.Series:
    """
    Computes the Twiss gamma values at every steps of the input step-by-step transfer matrix.

    Args:
        m: the step-by-step transfer matrix for which the beta values should be computed
        twiss: the initial Twiss values
        plane: an integer representing the plane (1 or 2)

    Returns:
        a Pandas Series with the gamma values computed at all steps of the input step-by-step transfer matrix
    """
    r11, r12, r21, r22, alpha, beta, gamma = _get_parameters(m, twiss, plane)
    return r21 ** 2 * beta - 2.0 * r21 * r22 * alpha + r22 ** 2 * gamma


def compute_mu_from_matrix(m: _pd.DataFrame, twiss: _BetaBlock, plane: int = 1) -> _pd.Series:
    """
    Computes the phase advance values at every steps of the input step-by-step transfer matrix.

    Args:
        m: the step-by-step transfer matrix for which the beta values should be computed
        twiss: the initial Twiss values
        plane: an integer representing the plane (1 or 2)

    Returns:
        a Pandas Series with the phase advance computed at all steps of the input step-by-step transfer matrix
    """
    r11, r12, r21, r22, alpha, beta, gamma = _get_parameters(m, twiss, plane)
    return _np.arctan2(r12, r11 * beta - r12 * alpha)


def compute_jacobian_from_matrix(m: _pd.DataFrame, plane: int = 1) -> _pd.Series:
    """
    Computes the jacobian of the 2x2 transfer matrix (useful to verify the simplecticity).

    Args:
        m: the step-by-step transfer matrix for which the jacobians should be computed
        plane: an integer representing the plane (1 or 2)

    Returns:
        a Pandas Series with the jacobian computed at all steps of the input step-by-step transfer matrix
    """
    r11, r12, r21, r22 = _get_parameters(m, None, plane)
    return r11 * r22 - r12 * r21


def compute_dispersion_from_matrix(m: _pd.DataFrame, twiss: _BetaBlock, plane: int = 1) -> _pd.Series:
    """
    Computes the dispersion function at every steps of the input step-by-step transfer matrix.

    Args:
        m: the step-by-step transfer matrix for which the dispersion function should be computed
        twiss: initial values for the Twiss parameters
        plane: an integer representing the plane (1 or 2)

    Returns:
        a Pandas Series with the dispersion function computed at all steps of the input step-by-step transfer matrix

    """
    p = 1 if plane == 1 else 3
    if p == 1:
        d0 = twiss['DISP1']
        dp0 = twiss['DISP2']
    else:
        d0 = twiss['DISP3']
        dp0 = twiss['DISP4']
    r11: _pd.Series = m[f"R{p}{p}"]
    r12: _pd.Series = m[f"R{p}{p + 1}"]
    r15: _pd.Series = m[f"R{p}5"]
    return d0 * r11 + dp0 * r12 + r15


def compute_dispersion_prime_from_matrix(m: _pd.DataFrame, twiss: _BetaBlock, plane: int = 1) -> _pd.Series:
    """
    Computes the dispersion prime function at every steps of the input step-by-step transfer matrix.

    Args:
        m: the step-by-step transfer matrix for which the dispersion prime function should be computed
        twiss: initial values for the Twiss parameters
        plane: an integer representing the plane (1 or 2)

    Returns:
        a Pandas Series with the dispersion prime function computed at all steps of the input step-by-step transfer
        matrix

    Example:

    """
    p = 1 if plane == 1 else 3
    if p == 1:
        d0 = twiss['DISP1']
        dp0 = twiss['DISP2']
    else:
        d0 = twiss['DISP3']
        dp0 = twiss['DISP4']
    r21: _pd.Series = m[f"R{p + 1}{p}"]
    r22: _pd.Series = m[f"R{p + 1}{p + 1}"]
    r25: _pd.Series = m[f"R{p + 1}5"]
    return d0 * r21 + dp0 * r22 + r25


def compute_periodic_twiss(matrix: _pd.DataFrame, end: Union[int, str] = -1) -> _BetaBlock:
    """
    Compute twiss parameters from a transfer matrix which is assumed to be a periodic transfer matrix.

    Args:
        matrix: the (periodic) transfer matrix
        end:

    Returns:
        a Series object with the values of the periodic Twiss parameters.
    """
    if isinstance(end, int):
        m = matrix.iloc[end]
    elif isinstance(end, str):
        m = matrix[matrix.LABEL1 == end].iloc[-1]
    twiss = dict({
        'CMU1': (m['R11'] + m['R22'])/2.0,
        'CMU2': (m['R33'] + m['R44'])/2.0,
    })
    if twiss['CMU1'] < -1.0 or twiss['CMU1'] > 1.0:
        warning(f"Horizontal motion is unstable; proceed with caution (cos(mu) = {twiss['CMU1']}).")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        twiss['MU1'] = _np.arccos(twiss['CMU1'])
    if twiss['CMU2'] < -1.0 or twiss['CMU2'] > 1.0:
        warning(f"Vertical motion is unstable; proceed with caution (cos(mu) = {twiss['CMU2']}).")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        twiss['MU2'] = _np.arccos(twiss['CMU2'])
    twiss['BETA11'] = m['R12'] / _np.sin(twiss['MU1']) * _ureg.m
    if twiss['BETA11'] < 0.0:
        twiss['BETA11'] *= -1
        twiss['MU1'] *= -1
    twiss['BETA22'] = m['R34'] / _np.sin(twiss['MU2']) * _ureg.m
    if twiss['BETA22'] < 0.0:
        twiss['BETA22'] *= -1
        twiss['MU2'] *= -1
    twiss['ALPHA11'] = (m['R11'] - m['R22']) / (2.0 * _np.sin(twiss['MU1']))
    twiss['ALPHA22'] = (m['R33'] - m['R44']) / (2.0 * _np.sin(twiss['MU2']))
    twiss['GAMMA11'] = -m['R21'] / _np.sin(twiss['MU1']) * _ureg.m**-1
    twiss['GAMMA22'] = -m['R43'] / _np.sin(twiss['MU2']) * _ureg.m**-1
    m44 = m[['R11', 'R12', 'R13', 'R14',
             'R21', 'R22', 'R23', 'R24',
             'R31', 'R32', 'R33', 'R34',
             'R41', 'R42', 'R43', 'R44']].apply(float).values.reshape(4, 4)
    r6 = m[['R15', 'R25', 'R35', 'R45']].apply(float).values.reshape(4, 1)
    disp = _np.dot(_np.linalg.inv(_np.identity(4) - m44), r6).reshape(4)
    twiss['DY'] = disp[0] * _ureg.m
    twiss['DYP'] = disp[1]
    twiss['DZ'] = disp[2] * _ureg.m
    twiss['DZP'] = disp[3]
    twiss['DISP1'] = twiss['DY']
    twiss['DISP2'] = twiss['DYP']
    twiss['DISP3'] = twiss['DZ']
    twiss['DISP4'] = twiss['DZP']

    return _BetaBlock(**twiss)
