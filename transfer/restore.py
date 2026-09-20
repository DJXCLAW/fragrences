#!/usr/bin/env python3
"""Restore the original Fragrance Atlas project from its verified transfer bundle.

This uses only the Python standard library. The bundle is a transport copy,
not the editable source: after the initial import, edit the root website files.
Existing files with different content are never overwritten.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import lzma
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent.parent
TRANSFER = ROOT / 'transfer'
WORKBOOK = 'downloads/Fragrance_Atlas_72_Colognes.xlsx'
EXPECTED_PATHS = {
    '.gitignore', '.nojekyll', 'START_PREVIEW.bat', 'QA.md',
    'qa-results.json', 'server.cjs', 'package.json', 'index.html',
    'preview.html', 'assets/styles.css', 'assets/app.js',
    'assets/data.js', 'downloads/fragrances.json', WORKBOOK,
}
ZIP_ATTRIBUTES = [
    'compress_type', 'create_system', 'create_version', 'extract_version',
    'reserved', 'flag_bits', 'volume', 'internal_attr', 'external_attr',
]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    manifest = json.loads((TRANSFER / 'ready.json').read_text(encoding='utf-8'))
    parts = manifest['parts']
    if not parts or len(parts) > 32 or len(set(parts)) != len(parts):
        raise ValueError('Invalid transfer parts')
    chunks = []
    for name in parts:
        if Path(name).name != name or not name.startswith('part-') or not name.endswith('.b64'):
            raise ValueError('Invalid transfer part path')
        chunks.append((TRANSFER / name).read_text(encoding='ascii').strip())
    compressed = base64.b64decode(''.join(chunks), validate=True)
    if digest(compressed) != manifest['compressed_sha256']:
        raise ValueError('Transfer checksum mismatch; no website files were written')
    raw = lzma.decompress(compressed)
    if len(raw) != manifest['payload_bytes'] or digest(raw) != manifest['payload_sha256']:
        raise ValueError('Payload checksum mismatch; no website files were written')
    payload = json.loads(raw)
    outputs = {name: text.encode('utf-8') for name, text in payload['texts'].items()}
    buffer = io.BytesIO()
    with ZipFile(buffer, 'w', ZIP_DEFLATED, compresslevel=6) as archive:
        archive.comment = base64.b64decode(payload['workbook_comment'], validate=True)
        for entry in payload['workbook_entries']:
            info = ZipInfo(entry['filename'], tuple(entry['date_time']))
            for attribute in ZIP_ATTRIBUTES:
                setattr(info, attribute, entry[attribute])
            info.comment = base64.b64decode(entry['comment'], validate=True)
            info.extra = base64.b64decode(entry['extra'], validate=True)
            archive.writestr(info, entry['text'].encode('utf-8'), compresslevel=6)
    outputs[WORKBOOK] = buffer.getvalue()
    placeholder = b'__FRAGRANCE_ATLAS_WORKBOOK_BASE64__'
    if outputs['preview.html'].count(placeholder) != 1:
        raise ValueError('Invalid preview template')
    outputs['preview.html'] = outputs['preview.html'].replace(
        placeholder, base64.b64encode(outputs[WORKBOOK])
    )
    if set(outputs) != EXPECTED_PATHS or set(payload['sha256']) != EXPECTED_PATHS:
        raise ValueError('Unexpected output file set')
    if len(outputs) != manifest['output_files']:
        raise ValueError('Unexpected output file count')
    # Validate the complete set before touching any website files.
    for name, contents in outputs.items():
        if digest(contents) != payload['sha256'][name]:
            raise ValueError(f'Original-file checksum mismatch: {name}')
        destination = (ROOT / name).resolve()
        if not destination.is_relative_to(ROOT):
            raise ValueError(f'Unsafe output path: {name}')
        if destination.exists() and destination.read_bytes() != contents:
            raise FileExistsError(f'Refusing to overwrite an edited file: {name}')
    for name, contents in outputs.items():
        destination = ROOT / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(contents)
        print(f'Verified and restored: {name} ({len(contents):,} bytes)')
    print(f'Success: all {len(outputs)} original project files match their SHA-256 checksums.')


if __name__ == '__main__':
    main()
