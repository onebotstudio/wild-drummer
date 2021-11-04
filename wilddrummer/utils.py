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
    o_env = librosa.onset.onset_strength(y, sr=sr)
    onset_frames = librosa.onset.onset_detect(onset_envelope=o_env, sr=sr)
    onset_samples = list(librosa.frames_to_samples(onset_frames))
    onset_arr = (np.array(onset_samples) / sr * 1000).astype(int)

    return onset_arr


def make_beats(audio, sample_list, sample_rate, bpm):
    """ make beats from audio segments """

    bpms = bpm / 60000
    interval = 1 / bpms  # /4
    intro = 0
    outro = 1000

    playlist = AudioSegment.empty()
    for s in sample_list:
        start = s - intro
        end = s + outro
        samp = audio[start:end]
        enter = intro + outro
        interval_silence = AudioSegment.silent(duration=int(interval - enter))
        playlist += samp
        playlist += interval_silence

    return playlist


file = 'kiki_0001.m4a'
data, new_file = denoise(file)
audio = AudioSegment.from_file(new_file)
sample_rate = audio.frame_rate

sample_arr = find_onsets(new_file)
beats = make_beats(audio, sample_arr, sample_rate, 100)

file_handle = beats.export("output.wav", format="wav")