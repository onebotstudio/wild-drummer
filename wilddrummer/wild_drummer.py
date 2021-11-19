#! /usr/bin/env python3

import os
import argparse
import numpy as np
from pydub import AudioSegment
from wilddrummer.utils import denoise, find_onsets, make_beats


def generate_audio(file, output_dir, bpm, downbeats_only):
    """

    Args:
    Returns:
    """
    y, sr = denoise(file)
    y_dub = np.array(y * (1 << 15), dtype=np.int16)

    audio = AudioSegment(
        y_dub.tobytes(),
        frame_rate=sr,
        sample_width=y_dub.dtype.itemsize,
        channels=1) + 10

    starts, onsets, stops, intro, high_ind = find_onsets(y, sr)
    beats = make_beats(
        audio,
        starts,
        onsets,
        stops,
        intro,
        high_ind,
        bpm,
        downbeats_only)
    beats_path = os.path.join(output_dir, "wild_drums.wav")
    beats.export(beats_path, format="wav")

    return None


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('file', help="input file")
    parser.add_argument('bpm', type=int, help="beats per minute")
    parser.add_argument('output_dir', help="output directory")

    parser.add_argument(
        '-x',
        '--downbeats',
        nargs='?',
        const=True,
        default=False,
        help="flag for downbeats only")

    args = parser.parse_args()
    file = args.file
    bpm = args.bpm
    output_dir = args.output_dir


    if args.downbeats:
        dbo = True
    else:
        dbo = False

    generate_audio(file, output_dir, bpm, downbeats_only=dbo)


if __name__ == "__main__":
    main()
