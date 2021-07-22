# digi_ninja_backend

Steps to create/run Python flask server:
1. pip3 install flask
2. 1) export FLASK_ENV=development
   2) export FLASK_APP=api.py
3. pip3 install pillow
4. 1) pip3 install aws-shell
   2) configure aws using command `aws configure`
5. flask run
6. Sample API request to upload image data:
   `curl --location --request POST 'http://ec2-18-136-207-128.ap-southeast-1.compute.amazonaws.com:5000/upload_image' \
--header 'content-type: application/json' \
--data-raw '{
    "imageName" : "abc",
    "imageUrl" : "https://firebasestorage.googleapis.com/v0/b/bukuwarung-app.appspot.com/o/invoice_images%2F1.jpeg?alt=media&token=5b113022-c5a0-41c3-a576-5ff2292be9cc",
    "bookId" : "book-01",
    "userId" : "user-01",
    "uploadId" : "upload-01"
}'`
