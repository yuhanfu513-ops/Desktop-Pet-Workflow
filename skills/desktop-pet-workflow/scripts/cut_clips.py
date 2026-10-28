#!/usr/bin/env python3
"""Cut 16-bit PCM WAV speech into a new, self-contained pet audio set."""
import argparse
import array
import json
import math
import os
from pathlib import Path
import shutil
import sys
import tempfile
import wave


def cut(item, manifest_dir, output, number, fade_ms, target_rms):
    source = Path(item['source']).expanduser()
    if not source.is_absolute():
        source = manifest_dir / source
    start, end = float(item['start']), float(item['end'])
    label = item['label']
    if not isinstance(label, str) or not label.strip():
        raise ValueError(f'clip {number}: label must be nonempty text')
    if not math.isfinite(start) or not math.isfinite(end) or start < 0 or start >= end:
        raise ValueError(f'clip {number}: invalid start/end')
    with wave.open(str(source), 'rb') as src:
        channels, width, rate, total = src.getnchannels(), src.getsampwidth(), src.getframerate(), src.getnframes()
        if width != 2 or src.getcomptype() != 'NONE' or channels < 1 or rate <= 0:
            raise ValueError(f'clip {number}: source must be 16-bit PCM WAV')
        first, last = round(start * rate), round(end * rate)
        if first >= total or last > total or last <= first:
            raise ValueError(f'clip {number}: time range exceeds source duration {total / rate:.3f}s')
        src.setpos(first)
        raw = src.readframes(last - first)
    values = array.array('h')
    values.frombytes(raw)
    if sys.byteorder != 'little':
        values.byteswap()
    if len(values) != (last - first) * channels:
        raise ValueError(f'clip {number}: source audio is truncated')
    gain = 1.0
    if target_rms is not None:
        rms = math.sqrt(sum(x*x for x in values) / len(values)) / 32768
        peak = max(abs(x) for x in values) / 32768
        gain = min(target_rms / max(rms, 1e-9), .95 / max(peak, 1e-9), 2.0)
    frames = last - first
    fade = min(round(fade_ms * rate / 1000), frames // 2)
    for i, sample in enumerate(values):
        frame = i // channels
        envelope = 1.0
        if fade:
            envelope = min(1.0, frame / fade, (frames - 1 - frame) / fade)
        values[i] = max(-32768, min(32767, round(sample * gain * envelope)))
    if sys.byteorder != 'little':
        values.byteswap()
    name = f'{number:02d}.wav'
    with wave.open(str(output / 'Clips' / name), 'wb') as dest:
        dest.setnchannels(channels)
        dest.setsampwidth(width)
        dest.setframerate(rate)
        dest.writeframes(values.tobytes())
    result = {'id': number, 'label': label, 'file': name, 'duration': frames / rate}
    provenance = {'id': number, 'source': str(source.resolve()), 'start': first / rate,
                  'end': last / rate, 'label': label, 'gain': gain}
    return result, provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path, help='JSON array: source, start, end, label')
    parser.add_argument('--output', required=True, type=Path, help='new directory to create')
    parser.add_argument('--fade-ms', type=float, default=5.0)
    parser.add_argument('--target-rms', type=float, help='optional linear RMS target, e.g. 0.1')
    args = parser.parse_args()
    if not math.isfinite(args.fade_ms) or args.fade_ms < 0:
        parser.error('--fade-ms must be a finite nonnegative number')
    if args.target_rms is not None and (not math.isfinite(args.target_rms) or not 0 < args.target_rms <= 1):
        parser.error('--target-rms must be between 0 and 1')
    if os.path.lexists(args.output):
        parser.error('output already exists; choose a new directory')
    items = json.loads(args.manifest.read_text(encoding='utf-8'))
    if not isinstance(items, list) or not items or not all(isinstance(x, dict) for x in items):
        parser.error('manifest must contain a nonempty JSON array of clip objects')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.pet-clips-', dir=args.output.parent))
    try:
        (stage / 'Clips').mkdir()
        clips, records = [], []
        for number, item in enumerate(items, 1):
            clip, record = cut(item, args.manifest.resolve().parent, stage, number, args.fade_ms, args.target_rms)
            clips.append(clip)
            records.append(record)
        (stage / 'clips.json').write_text(json.dumps(clips, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        (stage / 'cut-records.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        if os.path.lexists(args.output):
            raise FileExistsError(f'output was created concurrently: {args.output}')
        os.rename(stage, args.output)
        print(f'Created {len(clips)} clips in {args.output}')
    finally:
        if stage.exists():
            shutil.rmtree(stage)


if __name__ == '__main__':
    main()
