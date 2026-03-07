# Modulation Calculator Feature (Planned v1.4.0)

## Overview

Add comprehensive modulation calculations to rf-calc, directly supporting Modulation course content.

## New Command: `modulation`

### Features

**Analog Modulation:**
- AM bandwidth (double sideband): `BW = 2 × fm`
- FM bandwidth (Carson's rule): `BW ≈ 2(Δf + fm) = 2fm(β + 1)`
- Modulation index calculations

**Digital Modulation:**
- Symbol rate ↔ bit rate conversions
- Bandwidth calculations (Nyquist + occupied with raised cosine filter)
- Spectral efficiency (bits/s/Hz)
- Support for: BPSK, QPSK, 8PSK, 16PSK, 16QAM, 32QAM, 64QAM, 128QAM, 256QAM, ASK, FSK

**Usage Examples:**

```bash
# AM bandwidth calculation
rf-calc modulation --type am --message-freq 5k
# Output: BW = 10.000 kHz (2 × 5 kHz)

# FM bandwidth (Carson's rule)
rf-calc modulation --type fm --message-freq 15k --deviation 75k
# Output: β = 5.00, BW = 180.000 kHz

# Digital modulation bandwidth + spectral efficiency
rf-calc modulation --type digital --scheme qpsk --bitrate 1M
# Output: Rs = 500 ksps, Nyquist BW = 250 kHz, Occupied BW = 675 kHz (α=0.35), η = 1.48 bits/s/Hz

# Compare modulation schemes
rf-calc modulation --compare --bitrate 1M
# Output: table comparing BPSK/QPSK/8PSK/16QAM/64QAM/256QAM at 1 Mbps
```

## Implementation Details

**Functions to add:**
- `am_bandwidth(fm)` — returns 2 * fm
- `fm_bandwidth_carson(fm, beta)` — returns 2 * fm * (beta + 1)
- `nyquist_bandwidth(symbol_rate)` — returns Rs / 2
- `occupied_bandwidth(symbol_rate, rolloff=0.35)` — returns Rs * (1 + α)
- `spectral_efficiency(bits_per_symbol, rolloff=0.35)` — returns k / (1 + α)
- `bits_per_symbol(scheme)` — lookup table for common schemes
- `symbol_rate_from_bitrate(bitrate, k)` — returns Rb / k
- `bitrate_from_symbol_rate(symbol_rate, k)` — returns Rs * k

**Comparison Table Format:**
```
MODULATION SCHEME COMPARISON (1 Mbps)
============================================================
Scheme     k   Rs (ksps)    BW (kHz)     η (b/s/Hz)
------------------------------------------------------------
BPSK       1   1000.0       1350.0       0.74      
QPSK       2   500.0        675.0        1.48      
8PSK       3   333.3        450.0        2.22      
16QAM      4   250.0        337.5        2.96      
64QAM      6   166.7        225.0        4.44      
256QAM     8   125.0        168.8        5.93      
```

## Course Relevance

**Directly supports Modulation et traitement de signal (2434K5EM):**
- Carson's rule for FM bandwidth (lecture topic)
- Digital modulation schemes (ASK/FSK/PSK/QAM)
- Symbol rate / bit rate relationships
- Spectral efficiency trade-offs
- Raised cosine filter parameters (α = rolloff factor)

**Real-world applications:**
- Wi-Fi channel planning (compare schemes at given bandwidth)
- Cellular link budget (bandwidth ↔ data rate trade-offs)
- Ham radio FM (narrowband vs. wideband, β selection)
- LoRa/Meshtastic (spreading factor affects spectral efficiency)

## Prototype

Working prototype tested and validated at `/tmp/rf_calc_modulation_feature.py`.

Example output shows:
- AM DSB: 5 kHz message → 10 kHz BW ✓
- FM Carson: 15 kHz message + 75 kHz deviation (β=5) → 180 kHz BW ✓
- QPSK @ 1 Mbps: Rs = 500 ksps, occupied BW = 675 kHz, η = 1.48 bits/s/Hz ✓
- 16-QAM @ 1 Mbps: Rs = 250 ksps, occupied BW = 337.5 kHz, η = 2.96 bits/s/Hz ✓

## Next Steps

1. Integrate functions into `rf_calc.py`
2. Add argparse subcommand `modulation` with flags:
   - `--type {am,fm,digital}`
   - `--scheme {bpsk,qpsk,8psk,16qam,64qam,256qam}`
   - `--bitrate`, `--message-freq`, `--deviation`, `--rolloff`
   - `--compare` (comparison table mode)
3. Update README with modulation examples
4. Add to reference page at mel.9840002.xyz/rf-calc/
5. Tag v1.4.0 and push to GitHub

## Design Notes

- Zero external dependencies (stdlib only, consistent with rf-calc philosophy)
- Engineering notation output (format_freq, format_bps)
- Raised cosine α=0.35 as default (industry standard, practical)
- Includes educational notes (Nyquist vs. occupied BW, SNR trade-offs)
- Comparison table helps with scheme selection decisions

---

Built: March 6, 2026
Prototype location: `/tmp/rf_calc_modulation_feature.py`
Target version: v1.4.0
