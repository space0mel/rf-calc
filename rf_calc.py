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

__version__ = "1.3.0"

# ── Constants ──────────────────────────────────────────────────────────────────
C = 299_792_458        # speed of light in vacuum (m/s)
MU_0 = 4e-7 * math.pi # permeability of free space (H/m)
EPS_0 = 8.854187817e-12  # permittivity of free space (F/m)
ETA_0 = 376.730313668  # impedance of free space (Ω)

# ── Coaxial Cable Database ─────────────────────────────────────────────────────
# Format: name → {z0, vf, od_mm, cap_pf_m, atten_db_100m @ freq pairs}
# Data from manufacturer datasheets (Belden, Times Microwave, etc.)
COAX_DB = {
    "RG-6": {
        "z0": 75, "vf": 0.82, "od_mm": 6.86,
        "cap_pf_m": 67.3, "shield": "foil+braid",
        "use": "Cable TV, satellite, CATV distribution",
        "atten": {100e6: 6.6, 400e6: 13.1, 1e9: 21.3, 2e9: 31.2},
    },
    "RG-8": {
        "z0": 50, "vf": 0.66, "od_mm": 10.29,
        "cap_pf_m": 96.8, "shield": "braid",
        "use": "HF/VHF ham radio, base station feedlines",
        "atten": {100e6: 6.3, 400e6: 13.8, 1e9: 23.6},
    },
    "RG-11": {
        "z0": 75, "vf": 0.66, "od_mm": 10.29,
        "cap_pf_m": 67.3, "shield": "braid",
        "use": "Long CATV runs, trunk lines",
        "atten": {100e6: 4.3, 400e6: 9.2, 1e9: 15.4},
    },
    "RG-58": {
        "z0": 50, "vf": 0.66, "od_mm": 4.95,
        "cap_pf_m": 93.5, "shield": "braid",
        "use": "General purpose 50Ω, lab interconnects, Wi-Fi pigtails",
        "atten": {100e6: 13.5, 400e6: 27.6, 1e9: 47.2, 3e9: 88.6},
    },
    "RG-59": {
        "z0": 75, "vf": 0.66, "od_mm": 6.15,
        "cap_pf_m": 67.3, "shield": "braid",
        "use": "Video, short CATV runs, legacy analog",
        "atten": {100e6: 11.2, 400e6: 22.3, 1e9: 38.4},
    },
    "RG-142": {
        "z0": 50, "vf": 0.695, "od_mm": 4.95,
        "cap_pf_m": 95.1, "shield": "double braid",
        "use": "Mil-spec, high temp (up to 200°C), PTFE dielectric",
        "atten": {100e6: 11.5, 1e9: 39.4, 3e9: 72.2, 10e9: 145.0},
    },
    "RG-174": {
        "z0": 50, "vf": 0.66, "od_mm": 2.79,
        "cap_pf_m": 100.1, "shield": "braid",
        "use": "Miniature 50Ω, GPS antennas, IoT, tight spaces",
        "atten": {100e6: 26.2, 400e6: 52.5, 1e9: 88.6},
    },
    "RG-213": {
        "z0": 50, "vf": 0.66, "od_mm": 10.29,
        "cap_pf_m": 100.1, "shield": "braid",
        "use": "HF/VHF/UHF ham radio, mil-spec upgrade of RG-8",
        "atten": {100e6: 6.6, 400e6: 14.1, 1e9: 24.0},
    },
    "RG-316": {
        "z0": 50, "vf": 0.695, "od_mm": 2.49,
        "cap_pf_m": 95.1, "shield": "single braid",
        "use": "Thin PTFE, RF pigtails, internal equipment wiring",
        "atten": {100e6: 24.6, 1e9: 85.3, 3e9: 156.2},
    },
    "LMR-195": {
        "z0": 50, "vf": 0.83, "od_mm": 4.95,
        "cap_pf_m": 75.1, "shield": "foil+braid",
        "use": "Wi-Fi, cellular, IoT — low-loss replacement for RG-58",
        "atten": {100e6: 8.9, 400e6: 18.4, 900e6: 27.9, 2.4e9: 47.9},
    },
    "LMR-240": {
        "z0": 50, "vf": 0.84, "od_mm": 6.10,
        "cap_pf_m": 73.8, "shield": "foil+braid",
        "use": "Cellular, Wi-Fi AP, moderate-length RF runs",
        "atten": {100e6: 7.0, 400e6: 14.4, 900e6: 21.7, 2.4e9: 37.1},
    },
    "LMR-400": {
        "z0": 50, "vf": 0.85, "od_mm": 10.29,
        "cap_pf_m": 77.4, "shield": "foil+braid",
        "use": "Low-loss, cellular towers, long Wi-Fi runs, ham radio",
        "atten": {100e6: 3.9, 400e6: 7.8, 900e6: 11.8, 2.4e9: 22.0, 5.8e9: 36.8},
    },
    "LMR-600": {
        "z0": 50, "vf": 0.87, "od_mm": 14.99,
        "cap_pf_m": 75.8, "shield": "foil+braid",
        "use": "Very low-loss, long cellular/Wi-Fi backbone, rooftop",
        "atten": {100e6: 2.7, 400e6: 5.4, 900e6: 8.1, 2.4e9: 14.3, 5.8e9: 24.0},
    },
}

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


