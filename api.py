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


def get_table_info(blocks, ids):
    item_names = []
    item_qty = []
    item_unit_price = []
    total_item_price = []

    for block in blocks:
        block_id = block['Id']
        if block_id in ids:
            if 'Relationships' in block:
                if block['ColumnIndex'] == 1:
                    item_names.append(get_key_text(blocks, block['Relationships'][0]['Ids']))
                if block['ColumnIndex'] == 2:
                    item_qty.append(get_key_text(blocks, block['Relationships'][0]['Ids']))
                if block['ColumnIndex'] == 3:
                    item_unit_price.append(get_key_text(blocks, block['Relationships'][0]['Ids']))
                if block['ColumnIndex'] == 4:
                    total_item_price.append(get_key_text(blocks, block['Relationships'][0]['Ids']))

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

    return return_json


@app.route('/greet')
def say_hello():
    return 'Hello from Server'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
