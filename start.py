import logging
import threading
from flask import Flask, request, render_template, jsonify, send_from_directory
import os
from gevent.pywsgi import WSGIServer, WSGIHandler
from logging.handlers import RotatingFileHandler

import vocal
from vocal import cfg, tool
from vocal.cfg import ROOT_DIR
import subprocess
from spleeter.separator import Separator

class CustomRequestHandler(WSGIHandler):
    def log_request(self):
        pass


log = logging.getLogger('werkzeug')
log.handlers[:] = []
log.setLevel(logging.WARNING)

app = Flask(__name__, static_folder=os.path.join(ROOT_DIR, 'static'), static_url_path='/static',
            template_folder=os.path.join(ROOT_DIR, 'templates'))
root_log = logging.getLogger()  
root_log.handlers = []
root_log.setLevel(logging.WARNING)


app.logger.setLevel(logging.WARNING) 

file_handler = RotatingFileHandler(os.path.join(ROOT_DIR, 'vocal.log'), maxBytes=1024 * 1024, backupCount=5)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler.setLevel(logging.WARNING)
file_handler.setFormatter(formatter)

app.logger.addHandler(file_handler)


@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.config['STATIC_FOLDER'], filename)

@app.route('/')
def index():
    return render_template("index.html",version=vocal.version_str,cuda=cfg.cuda, language=cfg.LANG,root_dir=ROOT_DIR.replace('\\', '/'))


#upload audio
@app.route('/upload', methods=['POST'])
def upload():
    try:
        #get the uploaded file
        audio_file = request.files['audio']
        #for mp4 file
        noextname, ext = os.path.splitext(audio_file.filename)
        ext = ext.lower()
       #audio extraction
        wav_file = os.path.join(cfg.TMP_DIR, f'{noextname}.wav')
        if os.path.exists(wav_file) and os.path.getsize(wav_file) > 0:
            return jsonify({'code': 0, 'msg': cfg.transobj['lang1'], "data": os.path.basename(wav_file)})
        msg=""
        if ext in ['.mp4', '.mov', '.avi', '.mkv', '.mpeg', '.mp3', '.flac']:
            video_file = os.path.join(cfg.TMP_DIR, f'{noextname}{ext}')
            audio_file.save(video_file)
            params = [
                "-i",
                video_file,
            ]
            if ext not in ['.mp3', '.flac']:
                params.append('-vn')
            params.append(wav_file)
            rs = tool.runffmpeg(params)
            if rs != 'ok':
                return jsonify({"code": 1, "msg": rs})
            msg=","+cfg.transobj['lang9']
        elif ext == '.wav':
            audio_file.save(wav_file)
        else:
            return jsonify({"code": 1, "msg": f"{cfg.transobj['lang3']} {ext}"})

        # successful response
        return jsonify({'code': 0, 'msg': cfg.transobj['lang1']+msg, "data": os.path.basename(wav_file)})
    except Exception as e:
        app.logger.error(f'[upload]error: {e}')
        return jsonify({'code': 2, 'msg': cfg.transobj['lang2']})



@app.route('/process', methods=['GET', 'POST'])
def process():
    
    wav_name = request.form.get("wav_name").strip()
    model = request.form.get("model")
    wav_file = os.path.join(cfg.TMP_DIR, wav_name)
    noextname = wav_name[:-4]
    if not os.path.exists(wav_file):
        return jsonify({"code": 1, "msg": f"{wav_file} {cfg.langlist['lang5']}"})
    if not os.path.exists(os.path.join(cfg.MODEL_DIR, model, 'model.meta')):
        return jsonify({"code": 1, "msg": f"{model} {cfg.transobj['lang4']}"})
    try:
        p=subprocess.run(['ffprobe','-v','error','-show_entries',"format=duration",'-of', "default=noprint_wrappers=1:nokey=1", wav_file], capture_output=True)      
        if p.returncode==0:
            sec=float(p.stdout)  
    except:
        sec=1800
    print(f'{sec}')
    separator = Separator(f'spleeter:{model}', multiprocess=False)
    dirname = os.path.join(cfg.FILES_DIR, noextname)
    try:
        separator.separate_to_file(wav_file, destination=dirname, filename_format="{instrument}.{codec}", duration=sec)
    except Exception as e:
        return jsonify({"code": 1, "msg": str(e)})
    status={
        "accompaniment":"accompaniment",
        "bass":"bass",
        "drums":"drums",
        "piano":"piano",
        "vocals":"vocals",
        "other":"other"
    }
    data = []
    urllist = []
    for it in os.listdir(dirname):
        if it.endswith('.wav'):
            data.append( status[it[:-4]] if cfg.LANG=='zh' else it[:-4])
            urllist.append(f'http://{cfg.web_address}/static/files/{noextname}/{it}')

    return jsonify({"code": 0, "msg": cfg.transobj['lang6'], "data": data, "urllist": urllist,"dirname":dirname})


