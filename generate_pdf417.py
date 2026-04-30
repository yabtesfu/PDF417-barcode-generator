"""
PDF417 background-style barcode generator.

Produces a wide, short, dense PDF417 barcode in the style of the reference
image: many columns, few rows, high error-correction level so the codeword
grid looks like noise between the start/stop bars.

Usage:
    python generate_pdf417.py                      # defaults
    python generate_pdf417.py --text "hello world"
    python generate_pdf417.py --columns 30 --rows-target 6 --scale 3 --ratio 4
"""

import argparse
import random
import string
from pathlib import Path

from pdf417gen import encode, render_image


# PDF417 hard limit on total codewords (data + EC + descriptor).
MAX_CODEWORDS = 928
EC_CODEWORDS = {n: 2 ** (n + 1) for n in range(9)}  # level n -> 2^(n+1)


def random_payload(n_chars: int) -> str:
    alphabet = string.ascii_letters + string.digits + " ./-"
    return "".join(random.choices(alphabet, k=n_chars))


def fit_payload(columns: int, rows_target: int, security_level: int) -> str:
    """Return a random payload sized so the rendered barcode has roughly
    `rows_target` rows at the given column count and EC level.

    PDF417 packs ~1.2 bytes per codeword for binary data; we under-fill by 10%
    to leave headroom for the length descriptor and any compaction overhead.
    """
    total_codewords = columns * rows_target
    data_codewords = total_codewords - EC_CODEWORDS[security_level] - 1
    if data_codewords <= 0:
        raise ValueError("rows_target too small for the chosen EC level")
    if total_codewords > MAX_CODEWORDS:
        raise ValueError(
            f"columns*rows_target={total_codewords} exceeds PDF417 max {MAX_CODEWORDS}"
        )
    n_chars = max(1, int(data_codewords * 1.2 * 0.9))
    return random_payload(n_chars)


def build_barcode(text, columns, security_level, scale, ratio):
    codes = encode(text, columns=columns, security_level=security_level)
    return render_image(codes, scale=scale, ratio=ratio, padding=2)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--text", default=None,
                   help="Payload to encode. If omitted, a random payload is "
                        "generated to roughly fill the requested grid.")
    p.add_argument("--columns", type=int, default=20,
                   help="PDF417 data columns (1..30). More = wider.")
    p.add_argument("--rows-target", type=int, default=8,
                   help="Target row count when auto-sizing the random payload.")
    p.add_argument("--security-level", type=int, default=4,
                   help="Reed-Solomon EC level 0..8. Higher = more codewords.")
    p.add_argument("--scale", type=int, default=3,
                   help="Pixel size of one module.")
    p.add_argument("--ratio", type=int, default=3,
                   help="Module height-to-width ratio (PDF417 modules are tall).")
    p.add_argument("--seed", type=lambda s: int(s, 0), default=0xBA7C0DE)
    p.add_argument("--output", default="pdf417_background.png")
    args = p.parse_args()

    random.seed(args.seed)
    text = args.text or fit_payload(args.columns, args.rows_target,
                                    args.security_level)
    img = build_barcode(text, args.columns, args.security_level,
                        args.scale, args.ratio)

    out = Path(__file__).with_name(args.output)
    img.save(out)
    print(f"wrote {out}  ({img.width}x{img.height})  "
          f"text_len={len(text)}  cols={args.columns}  ec={args.security_level}")


if __name__ == "__main__":
    main()
