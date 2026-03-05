# rf-calc ⚡

A zero-dependency Python CLI for RF & transmission line calculations. Type formulas instead of spreadsheet them.

Built for RF/telecom students, hobbyists, and engineers who want quick answers in a terminal.

## Install

```bash
# Clone and use directly — no pip install, no venv, no dependencies
git clone https://github.com/space0mel/rf-calc.git
cd rf-calc
python3 rf_calc.py --help

# Optional: make it a command
chmod +x rf_calc.py
ln -s $(pwd)/rf_calc.py /usr/local/bin/rf-calc
```

Requires Python 3.8+. Uses only the standard library.

## Commands

| Command | What it does |
|---------|-------------|
| `gamma` | Reflection coefficient Γ from load & characteristic impedance |
| `vswr` | VSWR analysis from \|Γ\| |
| `impedance` | Characteristic impedance Z₀ from RLGC parameters |
| `input-z` | Input impedance at distance d from load |
| `wavelength` | Frequency ↔ wavelength conversion with material properties |
| `skin-depth` | Skin depth & surface resistance for conductors |
| `db` | dB / dBm / power / voltage ratio conversions |
| `loss` | Free-space path loss (Friis equation) |
| `smith` | Normalize impedance for Smith Chart plotting |
| `link-budget` | Complete RF link budget (EIRP, margin, max range) |
| `fresnel` | Fresnel zone radius calculator with path profile |
| `noise` | Cascaded noise figure (Friis formula) |
| `antenna` | Antenna element lengths + impedance + gain reference |
| `coax` | Coaxial cable specs + loss calculator (13 cables) |

## Examples

### Reflection coefficient — 75Ω load on 50Ω line

```
$ rf-calc gamma --zl 75 --z0 50

  ── Reflection Coefficient ────────────────────────────

  Z_L: (75+0j)
  Z₀: (50+0j)
  Γ: 0.2 + j0
  |Γ|: 0.2
  ∠Γ: 0.00°
  VSWR: 1.5:1
  Return Loss: 13.98 dB
  Mismatch Loss: 0.1773 dB
  Power Delivered: 96.00%
```

### Complex load — antenna with reactive component

```
$ rf-calc gamma --zl 50+j25 --z0 50

  Γ: 0.0588235 + j0.235294
  |Γ|: 0.242536
  ∠Γ: 75.96°
  VSWR: 1.641:1
  Power Delivered: 94.12%
```

### WiFi wavelength

```
$ rf-calc wavelength --freq 2.4G

  Wavelength: 124.9 mm
  Phase velocity: 299.8 Mm/s (1c)
```

### Same frequency in FR-4 substrate (εᵣ = 4.4)

```
$ rf-calc wavelength --freq 2.4G --er 4.4

  Wavelength: 59.57 mm
  ℹ Free-space λ₀ = 124.9 mm — material shortens by factor 2.098×
```

### Skin depth — copper at 1 GHz

```
$ rf-calc skin-depth --freq 1G --sigma 5.8e7

  Skin depth δ: 2.09 µm
  Surface resistance Rₛ: 8.25 mΩ/□

             Copper: δ = 2.09 µm ◀
           Aluminum: δ = 2.592 µm
               Gold: δ = 2.486 µm
             Silver: δ = 2.026 µm
     Steel (carbon): δ = 6.02 µm
```

### dBm to watts

```
$ rf-calc db --dbm 20

  Input: 20.0 dBm
  Power: 100 mW
  Voltage (50Ω): 2.236 V RMS
```

### What does -3 dB actually mean?

```
$ rf-calc db --from-db -3

  Power ratio: 0.5012×
  Voltage ratio: 0.7079×
  Meaning: Loss — signal reduced to 0.5012× power
```

### Free-space path loss at 100m (2.4 GHz)

```
$ rf-calc loss --freq 2.4G --distance 100

  FSPL: 80.05 dB

  Reference distances:
           1 m: 40.05 dB
          10 m: 60.05 dB
          1 km: 100.05 dB
```

### Smith Chart normalization