@app.route('/api',methods=['POST'])
def api():
    try:
       
        audio_file = request.files['file']
        model = request.form.get("model")
        
        noextname, ext = os.path.splitext(audio_file.filename)
        ext = ext.lower()
        
        wav_file = os.path.join(cfg.TMP_DIR, f'{noextname}.wav')
        if not os.path.exists(wav_file) or os.path.getsize(wav_file) == 0:
            if ext in ['.mp4', '.mov', '.avi', '.mkv', '.mpeg', '.mp3', '.flac']:
                video_file = os.path.join(cfg.TMP_DIR, f'{noextname}{ext}')
                audio_file.save(video_file)
                params = [
                    "-i",
                    video_file,
                ]
                if ext not in ['.mp3', '.flac']:
                    params.append('-vn')
                params.append(wav_file)
                rs = tool.runffmpeg(params)
                if rs != 'ok':
                    return jsonify({"code": 1, "msg": rs})
            elif ext == '.wav':
                audio_file.save(wav_file)
            else:
                return jsonify({"code": 1, "msg": f"{cfg.transobj['lang3']} {ext}"})

        
        if not os.path.exists(wav_file):
            return jsonify({"code": 1, "msg": f"{wav_file} {cfg.langlist['lang5']}"})
        if not os.path.exists(os.path.join(cfg.MODEL_DIR, model, 'model.meta')):
            return jsonify({"code": 1, "msg": f"{model} {cfg.transobj['lang4']}"})
        try:
            p = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', "format=duration", '-of',
                                "default=noprint_wrappers=1:nokey=1", wav_file], capture_output=True)
            if p.returncode == 0:
                sec = float(p.stdout)
        except:
            sec = 1800
        print(f'{sec}')
        separator = Separator(f'spleeter:{model}', multiprocess=False)
        dirname = os.path.join(cfg.FILES_DIR, noextname)
        try:
            separator.separate_to_file(wav_file, destination=dirname, filename_format="{instrument}.{codec}",
                                       duration=sec)
        except Exception as e:
            return jsonify({"code": 1, "msg": str(e)})
        status = {
            "accompaniment.wav":"accompaniment audio" if cfg.LANG=='en' else "accompaniment",
            "bass.wav": "bass audio" if cfg.LANG=='en' else"bass",
            "drums.wav": "drums audio" if cfg.LANG=='en' else"drums",
            "piano.wav": "piano audio" if cfg.LANG=='en' else"piano",
            "vocals.wav": "vocals audio" if cfg.LANG=='en' else"vocals",
            "other.wav": "other audio" if cfg.LANG=='en' else"other"
        }
        # data = []
        urllist = []
        for it in os.listdir(dirname):
            if it.endswith('.wav'):
                urllist.append(f'http://{cfg.web_address}/static/files/{noextname}/{it}')

        return jsonify({"code": 0, "msg": cfg.transobj['lang6'], "data": urllist,"status_text":status})
    except Exception as e:
        app.logger.error(f'[upload]error: {e}')
        return jsonify({'code': 2, 'msg': cfg.transobj['lang2']})




@app.route('/checkupdate', methods=['GET', 'POST'])
def checkupdate():
    return jsonify({'code': 0, "msg": cfg.updatetips})


if __name__ == '__main__':
    http_server = None
    try:
        threading.Thread(target=tool.checkupdate).start()        
        try:
            host = cfg.web_address.split(':')
            http_server = WSGIServer((host[0], int(host[1])), app ,handler_class=CustomRequestHandler)
            threading.Thread(target=tool.openweb, args=(cfg.web_address,)).start()
            http_server.serve_forever()
        finally:
            if http_server:
                http_server.stop()
    except Exception as e:
        if http_server:
            http_server.stop()
        print("error:" + str(e))
        app.logger.error(f"[app]start error:{str(e)}")
