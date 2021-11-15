#! /usr/bin/env python3

from pydub import AudioSegment
import numpy as np
import librosa
import noisereduce as nr


def denoise(file):
    """ denoise file """

    data, sr = librosa.load(file)
    denoised_data = nr.reduce_noise(y=data, sr=sr)
    #path += 'denoised_file.wav'
    #sf.write(path, denoised_data, samplerate=sr)

    return denoised_data, sr


def find_onsets(data, sample_rate):
    """ librosa onset detection """

    y = data
    sr = sample_rate
    o_env = librosa.onset.onset_strength(y, sr=sr, max_size=15)
    onset_frames = librosa.onset.onset_detect(onset_envelope=o_env, sr=sr)
    # separate low onsets
    onset_st = o_env[onset_frames]
    low_pos = np.where(onset_st < 5)[0]
    low_onset = onset_frames[low_pos]
    onset_frames = np.delete(onset_frames, low_pos, None)
    # backtrack for split point
    high_frames = librosa.onset.onset_backtrack(onset_frames, o_env)
    start_samples = list(librosa.frames_to_samples(high_frames))
    high_start = (np.array(start_samples) / sr * 1000).astype(int)
    low_frames = librosa.onset.onset_backtrack(low_onset, o_env)
    low_onset_samples = list(librosa.frames_to_samples(low_frames))
    low_start = (np.array(low_onset_samples) / sr * 1000).astype(int)
    # get onset points
    onset_samples = list(librosa.frames_to_samples(onset_frames))
    high_onset = (np.array(onset_samples) / sr * 1000).astype(int)
    lowonset_samples = list(librosa.frames_to_samples(low_onset))
    low_onset = (np.array(lowonset_samples) / sr * 1000).astype(int)
    # get intro
    high_intro = high_onset - high_start
    low_intro = low_onset - low_start

    return high_intro, high_onset, low_intro, low_onset


def make_beats(audio, sample_list, bpm, intro, outro=250):
    """ make beats from audio segments """

    bpms = bpm / 60000
    interval = 1 / bpms  # /2

    playlist = AudioSegment.empty()
    for i in range(len(sample_list)):
        s = sample_list[i]
        start = s - intro[i]
        end = s + outro
        samp = audio[start:end].fade_in(10).fade_out(outro // 2)
        if i == len(intro) - 1:
            enter = outro
        else:
            enter = outro + intro[i + 1]
        interval_silence = AudioSegment.silent(duration=int(interval - enter))
        playlist += samp
        playlist += interval_silence

    return playlist


def mix_beats(down_beats, up_beats, bpm, meter=4, delay=0):
    """ combine down beats and up beats"""

    bpms = bpm / 60000

    if meter == 4:
        interval = 1 / bpms / 2
    elif meter == 3:
        interval = 1 / bpms / 3
    else:
        interval = 0

    if len(down_beats) > len(up_beats):
        loop_rounds = len(down_beats) // len(up_beats) + 1
        beats = down_beats.overlay(
            up_beats * loop_rounds,
            position=delay + interval)
    else:
        loop_rounds = len(up_beats) // len(down_beats)
        down_beats = down_beats * loop_rounds
        beats = down_beats.overlay(up_beats, position=interval)

    return beats
