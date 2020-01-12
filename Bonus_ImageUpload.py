import os
from flask import Flask, session, abort, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
from flask import send_from_directory
import ImageProcess
import random
import string

UPLOAD_FOLDER = './static'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# 產生亂數
def keygen():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            # flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            # flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # 若沒有session則建立
            if session.get('username') == None:
                session['username'] = keygen()
            filename = session.get('username') + filename
            fpath = os.path.join(app.config['UPLOAD_FOLDER'], filename).replace('\\', '/')
            file.save(fpath)
            # 圖片檔案名稱回復，避免包含session字串的檔案名稱直接顯示於網址列
            filename = filename[10:]
            return redirect(url_for('showfile', filename=filename))
    return render_template('upload.html', pagetitle="Upload page")

@app.route('/show/<filename>')
def showfile(filename):
    # 檢查session是否存在
    if session.get('username') != None:
        filename = session.get('username') + filename
        fpath = os.path.join(app.config['UPLOAD_FOLDER'], filename).replace('\\', '/')
        # 檢查圖片是否存在
        if os.path.isfile(fpath):
            ImageProcess.process(fpath, binary = 1, flip = 1, save = 1)
            fname = filename.rsplit('.', 1)
            newfile = fname[0] + "_p." + ''.join(fname[1:])
            return render_template('image.html', pagetitle="Show image", fn=newfile)
    # 重新導向至upload_file
    return redirect(url_for('upload_file'))

if __name__ == '__main__':
    app.run(host='192.168.50.73', debug=True)
