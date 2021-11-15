import os
import numpy as np
from pydub import AudioSegment
from utils import denoise, find_onsets, make_beats, mix_beats
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = "tmp/"
app.config["CACHE_TYPE"] = "null"
#app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000


@app.route('/')
def upload_file():
    try:
        os.remove(app.config["UPLOAD_FOLDER"] + 'audio.wav')
        os.remove(app.config["UPLOAD_FOLDER"] + 'output.wav')
    except BaseException:
        pass
    return render_template('index.html')


@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)


@app.route('/display', methods=['GET', 'POST'])
def save_file():
    if request.method == 'POST':
        f = request.files['file']
        filename = 'audio.wav'
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        f.save(path)

        content = url_for('download_file', name=filename)

        return render_template('content.html', content=content)


@app.route('/generate_file', methods=['GET', 'POST'])
def generate_file():

    bpm = request.form.get("bpm", type=int)
    meter = request.form.get("meter", type=int)
    name = 'audio.wav'
    file = app.config["UPLOAD_FOLDER"] + name
    y, sr = denoise(file)
    y_dub = np.array(y * (1 << 15), dtype=np.int16)

    audio = AudioSegment(
        y_dub.tobytes(),
        frame_rate=sr,
        sample_width=y_dub.dtype.itemsize,
        channels=1) + 10

    high_start, high_onsets, low_start, low_onsets = find_onsets(y, sr)
    down_beats = make_beats(audio, high_onsets, bpm, high_start, outro=100)
    up_beats = make_beats(audio, low_onsets, bpm, low_start, outro=100) - 10
    gap = high_start[0] - low_start[0]
    beats = mix_beats(down_beats, up_beats, bpm, meter, delay=gap)
    beats_path = os.path.join(app.config["UPLOAD_FOLDER"], "output.wav")
    beats.export(beats_path, format="wav")
    beats_file = url_for('download_file', name="output.wav")

    return render_template('output.html', output=beats_file)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
    # app.add_url_rule(
    # "/uploads/<name>", endpoint="download_file", build_only=True)
