from flask import Flask, render_template, jsonify, request
from flask_bootstrap import Bootstrap
from flask_cors import CORS
import base64
from hashlib import md5
from APIClient import *
import firebase_admin
from firebase_admin import credentials, db
import time
import json
from threading import Thread

cred = credentials.Certificate('project-anti-alz-firebase-adminsdk-zlh54-decaa0ce0a.json') 
# firebase_admin.initialize_app(cred, {'databaseURL' : 'https://project-anti-alz.firebaseio.com/'})
root = db.reference()

# Imports the Google Cloud client library
from google.cloud import storage

# The name for the new bucket
bucket_name = 'history-images-3519435695'
# bucket = storage_client.create_bucket(bucket_name)


app = Flask(__name__)
CORS(app)
bootstrap = Bootstrap(app)
client = APIClient("people_13")

epoch = lambda: int(time.time() * 1000)

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/detect-face', methods=['POST'])
def detect_face():
    img_content = request.data
    filename = md5(img_content).hexdigest()

    img_path = "uploads/" + filename + ".jpg"
    with open(img_path, "wb") as fh:
        fh.write(img_content)

    def upload_to_cloud_storage(storage, bucket_name, filename, img_path):
        """Uploads a file to the bucket."""
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(filename)
        blob.upload_from_filename(img_path)
        print('File {} uploaded to {}.'.format(img_path, filename))
    
    thread = Thread(target=upload_to_cloud_storage, kwargs={
        'storage': storage,
        'bucket_name': bucket_name,
        'filename': filename,
        'img_path': img_path
    })
    thread.start()

    url = "https://storage.cloud.google.com/history-images-3519435695/"+ filename
    result = client.return_message_from_face(img_path)

    # this is a list now, what happens if the list is empty?
    print(result)
    if len(result) > 0:
        # result[0]['msg'] = "You met " + result[0]["name"] + " he is your " + result[0]["userData"] + "."
        print(result)
    else:
        # print("Empty List")
        return(jsonify({"error": "I'm sorry. I don't see anyone else."}))


    hist_ref = root.child('history')
    for person_id, person_info in result.items():
        hist_ref.child(str(epoch()) + '|' + person_id).set(
            {
                'imgUrls': url,
                'personId': person_id
            }
        )

    return jsonify(result)

@app.route('/reminders', methods=['GET'])
def get_reminders():
    return jsonify(client.fetch_all_reminders())

@app.route("/update_azure_db", methods=['POST'])
def update_azure_db():
    # print(request.json)
    data = request.json
    # json_data = request.data
    # json_file = open('json1')
    # json_str = json_file.read()
    # data = json.loads(json_str)[0]
    base64image = data["file"].split(',')[-1]

    decoded_img = base64.b64decode(base64image)
    img_path = "uploads/" + md5(base64image.encode('utf-8')).hexdigest() + ".jpg"
    with open(img_path, "wb") as fh:
        fh.write(decoded_img)
    client.add_person(data["name"], data["relation"], img_path, data["notes"])
    client.train_data()
    client.print_list()
    print("/update_azure_db called")
    return jsonify({"error": "Do not access"})

@app.route("/set-reminder-epoch", methods=["GET"])
def set_reminder_epoch():
    mins = int(request.args.get('mins', default = 30))
    client.set_reminder_epoch_group(mins * 60 * 1000, 10 * 1000)
    return jsonify({'status': 'success'})

@app.route("/get_history", methods=["POST"])
def get_history():
    users = root.child("history").get()
    return jsonify(users)

if __name__=='__main__':
    app.run(debug=True)
