from io import BytesIO

import boto3
import requests
from flask import Flask, request

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

import re

app = Flask(__name__)

cred = credentials.Certificate('/Users/tygrash/Downloads/bukuwarung-app-61d4411853b9.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

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


def get_table_info(blocks, ids):
    item_names = []
    item_qty = []
    item_unit_price = []
    total_item_price = []

    for block in blocks:
        block_id = block['Id']
        if block_id in ids:
            if 'Relationships' in block:
                cell_word_val = get_key_text(blocks, block['Relationships'][0]['Ids'])
                # print(cell_word_val)
                if block['ColumnIndex'] in [2, 3] and len(re.findall(r'[0]+', cell_word_val)) > 0 and \
                        len(re.findall(r'[^0-9|.]', cell_word_val)) == 0:
                    item_unit_price.append(cell_word_val)
                elif block['ColumnIndex'] in [1, 2] and len(re.findall(r'[^0-9|.]', cell_word_val)) > 1:
                    item_names.append(cell_word_val)
                elif block['ColumnIndex'] == 2:
                    item_qty.append(cell_word_val)
                elif block['ColumnIndex'] in [3]:
                    item_unit_price.append(cell_word_val)
                elif block['ColumnIndex'] == 4:
                    total_item_price.append(cell_word_val)

    return {'item_names': item_names, 'item_qty': item_qty, 'item_unit_price': item_unit_price,
            'total_item_price': total_item_price}


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

    # Fetch key values
    key_val_map = {}
    for block in blocks:
        if block['BlockType'] == "KEY_VALUE_SET":
            if 'KEY' in block['EntityTypes']:
                key = get_key_text(blocks, block['Relationships'][1]['Ids'])
                value = get_key_value(blocks, block['Relationships'][0]['Ids'])

                key_val_map[key] = value

    # Fetch all lines and words
    line_lst = []
    for block in blocks:
        if block['BlockType'] in ["LINE", "WORD"]:
            line_lst.append(block['Text'])

    # Fetch table info
    table_info = {}
    for block in blocks:
        if block['BlockType'] == "TABLE":
            table_info = get_table_info(blocks, block['Relationships'][0]['Ids'])

    return_json = {'imageName': content['imageName'], 'imageUrl': content['imageUrl'], 'bookId': content['bookId'],
                   'userId': content['userId'], 'uploadId': content['uploadId'], 'documentKeyValue': key_val_map,
                   'words': line_lst, 'table_info': table_info}

    doc_ref = db.collection(u'users_image_upload').document(content['uploadId'])
    doc_ref.set(return_json)

    return return_json


@app.route('/greet')
def say_hello():
    return 'Hello from Server'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
