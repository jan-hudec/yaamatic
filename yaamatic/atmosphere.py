"""ISO Standard Atmosphere.

Calculation of pressure and density in ISO Standard atmosphere copied and
translated from YASim.
"""

import bisect
import collections

from .units import U

_Datum = collections.namedtuple('_Datum', ['a', 'T', 'p', 'rho'])

_kg_m_3 = U.kg * U.m ** -3
_data = [
        _Datum(a * U.m, T * U.K, p * U.Pa, rho * _kg_m_3)
        for a, T, p, rho in (
            (  -900.0, 293.91, 111679.0, 1.32353 ),
            (     0.0, 288.11, 101325.0, 1.22500 ),
            (   900.0, 282.31,  90971.0, 1.12260 ),
            (  1800.0, 276.46,  81494.0, 1.02690 ),
            (  2700.0, 270.62,  72835.0, 0.93765 ),
            (  3600.0, 264.77,  64939.0, 0.85445 ),
            (  4500.0, 258.93,  57752.0, 0.77704 ),
            (  5400.0, 253.09,  51226.0, 0.70513 ),
            (  6300.0, 247.25,  45311.0, 0.63845 ),
            (  7200.0, 241.41,  39963.0, 0.57671 ),
            (  8100.0, 235.58,  35140.0, 0.51967 ),
            (  9000.0, 229.74,  30800.0, 0.46706 ),
            (  9900.0, 223.91,  26906.0, 0.41864 ),
            ( 10800.0, 218.08,  23422.0, 0.37417 ),
            ( 11700.0, 216.66,  20335.0, 0.32699 ),
            ( 12600.0, 216.66,  17654.0, 0.28388 ),
            ( 13500.0, 216.66,  15327.0, 0.24646 ),
            ( 14400.0, 216.66,  13308.0, 0.21399 ),
            ( 15300.0, 216.66,  11555.0, 0.18580 ),
            ( 16200.0, 216.66,  10033.0, 0.16133 ),
            ( 17100.0, 216.66,   8712.0, 0.14009 ),
            ( 18000.0, 216.66,   7565.0, 0.12165 ),
            ( 18900.0, 216.66,   6570.0, 0.10564 ),
            ( 19812.0, 216.66,   5644.0, 0.09073 ),
            ( 20726.0, 217.23,   4884.0, 0.07831 ),
            ( 21641.0, 218.39,   4235.0, 0.06755 ),
            ( 22555.0, 219.25,   3668.0, 0.05827 ),
            ( 23470.0, 220.12,   3182.0, 0.05035 ),
            ( 24384.0, 220.98,   2766.0, 0.04360 ),
            ( 25298.0, 221.84,   2401.0, 0.03770 ),
            ( 26213.0, 222.71,   2087.0, 0.03265 ),
            ( 27127.0, 223.86,   1814.0, 0.02822 ),
            ( 28042.0, 224.73,   1581.0, 0.02450 ),
            ( 28956.0, 225.59,   1368.0, 0.02112 ),
            ( 29870.0, 226.45,   1196.0, 0.01839 ),
            ( 30785.0, 227.32,   1044.0, 0.01599 ),
            )
        ]

_alts = [d.a for d in _data]

# Specific gas constant for air
Rs_air = 297.1 * U.J / U.kg / U.K

# Ratio of specific heats for (at 20°C; flightgear uses this value though
# standard temp is only 15°C at sea level and all less at higher altitudes).
# Also known as gamma.
kappa = 1.4

def _get(a, j):
    i = bisect.bisect(_alts, a)
    d0 = _data[i]
    d1 = _data[i + 1]
    frac = float((a - d0.a)/(d1.a - d0.a))
    return d0[j] + frac * (d1[j] - d0[j])

def getStdTemperature(a):
    return _get(a, 1)

def getStdPressure(a):
    return _get(a, 2)

def getStdDensity(a):
    return _get(a, 3)

def calcDensity(p, T):
    return p / (Rs_air * T.to_base_units())

def speedOfSound(T):
    # a = √(γ Rs T)
    # √(J/kg/K * K) = √(kg m²/s²/kg) = m/s ✓
    return (kappa * Rs_air * T.to(U.K)) ** 0.5

def machFromSpd(v, T):
    # Ma = v / a
    return float(v / speedOfSound(T))

def spdFromMach(Ma, T):
    # v = Ma * a
    return float(Ma) * speedOfSound(T)
