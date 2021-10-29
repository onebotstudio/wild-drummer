#! /usr/bin/env python3

from pydub import AudioSegment
from pydub.silence import split_on_silence
import numpy as np
import librosa
import random
from scipy.signal import find_peaks


def find_onsets(file):
    """ librosa onset detection"""

    y, sr = librosa.load(file)
    o_env = librosa.onset.onset_strength(y, sr=sr)
    onset_frames = librosa.onset.onset_detect(onset_envelope=o_env, sr=sr)
    onset_samples = list(librosa.frames_to_samples(onset_frames))
    onset_arr = (np.array(onset_samples)/sr*1000).astype(int)

    return onset_arr


def make_beats(audio, sample_list, sample_rate, bpm):
    """ make beats from audio segments """
    
    bpms = bpm/60000
    interval = 1/bpms#/4

    playlist = AudioSegment.empty()
    for s in sample_list:
        start = s - 23
        end = s + 23
        samp = audio[start:end]
        enter = 23 * 2
        interval_silence = AudioSegment.silent(duration=int(interval-enter))
        playlist += interval_silence
        playlist += samp

    return playlist


file = 'kiki_0001.m4a'
audio = AudioSegment.from_file(file)
sample_rate = audio.frame_rate

sample_arr = find_onsets(file)
beats = make_beats(audio, sample_arr, sample_rate, 120)

file_handle = beats.export("output.wav", format="wav")

