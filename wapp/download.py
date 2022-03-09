from fileinput import filename
from flask import send_file

def download_file(url, file):
    path = url
    print("path", path)
    return send_file(path, attachment_filename=file)