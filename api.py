from io import BytesIO

import boto3
import requests
from flask import Flask, request

app = Flask(__name__)


def get_key_text(blocks, ids):
    txt = ""

    for block in blocks:
        block_id = block['Id']
        if block_id in ids:
            txt = txt + block["Text"] + " "

    return txt


def get_key_value(blocks, ids):
    txt = ""
    for block in blocks:
        block_id = block['Id']
        if block_id in ids:
            if 'Relationships' in block:
                return get_key_text(blocks, block['Relationships'][0]['Ids'])

    return txt


@app.route('/upload_image', methods=['POST'])
def fetch_image():
    content = request.json
    print(content)

    image_url = content['imageUrl']
    response = requests.get(image_url)
    stream = BytesIO(response.content)

    # Analyze the document
    client = boto3.client('textract')

    image_binary = stream.getvalue()
    response = client.analyze_document(Document={'Bytes': image_binary},
                                       FeatureTypes=["FORMS", "TABLES"])

    blocks = response['Blocks']
    # print(blocks)
    key_val_map = {}
    for block in blocks:
        if block['BlockType'] == "KEY_VALUE_SET":
            if 'KEY' in block['EntityTypes']:
                key = get_key_text(blocks, block['Relationships'][1]['Ids'])
                value = get_key_value(blocks, block['Relationships'][0]['Ids'])

                key_val_map[key] = value

    return_json = {'imageName': content['imageName'], 'imageUrl': content['imageUrl'], 'bookId': content['bookId'],
                   'userId': content['userId'], 'uploadId': content['uploadId'], 'documentKeyValue': key_val_map}

    return return_json


@app.route('/greet')
def say_hello():
    return 'Hello from Server'
