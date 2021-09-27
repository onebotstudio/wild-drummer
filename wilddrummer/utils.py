#! /usr/bin/env python3

from pydub import AudioSegment
from pydub.silence import split_on_silence
import random
from scipy.signal import find_peaks

def split(sound):
    """ split audio by silence """

    dBFS = sound.dBFS
    chunks = split_on_silence(sound, 
        min_silence_len = 50,
        silence_thresh = dBFS-10)
    return chunks

def make_beats(audio_list, sample_rate, bpm):

    bpms = bpm/60000
    interval = 1/bpms/4

    playlist = AudioSegment.empty()
    playlist += audio_list[0]
    #len_ms = len(audio_list[0].get_array_of_samples())/ sample_rate
    for s in audio_list[1:]:
        samp = s.get_array_of_samples()
        peak_amplitude = s.max
        peak, _ = find_peaks(samp, height=peak_amplitude)
        enter = peak[0] / sample_rate
        #len_ms = len(samp)// sample_rate
        interval_silence = AudioSegment.silent(duration=int(interval-enter))
        playlist += interval_silence
        playlist += s

    return playlist


file = 'kiki_0001.m4a'
audio = AudioSegment.from_file(file)
sample_rate = audio.frame_rate

chunks = split(audio)
sound = chunks[:10]
sound = [s for s in sound for i in range(4)]
random.shuffle(sound)

beats = make_beats(sound,sample_rate, 120)

file_handle = beats.export("output.wav", format="wav")

