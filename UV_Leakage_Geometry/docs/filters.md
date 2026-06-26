# Filter Reference

All filter transmission curves are in `filters/`. Used by synphot via `SpectralElement.from_file()`.

| File | Survey | Band | Pivot λ (Å) | System |
|---|---|---|---|---|
| GALEX_GALEX.FUV.dat | GALEX | FUV | 1549 | AB |
| GALEX_GALEX.NUV.dat | GALEX | NUV | 2303 | AB |
| PAN-STARRS_PS1.g.dat | PanSTARRS | g | 4810 | AB |
| PAN-STARRS_PS1.r.dat | PanSTARRS | r | 6170 | AB |
| PAN-STARRS_PS1.i.dat | PanSTARRS | i | 7520 | AB |
| PAN-STARRS_PS1.z.dat | PanSTARRS | z | 8660 | AB |
| PAN-STARRS_PS1.y.dat | PanSTARRS | y | 9620 | AB |
| PAN-STARRS_PS1.w.dat | PanSTARRS | w (wide) | — | AB |
| UKIRT_UKIDSS.Y.dat | UKIDSS | Y | 10305 | Vega (+0.634) |
| UKIRT_UKIDSS.Z.dat | UKIDSS | Z | — | Vega |
| UKIRT_UKIDSS.J.dat | UKIDSS | J | 12483 | Vega (+0.938) |
| UKIRT_UKIDSS.H.dat | UKIDSS | H | 16313 | Vega (+1.379) |
| UKIRT_UKIDSS.K.dat | UKIDSS | K | 22010 | Vega (+1.900) |
| WISE_WISE.W1.dat | WISE | W1 | 33680 | Vega (+2.699) |
| WISE_WISE.W2.dat | WISE | W2 | 46180 | Vega (+3.339) |
| WISE_WISE.W3.dat | WISE | W3 | 120820 | Vega (+5.174) |
| WISE_WISE.W4.dat | WISE | W4 | 221940 | Vega (+6.620) |

Vega-to-AB offsets are added to the Vega magnitude before converting to F_λ.
