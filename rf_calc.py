#!/usr/bin/env python3
"""rf-calc — RF & Transmission Line Calculator CLI

A zero-dependency Python CLI for common RF engineering calculations.
Built for students, hobbyists, and anyone who'd rather type than spreadsheet.

Author: Mel (space0mel) — https://mel.9840002.xyz
License: MIT
"""

import argparse
import math
import sys
from typing import Optional

__version__ = "1.0.0"

# ── Constants ──────────────────────────────────────────────────────────────────
C = 299_792_458        # speed of light in vacuum (m/s)
MU_0 = 4e-7 * math.pi # permeability of free space (H/m)
EPS_0 = 8.854187817e-12  # permittivity of free space (F/m)
ETA_0 = 376.730313668  # impedance of free space (Ω)

# ── Helpers ────────────────────────────────────────────────────────────────────

def _eng(value: float, unit: str = "", precision: int = 4) -> str:
    """Format a number with engineering notation (SI prefixes)."""
    if value == 0:
        return f"0 {unit}".strip()

    prefixes = {
        -24: "y", -21: "z", -18: "a", -15: "f", -12: "p",
        -9: "n", -6: "µ", -3: "m", 0: "", 3: "k", 6: "M",
        9: "G", 12: "T", 15: "P", 18: "E",
    }

    exp = math.floor(math.log10(abs(value)))
    eng_exp = (exp // 3) * 3
    eng_exp = max(-24, min(18, eng_exp))

    mantissa = value / (10 ** eng_exp)
    prefix = prefixes.get(eng_exp, f"e{eng_exp}")
    return f"{mantissa:.{precision}g} {prefix}{unit}".strip()


def _parse_freq(s: str) -> float:
    """Parse a frequency string with optional SI suffix (e.g., '2.4G', '100M', '915k')."""
    s = s.strip().upper()
    multipliers = {"K": 1e3, "M": 1e6, "G": 1e9, "T": 1e12}
    if s and s[-1] in multipliers:
        return float(s[:-1]) * multipliers[s[-1]]
    # Also handle 'HZ' suffix
    if s.endswith("HZ"):
        s = s[:-2].strip()
        if s and s[-1] in multipliers:
            return float(s[:-1]) * multipliers[s[-1]]
        return float(s)
    return float(s)


def _parse_complex(s: str) -> complex:
    """Parse a complex impedance string like '50+j25' or '75-j10' or just '50'."""
    s = s.strip().replace(" ", "")
    # Handle forms like 50+j25, 50-j25
    s_lower = s.lower()
    if "j" in s_lower:
        # Replace 'j' notation: 50+j25 → 50+25j
        s_lower = s_lower.replace("+j", "+").replace("-j", "-")
        # If starts with j, it's pure imaginary
        if s_lower.startswith("j"):
            s_lower = s_lower[1:] + "j"
        else:
            # Find the split point — last + or - that's not at start
            for i in range(len(s_lower) - 1, 0, -1):
                if s_lower[i] in "+-":
                    real = s_lower[:i]
                    imag = s_lower[i:]
                    return complex(float(real), float(imag))
            # No split found, try direct
            return complex(float(s_lower.rstrip("j") or "0") * 1j)
        return complex(s_lower)
    return complex(float(s), 0)


def _show(label: str, value: str, indent: int = 2):
    """Print a labeled result line."""
    print(f"{'':>{indent}}{label}: {value}")


def _header(title: str):
    """Print a section header."""
    print(f"\n  ── {title} {'─' * max(1, 50 - len(title))}\n")


# ── Calculations ───────────────────────────────────────────────────────────────

def cmd_impedance(args):
    """Calculate characteristic impedance from RLGC parameters."""
    R = args.R  # Ω/m
    L = args.L  # H/m
    G = args.G  # S/m
    Cap = args.C  # F/m
    f = _parse_freq(args.freq)
    omega = 2 * math.pi * f

    Z = complex(R, omega * L)  # R + jωL
    Y = complex(G, omega * Cap)  # G + jωC

    Z0 = (Z / Y) ** 0.5
    gamma = (Z * Y) ** 0.5  # propagation constant

    alpha = gamma.real  # attenuation constant (Np/m)
    beta = gamma.imag   # phase constant (rad/m)
    vp = omega / beta if beta != 0 else float('inf')  # phase velocity
    wavelength = 2 * math.pi / beta if beta != 0 else float('inf')

    _header("Characteristic Impedance (RLGC)")
    _show("Frequency", _eng(f, "Hz"))
    _show("Z₀", f"{Z0.real:.4g} + j{Z0.imag:.4g} Ω  (|Z₀| = {abs(Z0):.4g} Ω)")
    _show("γ", f"{alpha:.6g} + jβ{beta:.6g}  (α = {_eng(alpha, 'Np/m')}, β = {_eng(beta, 'rad/m')})")
    _show("Phase velocity", f"{_eng(vp, 'm/s')}  ({vp/C:.4g}c)")
    _show("Wavelength", _eng(wavelength, "m"))

    if R == 0 and G == 0:
        Z0_lossless = math.sqrt(L / Cap)
        vp_lossless = 1 / math.sqrt(L * Cap)
        print(f"\n  ℹ Lossless case: Z₀ = √(L/C) = {Z0_lossless:.4g} Ω, vₚ = {_eng(vp_lossless, 'm/s')}")


def cmd_gamma(args):
    """Calculate reflection coefficient from load and characteristic impedance."""
    ZL = _parse_complex(args.zl)
    Z0 = _parse_complex(args.z0)

    gamma = (ZL - Z0) / (ZL + Z0)
    mag = abs(gamma)
    phase = math.degrees(math.atan2(gamma.imag, gamma.real))

    vswr = (1 + mag) / (1 - mag) if mag < 1 else float('inf')
    return_loss = -20 * math.log10(mag) if mag > 0 else float('inf')
    mismatch_loss = -10 * math.log10(1 - mag**2) if mag < 1 else float('inf')
    power_delivered = (1 - mag**2) * 100  # percentage

    _header("Reflection Coefficient")
    _show("Z_L", f"{ZL}")
    _show("Z₀", f"{Z0}")
    _show("Γ", f"{gamma.real:.6g} + j{gamma.imag:.6g}")
    _show("|Γ|", f"{mag:.6g}")
    _show("∠Γ", f"{phase:.2f}°")
    _show("VSWR", f"{vswr:.4g}:1" if vswr != float('inf') else "∞:1")
    _show("Return Loss", f"{return_loss:.2f} dB" if return_loss != float('inf') else "∞ dB")
    _show("Mismatch Loss", f"{mismatch_loss:.4f} dB" if mismatch_loss != float('inf') else "∞ dB")
    _show("Power Delivered", f"{power_delivered:.2f}%")


def cmd_vswr(args):
    """Calculate VSWR and related quantities from reflection coefficient magnitude."""
    mag = args.gamma

    if mag < 0 or mag > 1:
        print("Error: |Γ| must be between 0 and 1", file=sys.stderr)
        sys.exit(1)

    vswr = (1 + mag) / (1 - mag) if mag < 1 else float('inf')
    return_loss = -20 * math.log10(mag) if mag > 0 else float('inf')
    mismatch_loss = -10 * math.log10(1 - mag**2) if mag < 1 else float('inf')
    power_reflected = mag**2 * 100
    power_delivered = (1 - mag**2) * 100

    _header("VSWR Analysis")
    _show("|Γ|", f"{mag:.6g}")
    _show("VSWR", f"{vswr:.4g}:1" if vswr != float('inf') else "∞:1")
    _show("Return Loss", f"{return_loss:.2f} dB" if return_loss != float('inf') else "∞ dB")
    _show("Mismatch Loss", f"{mismatch_loss:.4f} dB" if mismatch_loss != float('inf') else "∞ dB")
    _show("Power Reflected", f"{power_reflected:.2f}%")
    _show("Power Delivered", f"{power_delivered:.2f}%")


def cmd_input_z(args):
    """Calculate input impedance at distance d from load."""
    ZL = _parse_complex(args.zl)
    Z0 = _parse_complex(args.z0)
    f = _parse_freq(args.freq)
    d = args.distance

    # Parse optional er for wavelength calculation
    er = args.er if args.er else 1.0
    vp = C / math.sqrt(er)
    wavelength = vp / f
    beta = 2 * math.pi / wavelength

    # Zin = Z0 * (ZL + jZ0*tan(βd)) / (Z0 + jZL*tan(βd))
    tan_bd = math.tan(beta * d)
    numerator = ZL + 1j * Z0 * tan_bd
    denominator = Z0 + 1j * ZL * tan_bd
    Zin = Z0 * (numerator / denominator)

    gamma_L = (ZL - Z0) / (ZL + Z0)

    _header("Input Impedance")
    _show("Z_L", f"{ZL}")
    _show("Z₀", f"{Z0}")
    _show("Frequency", _eng(f, "Hz"))
    _show("Distance", f"{_eng(d, 'm')}  ({d/wavelength:.4g}λ)")
    _show("εᵣ", f"{er}")
    _show("Wavelength", _eng(wavelength, "m"))
    _show("βd", f"{math.degrees(beta * d):.2f}°")
    _show("Z_in", f"{Zin.real:.4g} + j{Zin.imag:.4g} Ω  (|Z_in| = {abs(Zin):.4g} Ω)")

    # Special cases
    if abs(ZL) < 1e-10:
        print(f"\n  ℹ Short-circuit load → Z_in = jZ₀·tan(βd) = j{(Z0 * tan_bd).imag:.4g} Ω")
    elif abs(ZL) > 1e10:
        print(f"\n  ℹ Open-circuit load → Z_in = -jZ₀·cot(βd) = j{(-Z0 / tan_bd).imag:.4g} Ω")


def cmd_wavelength(args):
    """Frequency ↔ wavelength conversion with material properties."""
    er = args.er if args.er else 1.0
    ur = args.ur if args.ur else 1.0

    vp = C / math.sqrt(er * ur)

    if args.freq:
        f = _parse_freq(args.freq)
        lam = vp / f
        _header("Frequency → Wavelength")
        _show("Frequency", _eng(f, "Hz"))
    elif args.wavelength:
        lam = args.wavelength
        f = vp / lam
        _header("Wavelength → Frequency")
        _show("Wavelength", _eng(lam, "m"))
    else:
        print("Error: provide either --freq or --wavelength", file=sys.stderr)
        sys.exit(1)

    k = 2 * math.pi / lam  # wave number

    _show("εᵣ", f"{er}")
    _show("μᵣ", f"{ur}")
    _show("Phase velocity", f"{_eng(vp, 'm/s')}  ({vp/C:.4g}c)")
    _show("Wavelength", _eng(lam, "m"))
    _show("Frequency", _eng(f, "Hz"))
    _show("Wave number k", f"{_eng(k, 'rad/m')}")
    _show("Period", _eng(1/f, "s"))

    if er > 1 or ur > 1:
        lam_0 = C / f
        print(f"\n  ℹ Free-space λ₀ = {_eng(lam_0, 'm')} — material shortens by factor {lam_0/lam:.4g}×")


def cmd_skin_depth(args):
    """Calculate skin depth for a conductor at a given frequency."""
    f = _parse_freq(args.freq)
    sigma = args.sigma
    ur = args.ur if args.ur else 1.0

    omega = 2 * math.pi * f
    mu = ur * MU_0

    delta = 1 / math.sqrt(math.pi * f * mu * sigma)
    Rs = 1 / (sigma * delta)  # surface resistance

    _header("Skin Depth")
    _show("Frequency", _eng(f, "Hz"))
    _show("Conductivity σ", f"{_eng(sigma, 'S/m')}")
    _show("μᵣ", f"{ur}")
    _show("Skin depth δ", _eng(delta, "m"))
    _show("Surface resistance Rₛ", f"{_eng(Rs, 'Ω/□')}")

    # Common conductors for reference
    if not args.sigma:
        return
    print()
    conductors = {
        "Copper": 5.8e7,
        "Aluminum": 3.77e7,
        "Gold": 4.1e7,
        "Silver": 6.17e7,
        "Steel (carbon)": 6.99e6,
    }
    for name, s in conductors.items():
        d = 1 / math.sqrt(math.pi * f * MU_0 * ur * s)
        marker = " ◀" if abs(s - sigma) / s < 0.01 else ""
        print(f"    {name:>15}: δ = {_eng(d, 'm')}{marker}")


def cmd_db(args):
    """dB conversion utility."""
    _header("dB Conversion")

    if args.from_db is not None:
        db = args.from_db
        ratio_power = 10 ** (db / 10)
        ratio_voltage = 10 ** (db / 20)
        _show("Input", f"{db} dB")
        _show("Power ratio", f"{ratio_power:.6g}×")
        _show("Voltage ratio", f"{ratio_voltage:.6g}×")
        if db >= 0:
            _show("Meaning", f"Gain — signal amplified by {ratio_power:.4g}× power")
        else:
            _show("Meaning", f"Loss — signal reduced to {ratio_power:.4g}× power")

    elif args.power_ratio is not None:
        ratio = args.power_ratio
        if ratio <= 0:
            print("Error: power ratio must be > 0", file=sys.stderr)
            sys.exit(1)
        db = 10 * math.log10(ratio)
        _show("Power ratio", f"{ratio:.6g}×")
        _show("dB", f"{db:.4f} dB")

    elif args.voltage_ratio is not None:
        ratio = args.voltage_ratio
        if ratio <= 0:
            print("Error: voltage ratio must be > 0", file=sys.stderr)
            sys.exit(1)
        db = 20 * math.log10(ratio)
        _show("Voltage ratio", f"{ratio:.6g}×")
        _show("dB", f"{db:.4f} dB")

    elif args.dbm is not None:
        dbm = args.dbm
        watts = 10 ** ((dbm - 30) / 10)
        _show("Input", f"{dbm} dBm")
        _show("Power", _eng(watts, "W"))
        _show("Voltage (50Ω)", f"{_eng(math.sqrt(watts * 50), 'V')} RMS")
        _show("Voltage (75Ω)", f"{_eng(math.sqrt(watts * 75), 'V')} RMS")

    elif args.watts is not None:
        watts = args.watts
        if watts <= 0:
            print("Error: power must be > 0", file=sys.stderr)
            sys.exit(1)
        dbm = 10 * math.log10(watts) + 30
        _show("Power", _eng(watts, "W"))
        _show("dBm", f"{dbm:.4f} dBm")
        _show("dBW", f"{10 * math.log10(watts):.4f} dBW")

    else:
        print("Error: provide one of --from-db, --power-ratio, --voltage-ratio, --dbm, --watts", file=sys.stderr)
        sys.exit(1)


def cmd_loss(args):
    """Calculate free-space path loss (Friis)."""
    f = _parse_freq(args.freq)
    d = args.distance

    lam = C / f
    if d <= 0:
        print("Error: distance must be > 0", file=sys.stderr)
        sys.exit(1)

    # FSPL = (4πd/λ)²
    fspl_linear = (4 * math.pi * d / lam) ** 2
    fspl_db = 10 * math.log10(fspl_linear)

    _header("Free-Space Path Loss (Friis)")
    _show("Frequency", _eng(f, "Hz"))
    _show("Distance", _eng(d, "m"))
    _show("Wavelength", _eng(lam, "m"))
    _show("FSPL", f"{fspl_db:.2f} dB")
    _show("Linear", f"{fspl_linear:.4g}×")

    # Far-field check
    # Assuming isotropic antenna, far field starts at ~2λ
    far_field = 2 * lam
    if d < far_field:
        print(f"\n  ⚠ Distance ({_eng(d, 'm')}) < 2λ ({_eng(far_field, 'm')}) — may not be in far field")

    # Useful reference points
    print()
    print("  Reference distances:")
    for ref_d in [1, 10, 100, 1000, 10000]:
        if ref_d == d:
            continue
        ref_fspl = 10 * math.log10((4 * math.pi * ref_d / lam) ** 2)
        print(f"    {_eng(ref_d, 'm'):>10}: {ref_fspl:.2f} dB")


def cmd_smith(args):
    """Normalize impedance for Smith Chart plotting."""
    Z = _parse_complex(args.z)
    Z0 = _parse_complex(args.z0) if args.z0 else complex(50, 0)

    z_norm = Z / Z0  # normalized impedance
    gamma = (Z - Z0) / (Z + Z0)

    mag = abs(gamma)
    phase = math.degrees(math.atan2(gamma.imag, gamma.real))
    vswr = (1 + mag) / (1 - mag) if mag < 1 else float('inf')

    # Admittance
    Y = 1 / Z if abs(Z) > 0 else complex(float('inf'), float('inf'))
    Y0 = 1 / Z0
    y_norm = Y / Y0

    _header("Smith Chart")
    _show("Z", f"{Z}")
    _show("Z₀", f"{Z0}")
    _show("z (normalized)", f"{z_norm.real:.4g} + j{z_norm.imag:.4g}")
    _show("Γ", f"{gamma.real:.6g} + j{gamma.imag:.6g}")
    _show("|Γ|", f"{mag:.6g}")
    _show("∠Γ", f"{phase:.2f}°")
    _show("VSWR", f"{vswr:.4g}:1" if vswr != float('inf') else "∞:1")
    print()
    _show("Y", f"{Y.real:.4g} + j{Y.imag:.4g} S")
    _show("y (normalized)", f"{y_norm.real:.4g} + j{y_norm.imag:.4g}")

    # Smith Chart position description
    print()
    if z_norm.real > 1.1:
        region = "outside the r=1 circle (resistive component > Z₀)"
    elif z_norm.real < 0.9:
        region = "inside the r=1 circle (resistive component < Z₀)"
    else:
        region = "near the r=1 circle"

    if z_norm.imag > 0.1:
        half = "upper half (inductive)"
    elif z_norm.imag < -0.1:
        half = "lower half (capacitive)"
    else:
        half = "near the real axis (mostly resistive)"

    _show("Region", f"{region}, {half}")

    if mag > 0.5:
        print(f"\n  ⚠ High mismatch — consider matching network")


# ── CLI Setup ──────────────────────────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(
        prog="rf-calc",
        description="RF & Transmission Line Calculator — zero dependencies, all the formulas.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  rf-calc gamma --zl 75 --z0 50         Reflection coefficient for 75Ω load on 50Ω line
  rf-calc gamma --zl 50+j25 --z0 50     Complex load impedance
  rf-calc vswr --gamma 0.33             VSWR from |Γ| = 0.33
  rf-calc wavelength --freq 2.4G        WiFi wavelength in free space
  rf-calc wavelength --freq 915M --er 4 915 MHz in FR-4 substrate
  rf-calc skin-depth --freq 1G --sigma 5.8e7  Copper at 1 GHz
  rf-calc db --from-db -3               What -3 dB means in power/voltage
  rf-calc db --dbm 20                   20 dBm → watts
  rf-calc loss --freq 2.4G --distance 100  Free-space loss at 100m
  rf-calc smith --z 100+j50             Normalize for Smith Chart (default Z₀=50Ω)
  rf-calc input-z --zl 100+j50 --z0 50 --freq 1G --distance 0.1
        """
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    sub = parser.add_subparsers(dest="command", help="calculation to perform")

    # impedance (RLGC)
    p = sub.add_parser("impedance", help="Z₀ from RLGC parameters", aliases=["z0"])
    p.add_argument("--R", type=float, default=0, help="Resistance per unit length (Ω/m)")
    p.add_argument("--L", type=float, required=True, help="Inductance per unit length (H/m)")
    p.add_argument("--G", type=float, default=0, help="Conductance per unit length (S/m)")
    p.add_argument("--C", type=float, required=True, help="Capacitance per unit length (F/m)")
    p.add_argument("--freq", required=True, help="Frequency (e.g., 1G, 100M)")
    p.set_defaults(func=cmd_impedance)

    # gamma
    p = sub.add_parser("gamma", help="Reflection coefficient Γ from impedances", aliases=["reflect"])
    p.add_argument("--zl", required=True, help="Load impedance (e.g., 75, 50+j25)")
    p.add_argument("--z0", default="50", help="Characteristic impedance (default: 50Ω)")
    p.set_defaults(func=cmd_gamma)

    # vswr
    p = sub.add_parser("vswr", help="VSWR from |Γ|")
    p.add_argument("--gamma", type=float, required=True, help="|Γ| magnitude (0-1)")
    p.set_defaults(func=cmd_vswr)

    # input impedance
    p = sub.add_parser("input-z", help="Input impedance at distance d from load", aliases=["zin"])
    p.add_argument("--zl", required=True, help="Load impedance")
    p.add_argument("--z0", default="50", help="Characteristic impedance (default: 50Ω)")
    p.add_argument("--freq", required=True, help="Frequency")
    p.add_argument("--distance", type=float, required=True, help="Distance from load (m)")
    p.add_argument("--er", type=float, help="Relative permittivity (default: 1)")
    p.set_defaults(func=cmd_input_z)

    # wavelength
    p = sub.add_parser("wavelength", help="Frequency ↔ wavelength conversion", aliases=["lambda"])
    p.add_argument("--freq", help="Frequency (e.g., 2.4G)")
    p.add_argument("--wavelength", type=float, help="Wavelength (m)")
    p.add_argument("--er", type=float, help="Relative permittivity (default: 1)")
    p.add_argument("--ur", type=float, help="Relative permeability (default: 1)")
    p.set_defaults(func=cmd_wavelength)

    # skin depth
    p = sub.add_parser("skin-depth", help="Skin depth for a conductor", aliases=["skin"])
    p.add_argument("--freq", required=True, help="Frequency")
    p.add_argument("--sigma", type=float, required=True, help="Conductivity (S/m)")
    p.add_argument("--ur", type=float, help="Relative permeability (default: 1)")
    p.set_defaults(func=cmd_skin_depth)

    # dB conversion
    p = sub.add_parser("db", help="dB / dBm / power conversions")
    p.add_argument("--from-db", type=float, help="Convert dB to linear ratios")
    p.add_argument("--power-ratio", type=float, help="Convert power ratio to dB")
    p.add_argument("--voltage-ratio", type=float, help="Convert voltage ratio to dB")
    p.add_argument("--dbm", type=float, help="Convert dBm to watts")
    p.add_argument("--watts", type=float, help="Convert watts to dBm")
    p.set_defaults(func=cmd_db)

    # free-space path loss
    p = sub.add_parser("loss", help="Free-space path loss (Friis)", aliases=["fspl"])
    p.add_argument("--freq", required=True, help="Frequency")
    p.add_argument("--distance", type=float, required=True, help="Distance (m)")
    p.set_defaults(func=cmd_loss)

    # smith chart
    p = sub.add_parser("smith", help="Normalize impedance for Smith Chart")
    p.add_argument("--z", required=True, help="Impedance to normalize (e.g., 100+j50)")
    p.add_argument("--z0", help="Reference impedance (default: 50Ω)")
    p.set_defaults(func=cmd_smith)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)
    print()


if __name__ == "__main__":
    main()
