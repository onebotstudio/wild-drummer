#! /usr/bin/env python3

from pydub import AudioSegment
import numpy as np
import librosa
import noisereduce as nr
import soundfile as sf


def denoise(file):
    """ denoise file """

    data, sr = librosa.load(file)
    denoised_data = nr.reduce_noise(y=data, sr=sr)
    sf.write('denoised_file.wav', denoised_data, samplerate=sr)

    return denoised_data, 'denoised_file.wav'


def find_onsets(file):
    """ librosa onset detection """

    y, sr = librosa.load(file)
    o_env = librosa.onset.onset_strength(y, sr=sr, max_size=15)
    onset_frames =librosa.onset.onset_detect(onset_envelope=o_env, sr=sr)
    # separate low onsets
    onset_st =  o_env[onset_frames]
    low_pos = np.where(onset_st<5)[0]
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
    
    bpms = bpm/60000
    interval = 1/bpms#/2

    playlist = AudioSegment.empty()
    for i in range(len(sample_list)):
        s = sample_list[i]
        start = s - intro[i]
        end = s + outro
        samp = audio[start:end].fade_in(10).fade_out(outro//2)
        if i == len(intro) -1:
            enter = outro
        else:
            enter = outro + intro[i+1]
        interval_silence = AudioSegment.silent(duration=int(interval-enter))
        playlist += samp
        playlist += interval_silence

    return playlist


def mix_beats(down_beats, up_beats, bpm, meter=4, delay=0):
    """ combine down beats and up beats"""

    bpms = bpm/60000

    if meter == 4:
        interval = 1/bpms/2
    elif meter ==3:
        interval = 1/bpms/3
    else:
        interval = 0

    if len(down_beats) > len(up_beats):
        loop_rounds = len(down_beats) // len(up_beats) + 1
        beats = down_beats.overlay(up_beats*loop_rounds, position=delay+interval)
    else:
        loop_rounds = len(up_beats) // len(down_beats)
        down_beats = down_beats * loop_rounds
        beats = down_beats.overlay(up_beats, position=interval)
    
    return beats


file = '../samples/NHU05003078.wav'
bpm = 80
meter = 4
data, new_file = denoise(file)
audio = AudioSegment.from_file(new_file) + 10

high_start, high_onsets, low_start, low_onsets = find_onsets(new_file)
down_beats = make_beats(audio, high_onsets, bpm, high_start, outro=100)
up_beats= make_beats(audio, low_onsets, bpm, low_start, outro=100) - 10
gap = high_start[0]-low_start[0]
beats = mix_beats(down_beats, up_beats, bpm, meter, delay=gap)
file_handle = beats.export("output.wav", format="wav")