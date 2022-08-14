import time
from datetime import datetime

from gevent.pywsgi import WSGIServer
from flask import Flask, jsonify, request
from flask_cors import CORS

from retriever import Retriever
from util import base64_to_pil

retriever = Retriever('127.0.0.1', 'resnet_50_norm')

app = Flask(__name__)

@app.route('/')
def index():
    # check AI server status
    return jsonify({'ok':True})

@app.route("/cbir/", methods=['GET', 'POST'])
def cbir():
    if request.method == 'POST':
        data = request.json
        if data["key"] == "demo1":
            print('Valid Key')
            img = base64_to_pil(data["image"])
            start = time.time()
            results = retriever.search(img)
            end = time.time()
            time_taken = (end - start) * 1000
            msg = "搜索耗时: {:.0f} 毫秒".format(time_taken)
            print("Search Time: {:.0f} ms".format(time_taken))
            #print(results)
            now = datetime.now()
            timestamp = now.strftime("%Y-%m-%d_%H-%M-%S_%f")
            img.save("./upload/" + timestamp +".JPEG") 
            print('An uploaded image saved')
            base_url = "https://files.best360.tech/images/"
            resp = jsonify({'ok':True, 'result': msg, 
                    'image1': base_url + results[0][2].replace("./train/", ""),
                    'image2': base_url + results[1][2].replace("./train/", ""),
                    'image3': base_url + results[2][2].replace("./train/", ""),
                    'image4': base_url + results[3][2].replace("./train/", ""),
                    'image5': base_url + results[4][2].replace("./train/", "")})
        else:
            print('Invalid Key')
            resp = jsonify({'ok':False, 'result':'密钥不合法'})
        return resp
    else:
        return 'Invalid Method.\n'

if __name__ == '__main__':
    CORS(app, resources=r'/*')

    http_server = WSGIServer(("0.0.0.0", 5000), app)
    print('Server started.')
    http_server.serve_forever() 
