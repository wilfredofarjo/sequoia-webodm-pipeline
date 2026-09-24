#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sequoia Dataset Organizer v0.1.0

Organiza imágenes Parrot Sequoia almacenadas entre memoria interna y SD,
sin modificar los originales. Identifica GRE, RED, REG, NIR y RGB,
detecta duplicados exactos con SHA-256, separa capturas completas e
incompletas y, opcionalmente, asigna fechas reales mediante una bitácora
externa (JSON) para preparar carpetas listas para WebODM.

Python >= 3.9. No requiere paquetes externos.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

BANDS_REQUIRED = {"GRE", "RED", "REG", "NIR"}
IMAGE_EXTENSIONS = {".tif", ".tiff", ".jpg", ".jpeg"}
IGNORE_DIRS = {
    ".thumb",
    "__MACOSX",
    "Zip_Originales",
    "Sequoia_Organizado",
    "Sequoia_Final_WebODM",
}
SEQUOIA_RE = re.compile(
    r"^(?P<base>.+)_(?P<band>GRE|RED|REG|NIR|RGB)$",
    re.IGNORECASE,
)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def identify_band(path: Path):
    match = SEQUOIA_RE.match(path.stem)
    if not match:
        return None, None
    return match.group("base"), match.group("band").upper()


def is_ignored(path: Path) -> bool:
    return any(part in IGNORE_DIRS for part in path.parts)


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def copy_safe(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        shutil.copy2(source, destination)
        return destination

    counter = 2
    while True:
        candidate = destination.with_name(
            f"{destination.stem}_{counter}{destination.suffix}"
        )
        if not candidate.exists():
            shutil.copy2(source, candidate)
            return candidate
        counter += 1


def validate_roots(base: Path) -> tuple[Path, Path]:
    internal = base / "Interna"
    sd = base / "SD"

    missing = [str(p) for p in (internal, sd) if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "No se encontraron las carpetas requeridas: " + ", ".join(missing)
        )
    return internal, sd


def inventory_source(source_name: str, root: Path) -> tuple[list[dict], list[dict]]:
    records = []
    unrecognized = []

    for path in root.rglob("*"):
        if is_ignored(path) or not path.is_file():
            continue

        ext = path.suffix.lower()
        if ext not in IMAGE_EXTENSIONS:
            continue

        base_name, band = identify_band(path)
        relative = path.relative_to(root)
        folder = relative.parent.name if str(relative.parent) != "." else "RAIZ"

        if band is None:
            unrecognized.append({
                "source": source_name,
                "folder": folder,
                "original_name": path.name,
                "original_path": str(path),
                "size_bytes": path.stat().st_size,
            })
            continue

        # Las bandas multiespectrales originales deben ser TIFF.
        # GRE/RED/REG/NIR en JPG suelen ser miniaturas.
        if band in BANDS_REQUIRED and ext not in {".tif", ".tiff"}:
            continue

        records.append({
            "source": source_name,
            "folder": folder,
            "base_name": base_name,
            "band": band,
            "extension": ext,
            "original_name": path.name,
            "original_path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })

    return records, unrecognized


def deduplicate(records: list[dict]) -> tuple[list[dict], list[dict]]:
    by_hash = defaultdict(list)
    for row in records:
        by_hash[row["sha256"]].append(row)

    unique = []
    duplicates = []

    for digest, items in by_hash.items():
        unique.append(items[0])
        if len(items) > 1:
            for item in items:
                duplicates.append({
                    "sha256": digest,
                    "source": item["source"],
                    "folder": item["folder"],
                    "band": item["band"],
                    "original_name": item["original_name"],
                    "original_path": item["original_path"],
                })

    return unique, duplicates


def folder_sort_key(folder: str):
    if folder.isdigit():
        return (0, int(folder))
    return (1, folder.lower())


def group_captures(records: list[dict]) -> tuple[list[dict], dict[str, dict]]:
    grouped = defaultdict(list)

    # Fuente forma parte de la identidad: INTERNA y SD no se mezclan.
    for row in records:
        key = (row["source"], row["folder"], row["base_name"])
        grouped[key].append(row)

    captures = []
    capture_lookup = {}

    ordered = sorted(
        grouped.items(),
        key=lambda item: (
            0 if item[0][0] == "INTERNA" else 1,
            folder_sort_key(item[0][1]),
            item[0][2].lower(),
        ),
    )

    for index, ((source, folder, base_name), items) in enumerate(ordered, start=1):
        capture_id = f"CAP_{index:06d}"
        by_band = defaultdict(list)
        for item in items:
            by_band[item["band"]].append(item)

        conflicts = {
            band: vals for band, vals in by_band.items()
            if len({v["sha256"] for v in vals}) > 1
        }

        selected = {}
        for band, vals in by_band.items():
            if band in conflicts:
                continue
            selected[band] = vals[0]

        present = set(selected)
        missing = sorted(BANDS_REQUIRED - present)
        complete = not missing and not conflicts

        row = {
            "capture_id": capture_id,
            "source": source,
            "folder": folder,
            "base_name": base_name,
            "complete": "YES" if complete else "NO",
            "conflict": "YES" if conflicts else "NO",
            "GRE": "YES" if "GRE" in present else "NO",
            "RED": "YES" if "RED" in present else "NO",
            "REG": "YES" if "REG" in present else "NO",
            "NIR": "YES" if "NIR" in present else "NO",
            "RGB": "YES" if "RGB" in present else "NO",
            "missing_bands": ",".join(missing),
            "conflict_bands": ",".join(sorted(conflicts)),
        }

        captures.append(row)
        capture_lookup[capture_id] = {
            "metadata": row,
            "selected": selected,
        }

    return captures, capture_lookup


def load_session_rules(path: Path | None) -> dict:
    if path is None:
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def assign_real_date(capture: dict, rules: dict) -> str:
    """
    Reglas JSON:
    {
      "2026-05-28": [
        {"source": "INTERNA", "folder_start": 51, "folder_end": 215}
      ]
    }
    """
    source = capture["source"]
    folder = capture["folder"]
    if not folder.isdigit():
        return ""

    folder_number = int(folder)

    for date, blocks in rules.items():
        for block in blocks:
            if source != str(block["source"]).upper():
                continue
            start = int(block["folder_start"])
            end = int(block["folder_end"])
            if start <= folder_number <= end:
                return date
    return ""


def build_final_manifest(
    captures: list[dict],
    lookup: dict[str, dict],
    session_rules: dict,
    final_root: Path,
) -> tuple[list[dict], list[dict]]:
    manifest = []
    summary = defaultdict(lambda: {
        "total": 0,
        "complete": 0,
        "incomplete": 0,
        "rgb": 0,
    })

    for capture in captures:
        date = assign_real_date(capture, session_rules)
        session = f"Sesion_{date}" if date else "Sesion_Sin_Fecha"
        selected = lookup[capture["capture_id"]]["selected"]
        complete = capture["complete"] == "YES"

        summary[date or "SIN_FECHA"]["total"] += 1
        summary[date or "SIN_FECHA"]["complete" if complete else "incomplete"] += 1
        if "RGB" in selected:
            summary[date or "SIN_FECHA"]["rgb"] += 1

        for band in ("GRE", "RED", "REG", "NIR"):
            item = selected.get(band)
            if item is None:
                continue

            name = f"{capture['capture_id']}_{band}.TIF"
            if complete:
                destination = (
                    final_root / session / "WebODM_Multiespectral" / name
                )
                state = "READY_WEBODM"
            else:
                destination = (
                    final_root
                    / "Capturas_Incompletas"
                    / session
                    / capture["capture_id"]
                    / name
                )
                state = "INCOMPLETE"

            manifest.append({
                "capture_id": capture["capture_id"],
                "real_date": date,
                "session": session,
                "source": capture["source"],
                "folder": capture["folder"],
                "band": band,
                "complete": capture["complete"],
                "state": state,
                "original_name": item["original_name"],
                "original_path": item["original_path"],
                "sha256": item["sha256"],
                "final_name": name,
                "destination": str(destination),
            })

        rgb = selected.get("RGB")
        if rgb is not None:
            name = f"{capture['capture_id']}_RGB.JPG"
            destination = final_root / session / "RGB_Referencia" / name
            manifest.append({
                "capture_id": capture["capture_id"],
                "real_date": date,
                "session": session,
                "source": capture["source"],
                "folder": capture["folder"],
                "band": "RGB",
                "complete": capture["complete"],
                "state": "RGB_REFERENCE",
                "original_name": rgb["original_name"],
                "original_path": rgb["original_path"],
                "sha256": rgb["sha256"],
                "final_name": name,
                "destination": str(destination),
            })

    summary_rows = []
    for date in sorted(summary):
        values = summary[date]
        summary_rows.append({
            "real_date": date,
            "captures_total": values["total"],
            "captures_complete": values["complete"],
            "captures_incomplete": values["incomplete"],
            "captures_with_rgb": values["rgb"],
            "webodm_tiff_count": values["complete"] * 4,
        })

    return manifest, summary_rows


def copy_final_dataset(
    manifest: list[dict],
    copy_rgb: bool,
    copy_incomplete: bool,
) -> int:
    copied = 0
    for row in manifest:
        state = row["state"]

        if state == "RGB_REFERENCE" and not copy_rgb:
            continue
        if state == "INCOMPLETE" and not copy_incomplete:
            continue
        if state not in {"READY_WEBODM", "RGB_REFERENCE", "INCOMPLETE"}:
            continue

        copy_safe(Path(row["original_path"]), Path(row["destination"]))
        copied += 1

    return copied


def parse_args():
    parser = argparse.ArgumentParser(
        description="Organiza imágenes Parrot Sequoia y prepara datasets para WebODM."
    )
    parser.add_argument(
        "--base",
        required=True,
        help="Carpeta que contiene Interna/ y SD/.",
    )
    parser.add_argument(
        "--output",
        help="Salida de reportes. Por defecto: <base>/Sequoia_Organizado",
    )
    parser.add_argument(
        "--session-map",
        help="JSON opcional para asignar fechas reales por fuente/rango de carpetas.",
    )
    parser.add_argument(
        "--copy-final",
        action="store_true",
        help="Copia el dataset final. Sin esta opción solo genera reportes.",
    )
    parser.add_argument(
        "--no-rgb",
        action="store_true",
        help="No copiar RGB de referencia.",
    )
    parser.add_argument(
        "--no-incomplete",
        action="store_true",
        help="No copiar capturas incompletas.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    base = Path(args.base).expanduser().resolve()
    output = (
        Path(args.output).expanduser().resolve()
        if args.output
        else base / "Sequoia_Organizado"
    )
    reports = output / "Reportes"
    final_root = output / "Sequoia_Final_WebODM"

    internal, sd = validate_roots(base)

    print("=" * 68)
    print("SEQUOIA DATASET ORGANIZER v0.1.0")
    print("=" * 68)
    print("Modo:", "COPIA FINAL" if args.copy_final else "DIAGNÓSTICO")
    print()

    all_records = []
    all_unrecognized = []

    for source_name, root in (("INTERNA", internal), ("SD", sd)):
        print(f"Inventariando {source_name}...")
        records, unrecognized = inventory_source(source_name, root)
        all_records.extend(records)
        all_unrecognized.extend(unrecognized)

    unique_records, duplicates = deduplicate(all_records)
    captures, lookup = group_captures(unique_records)

    rules = load_session_rules(
        Path(args.session_map).expanduser().resolve()
        if args.session_map else None
    )

    manifest, final_summary = build_final_manifest(
        captures,
        lookup,
        rules,
        final_root,
    )

    write_csv(
        reports / "captures.csv",
        captures,
        [
            "capture_id", "source", "folder", "base_name", "complete",
            "conflict", "GRE", "RED", "REG", "NIR", "RGB",
            "missing_bands", "conflict_bands",
        ],
    )

    write_csv(
        reports / "duplicates.csv",
        duplicates,
        [
            "sha256", "source", "folder", "band",
            "original_name", "original_path",
        ],
    )

    write_csv(
        reports / "unrecognized.csv",
        all_unrecognized,
        [
            "source", "folder", "original_name",
            "original_path", "size_bytes",
        ],
    )

    write_csv(
        reports / "final_manifest.csv",
        manifest,
        [
            "capture_id", "real_date", "session", "source", "folder",
            "band", "complete", "state", "original_name", "original_path",
            "sha256", "final_name", "destination",
        ],
    )

    write_csv(
        reports / "summary_by_real_date.csv",
        final_summary,
        [
            "real_date", "captures_total", "captures_complete",
            "captures_incomplete", "captures_with_rgb",
            "webodm_tiff_count",
        ],
    )

    complete_count = sum(c["complete"] == "YES" for c in captures)
    incomplete_count = len(captures) - complete_count

    print()
    print(f"Imágenes reconocidas: {len(all_records)}")
    print(f"Archivos únicos: {len(unique_records)}")
    print(f"Duplicados exactos: {len(duplicates)} registros")
    print(f"Capturas: {len(captures)}")
    print(f"Capturas completas: {complete_count}")
    print(f"Capturas incompletas: {incomplete_count}")
    print(f"Reportes: {reports}")

    if args.copy_final:
        if not rules:
            print(
                "ERROR: --copy-final requiere --session-map para evitar "
                "copiar imágenes sin fecha experimental validada.",
                file=sys.stderr,
            )
            return 2

        copied = copy_final_dataset(
            manifest,
            copy_rgb=not args.no_rgb,
            copy_incomplete=not args.no_incomplete,
        )
        print(f"Archivos copiados: {copied}")
        print(f"Dataset final: {final_root}")
    else:
        print("No se modificaron ni copiaron fotografías.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