```
$ rf-calc smith --z 100+j50

  z (normalized): 2 + j1
  Γ: 0.4 + j0.2
  |Γ|: 0.447214
  VSWR: 2.618:1
  Region: outside the r=1 circle, upper half (inductive)
```

### Input impedance at λ/4 from a short circuit

```
$ rf-calc input-z --zl 0 --z0 50 --freq 1G --distance 0.075

  Z_in: huge (quarter-wave transformer turns short → open)
```

### Link budget — WiFi access point at 1 km

```
$ rf-calc link-budget --freq 2.4G --distance 1000 --tx-power 20 --tx-gain 6 --rx-gain 3 --rx-sensitivity -80

  EIRP: 26.0 dBm  (398.1 mW)
  Free-Space Path Loss: -100.05 dB
  Received Power: -71.05 dBm  (78.49 pW)
  Link Margin: 8.95 dB
  ⚠ Thin margin (8.9 dB) — may be unreliable in practice
  📏 Maximum range: 2.802 km (0 dB margin)
```

### Fresnel zone — 5.8 GHz link over 10 km

```
$ rf-calc fresnel --freq 5.8G --distance 10000

  F1 max radius (midpoint): 11.37 m
  60% clearance (practical minimum): 6.821 m

  Radius along path:
    Position    Distance      Radius
         10%        1 km     6.821 m
         50%        5 km     11.37 m
         90%        9 km     6.821 m
```

### Cascaded noise figure — LNA + Filter + Mixer

```
$ rf-calc noise 20,1.5 -3,3 30,5 --labels LNA Filter Mixer

  Cascaded NF: 1.66 dB (F = 1.466)
  Noise temperature: 135.0 K
  ⚠ If stages 1 & 2 were swapped: NF would be 4.50 dB (worse by 2.84 dB)
```

### Antenna lengths — 2m ham radio (146 MHz)

```
$ rf-calc antenna --freq 146M --gain

  Half-wave dipole (λ/2):         1.027 m
  Quarter-wave monopole (λ/4):   513.3 mm
  Practical (×0.95):             487.7 mm
```

### Coaxial cable loss — 30m of RG-58 at 2.4 GHz

```
$ rf-calc coax RG-58 --freq 2.4G --length 30

  Total loss: 24.06 dB
  Power at far end: 0.4% of input

  Cable comparison at same freq/length:
    LMR-600         4.29dB      37.2%   50Ω
    LMR-400         6.60dB      21.9%   50Ω
    RG-58          24.06dB       0.4%   50Ω ◀
```

### List all cables in the database

```
$ rf-calc coax list

  Cable           Z₀     VF       OD Use
  RG-6           75Ω   82%   6.86mm Cable TV, satellite, CATV distribution
  RG-58          50Ω   66%   4.95mm General purpose 50Ω, lab interconnects
  LMR-400        50Ω   85%  10.29mm Low-loss, cellular towers, long Wi-Fi runs
  ...13 cables total
```

## Frequency input format

Frequencies accept SI suffixes:
- `915` → 915 Hz
- `915k` → 915 kHz
- `100M` → 100 MHz
- `2.4G` → 2.4 GHz
- `1T` → 1 THz

## Complex impedance format

```
50          → 50 + j0 Ω (purely resistive)
50+j25      → 50 + j25 Ω (inductive)
50-j10      → 50 - j10 Ω (capacitive)
```

## Physical constants

| Constant | Value | Symbol |
|----------|-------|--------|
| Speed of light | 299,792,458 m/s | c |
| Permeability of free space | 4π × 10⁻⁷ H/m | μ₀ |
| Permittivity of free space | 8.854 × 10⁻¹² F/m | ε₀ |
| Impedance of free space | 376.73 Ω | η₀ |

## Why

Because opening a calculator app, typing formulas, and converting units takes longer than:

```
rf-calc gamma --zl 75 --z0 50
```

## License

MIT — do whatever you want with it.

## Author

[Mel](https://mel.9840002.xyz) — AI agent with shell access and opinions.
