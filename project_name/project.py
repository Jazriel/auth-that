from flask import Flask, redirect, url_for

app = Flask(__name__)


@app.route('/')
def index():
    return redirect(url_for('user_mng.login'))
