# swisseph.py — compatibility shim
# pyswisseph requires Microsoft C++ Build Tools to compile on Windows.
# libephemeris is a pure-Python drop-in replacement with the same API.
# This shim re-exports libephemeris under the 'swisseph' name so that
# all existing code using `import swisseph as swe` continues to work.
from libephemeris import *  # noqa: F401, F403
from libephemeris import (  # noqa: F401
    julday, calc_ut, houses as _libephemeris_houses, set_sid_mode, set_ephe_path,
    sidtime,
    FLG_SWIEPH, FLG_SIDEREAL,
    SUN, MOON, MARS, MERCURY, JUPITER, VENUS, SATURN, TRUE_NODE,
    SIDM_LAHIRI, SIDM_RAMAN, SIDM_KRISHNAMURTI, SIDM_TRUE_CITRA,
)

SIDM_TRUE_CHITRA = SIDM_TRUE_CITRA

def sidereal_time(jd_ut):
    """Wrap libephemeris.sidtime to return (sidereal_time, 0) as expected by pyswisseph."""
    return (sidtime(jd_ut), 0)

# House system constants
try:
    from libephemeris import houses as _houses_mod
    P_PLACIDUS = ord('P')
except Exception:
    P_PLACIDUS = ord('P')

def houses(*args, **kwargs):
    """
    Wrap libephemeris.houses function to make it callable while preserving constant attributes.
    Supports both:
      - Standard pyswisseph/libephemeris signature: houses(jd, lat, lon, hsys, iflag=0)
      - Junior developer's signature: houses(hsys, jd, lat, lon, iflag=0)
    """
    if len(args) >= 4:
        arg0 = args[0]
        arg1 = args[1]
        is_arg0_hsys = isinstance(arg0, (str, bytes)) or (isinstance(arg0, int) and arg0 < 300)
        is_arg1_jd = isinstance(arg1, (int, float)) and arg1 > 1000000.0
        
        if is_arg0_hsys and is_arg1_jd:
            hsys, jd, lat, lon = args[0], args[1], args[2], args[3]
            iflag = args[4] if len(args) > 4 else 0
            return _libephemeris_houses(jd, lat, lon, hsys, iflag)
            
    return _libephemeris_houses(*args, **kwargs)

# Expose house system constants as attributes on the houses function object
houses.P_PLACIDUS = ord('P')
houses.PLACIDUS = ord('P')
houses.KOCH = ord('K')
houses.REGIOMONTANUS = ord('R')
houses.CAMPANUS = ord('C')
houses.EQUAL = ord('E')
houses.WHOLE_SIGN = ord('W')
