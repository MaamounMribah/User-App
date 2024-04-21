# Flask app with adjustments
from flask import Flask, render_template, request, session, jsonify, redirect, url_for
from urllib.parse import unquote, quote
from google.cloud import storage
from werkzeug.utils import secure_filename
from datetime import timedelta
import requests
import os
import json

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.permanent_session_lifetime = timedelta(minutes=1)

# Google Cloud Storage setup
storage_client = storage.Client()

bucket_name = 'my-bucket-int-infra-training-gcp'
source_file_name = 'keywords.json'
destination_blob_name = 'keywords.json'
pv_mount_path='/mnt/gcs'

def upload_to_gcs_and_pv(storage_client,bucket_name, source_file_name, destination_blob_name, pv_mount_path):
    """Uploads a file to the bucket and writes it to Persistent Volume."""
    
    # Upload to GCS
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print(f"File {source_file_name} uploaded to {destination_blob_name} in GCS.")

    # Write to PV
    #pv_path = os.path.join(pv_mount_path, destination_blob_name)
    #shutil.copy(source_file_name, pv_path)
    print(f"File {source_file_name} copied to PV at {pv_path}.")



@app.route('/', methods=['GET'])
def show_keywords():
    return render_template('search_form.html', keywords=session.get('keywords', []))

@app.route('/add_keyword', methods=['POST'])
def add_keyword():
    keyword = request.form.get('keyword')
    if keyword:
        if 'keywords' not in session:
            session['keywords'] = []
        session['keywords'].append(keyword)
        session.modified = True
    return redirect(url_for('show_keywords'))

@app.route('/delete_keyword/<int:index>', methods=['POST'])
def delete_keyword(index):
    if 'keywords' in session and index < len(session['keywords']):
        session['keywords'].pop(index)
        session.modified = True
    return jsonify(status='success')

@app.route('/edit_keyword/<int:index>', methods=['POST'])
def edit_keyword(index):
    new_keyword = request.json.get("new_keyword")

    if new_keyword and new_keyword.strip():
        keywords = session.get('keywords', [])
        if index < len(keywords):
            # Update the keyword with the new value
            keywords[index] = new_keyword
            session.modified = True

    return jsonify(status='success')

@app.route('/trigger_pipeline', methods=['POST'])
def trigger_pipeline():
    token = os.getenv("GITHUB_TOKEN")
    repo = "MaamounMribah/CI-CD-Pipeline-GCP"
    workflow_id = "manifest.yaml"

    with open(source_file_name, 'w') as f:
        json.dump(session.get('keywords', []), f)

    upload_to_gcs_and_pv(storage_client, bucket_name, source_file_name, destination_blob_name,pv_mount_path)

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.json",
    }

    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_id}/dispatches"
    payload = {
        "ref": "main",
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return jsonify(status="success", message="Workflow triggered successfully.")
    else:
        error_details = response.text
        return jsonify(status="error", message="Failed to trigger workflow.", details=error_details), response.status_code

@app.errorhandler(Exception)
def handle_exception(error):
    return jsonify(status="error", message=str(error)), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
