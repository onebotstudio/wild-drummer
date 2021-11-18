#! /usr/bin/env python3

from pydub import AudioSegment
import numpy as np
import librosa
import noisereduce as nr


def denoise(file):
    """ denoise file """

    data, sr = librosa.load(file)
    denoised_data = nr.reduce_noise(y=data, sr=sr)

    return denoised_data, sr


def find_onsets_old(data, sample_rate):
    """ onset detection """

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


def find_onsets(data, sample_rate):
    """ onset detection

    Args:
        data: librosa read audio output
        sample_rate

    Returns:
        starts: onset starting points array
        onsets: onset points array
        stops: onset ending points array
        intro: gaps between starting points and onset points
        high_ind: index of high onsets
     """

    y = data
    sr = sample_rate
    o_env = librosa.onset.onset_strength(y, sr=sr, max_size=10)
    onset_frames = librosa.onset.onset_detect(onset_envelope=o_env, sr=sr)
    onset_st = o_env[onset_frames]
    high_ind = np.where(onset_st > 8)[0]

    # backtrack for split point
    high_frames = librosa.onset.onset_backtrack(onset_frames, o_env)
    start_samples = list(librosa.frames_to_samples(high_frames))
    start_tmp = (np.array(start_samples) / sr * 1000).astype(int)
    start_samples = np.concatenate(start_samples, len(y))
    starts = (np.array(start_samples[0:-1]) / sr * 1000).astype(int)
    stops = (np.array(start_samples[1:]) / sr * 1000).astype(int)

    # get onset points
    onset_samples = list(librosa.frames_to_samples(onset_frames))
    onsets = (np.array(onset_samples) / sr * 1000).astype(int)
    # get intro
    intro = onsets - start_tmp

    return starts, onsets, stops, intro, high_ind


def make_beats_old(audio, sample_list, bpm, intro, outro=250):
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


def make_beats(
        audio,
        starts,
        onsets,
        stops,
        intro,
        high_ind,
        bpm,
        downbeats_only=False):
    """ make beats from audio segments

    Args:
        audio: audio file
        starts: onset starting points array
        onsets: onset points array
        stops: onset ending points array
        intro: gaps between starting points and onset points
        high_ind: index of high onsets
        bpm: beats per minute
        downbeats_only: set true if only down beats

    Returns:
        sample: beats AudioSegment obj
    """

    meter = 4
    bpms = bpm / 60000
    downbeat_interval = int(1 / bpms)

    if downbeats_only:
        interval_silence = AudioSegment.silent(duration=downbeat_interval)
        sample = audio[starts[0]:stops[0]].fade_in(
            10).fade_out(30) + interval_silence
        for i in range(1, len(starts)):
            sample = sample.overlay(audio[starts[i]:stops[i]].fade_in(10).fade_out(
                30), position=downbeat_interval * i - intro[i]) + interval_silence
        return sample
    else:
        upbeat_interval = int(1 / bpms / meter)
        # compute gaps
        onsets_p = onsets[1:]
        onsets_p = np.append(onsets_p, onsets[-1])
        gap_til_next = onsets_p - onsets
        # add fading
        sample = audio[starts[0]:stops[0]].fade_in(10).fade_out(30)
        pos = intro[0]
        for i in range(len(starts) - 1):
            # high onsets can only be down beats
            if i in high_ind:
                interval = downbeat_interval
                pos = pos // downbeat_interval * downbeat_interval
            elif gap_til_next[i] <= upbeat_interval // 2:
                interval = upbeat_interval // 2
            elif gap_til_next[i] <= upbeat_interval:
                interval = upbeat_interval
            else:
                interval = downbeat_interval
            pos += interval
            interval_silence = AudioSegment.silent(duration=interval)
            sample = sample + interval_silence
            sample = sample.overlay(
                    audio[starts[i + 1]:stops[i + 1]].fade_in(10).fade_out(30), 
                    position=pos - intro[i + 1])

    return sample


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