def cmd_link_budget(args):
    """Calculate a complete RF link budget."""
    f = _parse_freq(args.freq)
    d = args.distance

    # Transmitter
    tx_power_dbm = args.tx_power  # dBm
    tx_cable_loss = args.tx_cable_loss if args.tx_cable_loss else 0  # dB
    tx_ant_gain = args.tx_gain if args.tx_gain else 0  # dBi

    # Receiver
    rx_cable_loss = args.rx_cable_loss if args.rx_cable_loss else 0  # dB
    rx_ant_gain = args.rx_gain if args.rx_gain else 0  # dBi
    rx_sensitivity = args.rx_sensitivity  # dBm (optional)

    # Additional losses
    misc_loss = args.misc_loss if args.misc_loss else 0  # dB

    # Calculate FSPL
    lam = C / f
    fspl_db = 20 * math.log10(4 * math.pi * d / lam)

    # EIRP = Tx Power - Tx Cable Loss + Tx Antenna Gain
    eirp = tx_power_dbm - tx_cable_loss + tx_ant_gain

    # Received power = EIRP - FSPL + Rx Antenna Gain - Rx Cable Loss - Misc Loss
    rx_power = eirp - fspl_db + rx_ant_gain - rx_cable_loss - misc_loss

    _header("Link Budget")

    print("  TRANSMITTER")
    _show("Tx Power", f"{tx_power_dbm:.1f} dBm  ({_eng(10**((tx_power_dbm-30)/10), 'W')})", 4)
    _show("Tx Cable Loss", f"-{tx_cable_loss:.1f} dB", 4)
    _show("Tx Antenna Gain", f"+{tx_ant_gain:.1f} dBi", 4)
    _show("EIRP", f"{eirp:.1f} dBm  ({_eng(10**((eirp-30)/10), 'W')})", 4)

    print()
    print("  PATH")
    _show("Frequency", _eng(f, "Hz"), 4)
    _show("Distance", _eng(d, "m"), 4)
    _show("Wavelength", _eng(lam, "m"), 4)
    _show("Free-Space Path Loss", f"-{fspl_db:.2f} dB", 4)
    if misc_loss > 0:
        _show("Miscellaneous Losses", f"-{misc_loss:.1f} dB", 4)

    print()
    print("  RECEIVER")
    _show("Rx Antenna Gain", f"+{rx_ant_gain:.1f} dBi", 4)
    _show("Rx Cable Loss", f"-{rx_cable_loss:.1f} dB", 4)

    print()
    print("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    _show("Received Power", f"{rx_power:.2f} dBm  ({_eng(10**((rx_power-30)/10), 'W')})", 2)

    if rx_sensitivity is not None:
        margin = rx_power - rx_sensitivity
        _show("Rx Sensitivity", f"{rx_sensitivity:.1f} dBm", 2)
        _show("Link Margin", f"{margin:.2f} dB", 2)
        if margin > 10:
            print(f"\n  ✅ Healthy link margin ({margin:.1f} dB > 10 dB)")
        elif margin > 0:
            print(f"\n  ⚠ Thin margin ({margin:.1f} dB) — may be unreliable in practice")
        else:
            print(f"\n  ❌ Link FAILS — {abs(margin):.1f} dB below sensitivity")

    # Show max range for this link
    if rx_sensitivity is not None:
        # Solve for max d where rx_power = rx_sensitivity
        # rx_power = eirp - 20*log10(4πd/λ) + rx_ant_gain - rx_cable_loss - misc_loss
        # => 20*log10(4πd/λ) = eirp + rx_ant_gain - rx_cable_loss - misc_loss - rx_sensitivity
        max_fspl = eirp + rx_ant_gain - rx_cable_loss - misc_loss - rx_sensitivity
        if max_fspl > 0:
            max_d = lam * 10 ** (max_fspl / 20) / (4 * math.pi)
            print(f"  📏 Maximum range: {_eng(max_d, 'm')} (0 dB margin)")


def cmd_fresnel(args):
    """Calculate Fresnel zone radius at any point along a path."""
    f = _parse_freq(args.freq)
    d_total = args.distance
    n = args.zone  # Fresnel zone number

    lam = C / f

    if args.point is not None:
        d1 = args.point
        d2 = d_total - d1
        if d1 <= 0 or d2 <= 0:
            print("Error: point must be between 0 and total distance")
            sys.exit(1)
        r_n = math.sqrt(n * lam * d1 * d2 / d_total)

        _header(f"Fresnel Zone {n}")
        _show("Frequency", _eng(f, "Hz"))
        _show("Total path", _eng(d_total, "m"))
        _show("Point at", _eng(d1, "m"))
        _show("Wavelength", _eng(lam, "m"))
        _show(f"F{n} radius at point", _eng(r_n, "m"))
        print(f"\n  60% clearance (practical minimum): {_eng(0.6 * r_n, 'm')}")
    else:
        # Max radius at midpoint
        d1 = d_total / 2
        d2 = d_total / 2
        r_n_max = math.sqrt(n * lam * d1 * d2 / d_total)

        _header(f"Fresnel Zone {n}")
        _show("Frequency", _eng(f, "Hz"))
        _show("Total path", _eng(d_total, "m"))
        _show("Wavelength", _eng(lam, "m"))
        _show(f"F{n} max radius (midpoint)", _eng(r_n_max, "m"))
        print(f"\n  60% clearance (practical minimum): {_eng(0.6 * r_n_max, 'm')}")

        # Show table of radii at 10%, 20%, ... 90%
        print(f"\n  Radius along path:")
        print(f"  {'Position':>10}  {'Distance':>10}  {'Radius':>10}")
        print(f"  {'─' * 10}  {'─' * 10}  {'─' * 10}")
        for pct in [10, 20, 30, 40, 50, 60, 70, 80, 90]:
            p_d1 = d_total * pct / 100
            p_d2 = d_total - p_d1
            r = math.sqrt(n * lam * p_d1 * p_d2 / d_total)
            print(f"  {pct:>9}%  {_eng(p_d1, 'm'):>10}  {_eng(r, 'm'):>10}")


def cmd_noise(args):
    """Calculate cascaded noise figure for a receiver chain."""
    # Parse stages: each stage is "gain_dB,nf_dB"
    stages = []
    for s in args.stages:
        parts = s.split(",")
        if len(parts) != 2:
            print(f"Error: stage '{s}' must be 'gain_dB,nf_dB' (e.g., '20,1.5')")
            sys.exit(1)
        gain_db, nf_db = float(parts[0]), float(parts[1])
        stages.append((gain_db, nf_db))

    if not stages:
        print("Error: at least one stage required")
        sys.exit(1)

    # Convert to linear
    gains_lin = [10 ** (g / 10) for g, _ in stages]
    nfs_lin = [10 ** (nf / 10) for _, nf in stages]

    # Friis noise formula: F_total = F1 + (F2-1)/G1 + (F3-1)/(G1*G2) + ...
    f_total = nfs_lin[0]
    cumulative_gain = gains_lin[0]
    for i in range(1, len(stages)):
        f_total += (nfs_lin[i] - 1) / cumulative_gain
        cumulative_gain *= gains_lin[i]

    nf_total_db = 10 * math.log10(f_total)
    total_gain_db = sum(g for g, _ in stages)

    # Noise temperature
    t_ref = args.t_ref if args.t_ref else 290  # K
    t_noise = t_ref * (f_total - 1)

    _header("Cascaded Noise Figure")

    print("  STAGES")
    print(f"  {'#':>3}  {'Gain (dB)':>10}  {'NF (dB)':>10}  {'Component':>15}")
    print(f"  {'─' * 3}  {'─' * 10}  {'─' * 10}  {'─' * 15}")
    for i, (g, nf) in enumerate(stages):
        label = args.labels[i] if args.labels and i < len(args.labels) else f"Stage {i+1}"
        print(f"  {i+1:>3}  {g:>+10.1f}  {nf:>10.1f}  {label:>15}")

    print()
    print("  RESULTS")
    _show("Total gain", f"{total_gain_db:+.1f} dB ({_eng(cumulative_gain, '')}x)")
    _show("Cascaded NF", f"{nf_total_db:.2f} dB (F = {f_total:.3f})")
    _show("Noise temperature", f"{t_noise:.1f} K (T_ref = {t_ref} K)")
    _show("Sensitivity impact", f"First stage dominates — its NF of {stages[0][1]:.1f} dB contributes most")

    if len(stages) >= 2:
        # Show what happens if we swap stages 1 and 2
        f_swapped = nfs_lin[1]
        f_swapped += (nfs_lin[0] - 1) / gains_lin[1]
        nf_swapped_db = 10 * math.log10(f_swapped)
        print(f"\n  ⚠ If stages 1 & 2 were swapped: NF would be {nf_swapped_db:.2f} dB"
              f" ({'worse' if nf_swapped_db > nf_total_db else 'better'} by"
              f" {abs(nf_swapped_db - nf_total_db):.2f} dB)")


def cmd_antenna(args):
    """Calculate antenna element lengths for common antenna types."""
    f = _parse_freq(args.freq)
    lam = C / f

    # Apply velocity factor if specified
    vf = args.vf if args.vf else 1.0

    _header("Antenna Calculator")
    _show("Frequency", _eng(f, "Hz"))
    _show("Free-space wavelength", _eng(lam, "m"))
    if vf != 1.0:
        _show("Velocity factor", f"{vf:.2f}")
        _show("Effective wavelength", _eng(lam * vf, "m"))

    lam_eff = lam * vf

    print()
    print("  ELEMENT LENGTHS")
    print(f"  {'Type':30s}  {'Length':>12}  {'Formula'}")
    print(f"  {'─' * 30}  {'─' * 12}  {'─' * 15}")

    elements = [
        ("Full wave (λ)", lam_eff, "λ"),
        ("Half-wave dipole (λ/2)", lam_eff / 2, "λ/2"),
        ("Quarter-wave monopole (λ/4)", lam_eff / 4, "λ/4"),
        ("5/8 wave (5λ/8)", 5 * lam_eff / 8, "5λ/8"),
        ("Folded dipole", lam_eff / 2, "λ/2"),
    ]

    for name, length, formula in elements:
        print(f"  {name:30s}  {_eng(length, 'm'):>12}  {formula}")

    # Practical wire antenna (with 0.95 correction factor)
    print()
    print("  PRACTICAL LENGTHS (×0.95 correction for wire thickness)")
    for name, length, formula in elements[:4]:
        print(f"  {name:30s}  {_eng(length * 0.95, 'm'):>12}")

    # Antenna impedance reference
    print()
    print("  REFERENCE IMPEDANCES")
    print(f"  {'Half-wave dipole':30s}  {'73 + j42.5 Ω (theoretical)':>30}")
    print(f"  {'Quarter-wave monopole':30s}  {'36.5 + j21.25 Ω (over ground)':>30}")
    print(f"  {'Folded dipole':30s}  {'292 Ω (4× half-wave)':>30}")
    print(f"  {'5/8 wave':30s}  {'~50 Ω (with matching network)':>30}")

    if args.gain:
        print()
        print("  THEORETICAL GAIN")
        print(f"  {'Isotropic':30s}  {'0 dBi'}")
        print(f"  {'Half-wave dipole':30s}  {'2.15 dBi'}")
        print(f"  {'Quarter-wave monopole':30s}  {'5.15 dBi (over perfect ground)'}")
        print(f"  {'5/8 wave':30s}  {'3.2 dBi'}")
        print(f"  {'Folded dipole':30s}  {'2.15 dBi'}")


def _interp_atten(atten_data: dict, freq: float) -> Optional[float]:
    """Interpolate attenuation from frequency/dB-per-100m data points."""
    freqs = sorted(atten_data.keys())
    if freq <= freqs[0]:
        # Extrapolate down using sqrt relationship (attenuation ∝ √f for skin effect)
        return atten_data[freqs[0]] * math.sqrt(freq / freqs[0])
    if freq >= freqs[-1]:
        return atten_data[freqs[-1]] * math.sqrt(freq / freqs[-1])

    # Find bracketing points and interpolate
    for i in range(len(freqs) - 1):
        if freqs[i] <= freq <= freqs[i + 1]:
            f1, f2 = freqs[i], freqs[i + 1]
            a1, a2 = atten_data[f1], atten_data[f2]
            # Log-linear interpolation
            ratio = math.log(freq / f1) / math.log(f2 / f1)
            return a1 + (a2 - a1) * ratio
    return None


def cmd_coax(args):
    """Look up coaxial cable specs and calculate loss at a given frequency/distance."""
    cable_name = args.cable.upper().replace("_", "-")

    # Try exact match first, then partial
    cable = None
    for name, data in COAX_DB.items():
        if name.upper() == cable_name:
            cable = (name, data)
            break

    if not cable:
        for name, data in COAX_DB.items():
            if cable_name in name.upper() or name.upper() in cable_name:
                cable = (name, data)
                break

    if not cable:
        if args.cable.lower() == "list":
            _header("Available Coaxial Cables")
            print(f"  {'Cable':<12} {'Z₀':>5} {'VF':>6} {'OD':>8} {'Use'}")
            print(f"  {'─'*12} {'─'*5} {'─'*6} {'─'*8} {'─'*40}")
            for name, data in COAX_DB.items():
                print(f"  {name:<12} {data['z0']:>4}Ω {data['vf']:>5.0%} {data['od_mm']:>6.2f}mm {data['use'][:40]}")
            print(f"\n  {len(COAX_DB)} cables in database. Use: rf-calc coax <name> [--freq F] [--length L]")
            return
        print(f"Error: cable '{args.cable}' not in database. Use 'rf-calc coax list' to see all.", file=sys.stderr)
        sys.exit(1)

    name, data = cable

    _header(f"Coaxial Cable: {name}")
    _show("Impedance Z₀", f"{data['z0']} Ω")
    _show("Velocity factor", f"{data['vf']:.0%}  (vₚ = {_eng(C * data['vf'], 'm/s')})")
    _show("Outer diameter", f"{data['od_mm']} mm")
    _show("Capacitance", f"{data['cap_pf_m']} pF/m")
    _show("Shielding", data['shield'])
    _show("Typical use", data['use'])

    # Attenuation table
    print()
    print("  Attenuation (dB/100m):")
    for freq, atten in sorted(data['atten'].items()):
        print(f"    {_eng(freq, 'Hz'):>10}: {atten:.1f} dB/100m")

    # If frequency specified, calculate at that frequency
    if args.freq:
        f = _parse_freq(args.freq)
        atten_100m = _interp_atten(data['atten'], f)
        vp = C * data['vf']
        wavelength = vp / f

        print()
        _show("At frequency", _eng(f, "Hz"))
        _show("Wavelength (in cable)", _eng(wavelength, "m"))

        if atten_100m is not None:
            _show("Attenuation", f"{atten_100m:.2f} dB/100m")

            if args.length:
                d = args.length
                total_loss = atten_100m * d / 100
                power_out = 10 ** (-total_loss / 10) * 100
                _show("Cable length", _eng(d, "m"))
                _show("Total loss", f"{total_loss:.2f} dB")
                _show("Power at far end", f"{power_out:.1f}% of input")
                _show("Electrical length", f"{d / wavelength:.2f}λ")

                # Compare with other cables at same freq/length
                print()
                print("  Cable comparison at same freq/length:")
                print(f"    {'Cable':<12} {'Loss':>8} {'Power out':>10} {'Z₀':>5}")
                print(f"    {'─'*12} {'─'*8} {'─'*10} {'─'*5}")
                comparisons = []
                for cname, cdata in COAX_DB.items():
                    if cdata['z0'] == data['z0']:  # same impedance family
                        ca = _interp_atten(cdata['atten'], f)
                        if ca:
                            cl = ca * d / 100
                            cp = 10 ** (-cl / 10) * 100
                            comparisons.append((cname, cl, cp, cdata['z0']))
                comparisons.sort(key=lambda x: x[1])
                for cname, cl, cp, cz in comparisons:
                    marker = " ◀" if cname == name else ""
                    print(f"    {cname:<12} {cl:>7.2f}dB {cp:>9.1f}% {cz:>4}Ω{marker}")


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
  rf-calc link-budget --freq 2.4G --distance 1000 --tx-power 20 --tx-gain 6 --rx-gain 3 --rx-sensitivity -80
  rf-calc fresnel --freq 5.8G --distance 10000     Fresnel zone for 10 km at 5.8 GHz
  rf-calc noise 20,1.5 -3,3 30,5 --labels LNA Filter Mixer  Cascaded noise figure
  rf-calc antenna --freq 146M --gain               2m ham antenna lengths + gains
  rf-calc coax list                      Show all cables in database
  rf-calc coax RG-58 --freq 2.4G        RG-58 specs + loss at 2.4 GHz
  rf-calc coax LMR-400 --freq 900M --length 30  Total loss for 30m LMR-400
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

    # link budget
    p = sub.add_parser("link-budget", help="Complete RF link budget calculator", aliases=["link"])
    p.add_argument("--freq", required=True, help="Frequency")
    p.add_argument("--distance", type=float, required=True, help="Distance (m)")
    p.add_argument("--tx-power", type=float, required=True, help="Transmitter power (dBm)")
    p.add_argument("--tx-gain", type=float, help="Tx antenna gain (dBi, default: 0)")
    p.add_argument("--tx-cable-loss", type=float, help="Tx cable loss (dB, default: 0)")
    p.add_argument("--rx-gain", type=float, help="Rx antenna gain (dBi, default: 0)")
    p.add_argument("--rx-cable-loss", type=float, help="Rx cable loss (dB, default: 0)")
    p.add_argument("--rx-sensitivity", type=float, help="Receiver sensitivity (dBm) — enables margin calc")
    p.add_argument("--misc-loss", type=float, help="Additional losses (dB, default: 0)")
    p.set_defaults(func=cmd_link_budget)

    # fresnel zone
    p = sub.add_parser("fresnel", help="Fresnel zone radius calculator")
    p.add_argument("--freq", required=True, help="Frequency")
    p.add_argument("--distance", type=float, required=True, help="Total path distance (m)")
    p.add_argument("--zone", type=int, default=1, help="Fresnel zone number (default: 1)")
    p.add_argument("--point", type=float, help="Distance from Tx to calculate radius (m). Default: show full table")
    p.set_defaults(func=cmd_fresnel)

    # noise figure
    p = sub.add_parser("noise", help="Cascaded noise figure (Friis formula)", aliases=["nf"])
    p.add_argument("stages", nargs="+", help="Stages as 'gain_dB,nf_dB' (e.g., '20,1.5' '-3,3' '30,5')")
    p.add_argument("--labels", nargs="+", help="Stage labels (e.g., 'LNA' 'Filter' 'Mixer')")
    p.add_argument("--t-ref", type=float, help="Reference temperature in K (default: 290)")
    p.set_defaults(func=cmd_noise)

    # antenna calculator
    p = sub.add_parser("antenna", help="Antenna element length calculator", aliases=["ant"])
    p.add_argument("--freq", required=True, help="Frequency")
    p.add_argument("--vf", type=float, help="Velocity factor (default: 1.0)")
    p.add_argument("--gain", action="store_true", help="Show theoretical gain table")
    p.set_defaults(func=cmd_antenna)

    # coaxial cable lookup
    p = sub.add_parser("coax", help="Coaxial cable specs + loss calculator (13 cables)", aliases=["cable"])
    p.add_argument("cable", help="Cable type (e.g., RG-58, LMR-400) or 'list'")
    p.add_argument("--freq", help="Frequency for loss calculation")
    p.add_argument("--length", type=float, help="Cable length in meters")
    p.set_defaults(func=cmd_coax)

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
