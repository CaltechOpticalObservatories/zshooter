import numpy as np
from astropy import units as u
import astropy.units as u
import numpy as np
import os.path
from scipy.interpolate import dfitpack
import scipy.special as spy_sp
import scipy.signal as spy_sig
from synphot import SpectralElement, SourceSpectrum, units as uu, ReddeningLaw
from synphot.models import BlackBodyNorm1D, ConstFlux1D, Empirical1D, Gaussian1D, Box1D
from astropy.modeling.models import Moffat2D, Moffat1D
import ETC_import
from scipy.interpolate import RegularGridInterpolator
# import skycalc_ipy


MOFFAT_BETA = 4.765
MOFFAT_THETA_FACTOR = 0.5 / (2 ** (1. / MOFFAT_BETA) - 1.) ** .5  # theta = factor*seeingFWHM

_MOFFAT_INTEGRAL_INTERPOLATOR = None


def avgmag(m1, m2):
    return float(2.5 * np.log10((10**(m1/2.5) + 10**(m2/2.5))/2))


def moffat_integral_interpolator(xmax: float = 6.0, xstep: float = .01):
    """
    Construct an efficient interpolator for Moffat PSF as needed. The interpolator gives the integral
    of the 2D Moffat from 0-x, and 0-y. So for the integral of a souce centered on a slit of w,h
    compute 4*moffat_integral_interpolator()((w/2, h/2))

    """

    global _MOFFAT_INTEGRAL_INTERPOLATOR

    if _MOFFAT_INTEGRAL_INTERPOLATOR is not None and _MOFFAT_INTEGRAL_INTERPOLATOR[0] == (xmax, xstep):
        return _MOFFAT_INTEGRAL_INTERPOLATOR[1]

    x = np.arange(0, xmax + xstep, xstep)
    xx, yy = np.meshgrid(x, x)
    mvals = Moffat2D(alpha=MOFFAT_BETA)(xx, yy)
    mint = np.zeros(np.array(mvals.shape) + 1)
    mint[1:, 1:] = mvals.cumsum(axis=0).cumsum(axis=1) / mvals.sum() / 4  # we are only one quadrant!

    def interpf(*args, **kwargs):
        interp = RegularGridInterpolator((x, x), mint[:-1, :-1], bounds_error=False, fill_value=None)
        return interp(*args, **kwargs).clip(0, .25)

    _MOFFAT_INTEGRAL_INTERPOLATOR = ((xmax, xstep), interpf)
    return interpf


def seeing_lambda(w, FWHM, pivot=500. * u.nm):
    """
    Seeing law scaled to wavelength

    https://opg.optica.org/josa/fulltext.cfm?uri=josa-68-7-877&id=57124
    https://www.mdpi.com/2072-4292/14/2/405
    """
    assert u.get_physical_type(w) == 'length', "w must have units of length"
    return FWHM * (w / pivot) ** -0.2


def rangeQ(q0, q1, dq=None):
    """Construct an evenly spaced array using unitful Quantities
    Note that the last point will be exclusive of q1
    """

    assert isinstance(q0, u.Quantity) and isinstance(q1, u.Quantity), "Inputs must be Quantities"

    unit = q0.unit
    if dq is None:
        dq = 1. * unit
    else:
        assert isinstance(dq, u.Quantity), "Inputs must be Quantities"

    # Make sure all input units are same dimension
    assert (unit.physical_type == q1.unit.physical_type) and (unit.physical_type == dq.unit.physical_type), \
        "All inputs must have same physical dimensions (different units are OK)"

    v0 = q0.value
    v1 = q1.to_value(unit)
    dv = dq.to_value(unit)

    return np.arange(v0, v1, dv) * unit

def slit_loss(w, h, fwhm, pivot=500. * u.nm, domain=None):
    """
    Compute fraction of PSF passing through slit and side slices, assuming Moffat PSF

    w: slit width (unitful; angular projection on sky), total width
    h: slit length (height) (unitful; angular projection on sky)
    FWHM: seeing at pivot (unitful)
    optics: Bandpass object for slicer side optics
    wavelengths: optional wavelengths to measure at (in nm)

    RETURNS: Dictionary of bandpass objects for 'center', 'side', and 'total'
    """

    # Slow function of wavelength so choose 10nm sampling
    lams = np.arange(*domain, 10)*u.nm

    # Dimensionless coordinates
    ts = MOFFAT_THETA_FACTOR * seeing_lambda(lams, fwhm, pivot=pivot)  # specific to Moffat PSF
    wts = (w / ts).value
    hts = (h / ts).value

    interp = moffat_integral_interpolator()

    # centerFrac = 4 * interp((wts / 1 / 2, hts / 2))
    totalFrac = 4 * interp((wts / 2, hts / 2))

    # fracs = {'center': centerFrac}
    # Sides need to be evaluated at slice_edges
    # slice_edges = (np.arange((nslit - 1) // 2 + 1) * w / nslit + w / nslit / 2)[:,None] / ts
    # if hasattr(hts, '__iter__') and slice_edges.shape[-1] != hts.shape[-1]:
    #     slice_edges = slice_edges[:, None]
    # profile_sides = np.diff(2*interp((slice_edges, hts / 2)), axis=0)


    return lams, totalFrac #SpectralElement(Empirical1D, points=lams, lookup_table=totalFrac)