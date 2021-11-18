import os
import glob
import numpy as np
from pydub import AudioSegment
from utils import denoise, find_onsets, make_beats, mix_beats
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, current_app
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = "tmp/"
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a'}
#app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def upload_file():
    try:
        for file in glob.glob(os.path.join(
                                    app.config['UPLOAD_FOLDER'], 'audio*')
                                    ):
            os.remove(file)
        os.remove(app.config["UPLOAD_FOLDER"] + 'output.wav')
    except BaseException:
        pass
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('About.html')


@app.route('/contact')
def contact():
    return render_template('Contact.html')


@app.route('/uploads/<name>', methods=['GET', 'POST'])
def download_file(name):
    uploads = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'])
    return send_from_directory(uploads, name)


@app.route('/display', methods=['GET', 'POST'])
def save_file():
    if request.method == 'POST':
        f = request.files['file']
        if f and allowed_file(f.filename):
            _, ext = f.filename.split('.')
            filename = 'audio.{}'.format(ext)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            f.save(path)
            content = url_for('download_file', name=filename)
            return render_template('content.html', content=content)

    return upload_file()


@app.route('/output', methods=['GET', 'POST'])
def generate_file():
    if request.method == 'POST':
        bpm = request.form.get("bpm", type=int)
        file = glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], 'audio*'))[0]
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
            downbeats_only=False)
        #up_beats = make_beats(audio, low_onsets, bpm, low_start, outro=100)-10
        #gap = high_start[0] - low_start[0]
        #beats = mix_beats(down_beats, up_beats, bpm, meter, delay=gap)
        beats_path = os.path.join(app.config["UPLOAD_FOLDER"], "output.wav")
        beats.export(beats_path, format="wav")
        beats_file = url_for('download_file', name="output.wav")

        return render_template('output.html', output=beats_file)
    return redirect(url_for('upload_file'))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
