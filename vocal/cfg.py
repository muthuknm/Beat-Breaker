import locale
import os
import sys
import tensorflow
web_address = '127.0.0.1:9999'
LANG = "en" if locale.getdefaultlocale()[0].split('_')[0].lower() != 'zh' else "zh"

ROOT_DIR = os.getcwd()
MODEL_DIR = os.path.join(ROOT_DIR, 'pretrained_models')
STATIC_DIR = os.path.join(ROOT_DIR, 'static')
TMP_DIR = os.path.join(STATIC_DIR, 'tmp')
FILES_DIR = os.path.join(STATIC_DIR, 'files')
if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR, 0o777, exist_ok=True)
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR, 0o777, exist_ok=True)
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, 0o777, exist_ok=True)
if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR, 0o777, exist_ok=True)

if sys.platform == 'win32':
    os.environ['PATH'] = f'{ROOT_DIR};{ROOT_DIR}\\ffmpeg;' + os.environ['PATH']
else:
    os.environ['PATH'] = f'{ROOT_DIR}:{ROOT_DIR}/ffmpeg:' + os.environ['PATH']

langlist = {
    "zh": {
        "lang1": "Upload successful",
        "lang2": "Upload failed",
        "lang3": "Upload failed: Uploading this format is not allowed",
        "lang4": "Model file does not exist",
        "lang5": "File does not exist",
        "lang6": "Separation successful",
        "lang7": "Separation failed",
        "lang8": "The browser is open. If it does not open automatically, please open the URL manually", 
        "lang9": "Converted to wav"
    },
    "en": {
        "lang1": "Upload successful",
        "lang2": "Upload failed",
        "lang3": "Upload failed: Uploading this format is not allowed",
        "lang4": "Model file does not exist",
        "lang5": "File does not exist",
        "lang6": "Separation successful",
        "lang7": "Separation failed",
        "lang8": "The browser is open. If it does not open automatically, please open the URL manually", 
        "lang9": "Converted to wav"
    }
}
updatetips = ""
cuda = True if len(tensorflow.config.list_physical_devices('GPU'))>0 else False
transobj = langlist[LANG]
