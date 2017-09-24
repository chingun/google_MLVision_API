import base64
import os

from flask import Flask, redirect, render_template, request
from google.cloud import datastore
from google.cloud import storage
from google.cloud import vision


app = Flask(__name__)


@app.route('/')
def homepage():
    # Create a Cloud Datastore client.
    datastore_client = datastore.Client()

    # Use the Cloud Datastore client to fetch information from Datastore about
    # each photo.
    query = datastore_client.query(kind='Photos')
    image_entities = list(query.fetch())    

    # Return a Jinja2 HTML template.
    return render_template('homepage.html', image_entities=image_entities)


@app.route('/upload_photo', methods=['GET', 'POST'])
def upload_photo():
    # Create a Cloud Storage client.
    storage_client = storage.Client()

    # Get the Cloud Storage bucket that the file will be uploaded to.
    bucket = storage_client.get_bucket('staging.stoked-legend-180807.appspot.com')
    # bucket = storage_client.get_bucket(os.environ.get('CLOUD_STORAGE_BUCKET'))

    # Create a new blob and upload the file's content to Cloud Storage.
    photo = request.files['file']
    photo2 = request.files['file1'] #2


    blob = bucket.blob(photo.filename)
    blob.upload_from_string(
            photo.read(), content_type=photo.content_type)

    blob2 = bucket.blob(photo2.filename) #2
    blob2.upload_from_string(
            photo2.read(), content_type=photo2.content_type)
    # Make the blob publicly viewable.
    blob.make_public()
    image_public_url = blob.public_url
    
    blob2.make_public() #2 
    image_public_url2 = blob2.public_url #2

    # Create a Cloud Vision client.
    vision_client = vision.ImageAnnotatorClient()

    # Retrieve a-180807.appspot.com', blob.name)
    source_uri = 'gs://{}/{}'.format('staging.stoked-legend-180807.appspot.com', blob.name)
    response = vision_client.annotate_image({
        'image': {'source': {'image_uri': source_uri}}, # 'image': {'source': {'image_uri': source_uri}},
    })
    labels = response.label_annotations
    faces = response.face_annotations
    web_entities = response.web_detection.web_entities

    source_uri2 = 'gs://{}/{}'.format('staging.stoked-legend-180807.appspot.com', blob2.name)
    response = vision_client.annotate_image({
        'image': {'source': {'image_uri':source_uri2}},
    })
    labels2 = response.label_annotations
    faces2 = response.face_annotations
    web_entities2 = response.web_detection.web_entities


    # Create a Cloud Datastore client
    datastore_client = datastore.Client()

    # The kind for the new entity
    kind = 'Photos'

    # The name/ID for the new entity
    name = blob.name
    name2 = blob2.name #2

    # Create the Cloud Datastore key for the new entity
    key = datastore_client.key(kind, name)
    key2 = datastore_client.key(kind, name2)

    # Construct the new entity using the key. Set dictionary values for entity
    # keys image_public_url and label.
    entity = datastore.Entity(key)
    entity['image_public_url'] = image_public_url
    entity['label'] = labels[0].description



    entity2 = datastore.Entity(key2)
    entity2['image_public_url'] = image_public_url2
    entity2['label'] = labels2[0].description


    # Save the new entity to Datastore
    datastore_client.put(entity)

    datastore_client.put(entity2)

    # Redirect to the home page.
    
    return render_template('homepage.html', labels=labels, web_entities=web_entities, public_url=image_public_url, labels2=labels2, web_entities2=web_entities2, public_url2=image_public_url2,)


@app.errorhandler(500)
def server_error(e):
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)