from flask import Flask, render_template, request, session, jsonify, redirect, url_for
from urllib.parse import unquote
import os
import requests

import json 
from google.cloud import storage


app = Flask(__name__)


token = os.getenv("GITHUB_TOKEN")
app.secret_key = os.getenv("SECRET_KEY")

# Usage example:
bucket_name = 'my-bucket-int-infra-training-gcp'
source_file_name = 'keywords.json'
destination_blob_name = 'keywords.json'

storage_client = storage.Client()

def upload_to_gcs(storage_client,bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    

    
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(f"File {source_file_name} uploaded to {destination_blob_name}.")

@app.route('/', methods=['GET'])
def index():
    return render_template('search_form.html', keywords=session.get('keywords', []))

@app.route('/add_keyword', methods=['POST'])
def add_keyword():
    keyword = request.form.get('keyword')
    if keyword:
        if 'keywords' not in session:
            session['keywords'] = []
        session['keywords'].append(keyword)
        session.modified = True
    return redirect(url_for('index'))



@app.route('/delete_keyword/<path:keyword>', methods=['POST'])
def delete_keyword(keyword):
    keyword = unquote(keyword)  # Decode URL-encoded keyword
    if 'keywords' in session:
        session['keywords'] = [k for k in session['keywords'] if k != keyword]
        session.modified = True
    return redirect(url_for('index'))

@app.route('/trigger_pipeline', methods=['POST'])
def trigger_pipeline():
    repo = "MaamounMribah/CI-CD-Pipeline-GCP"  # Replace with your GitHub username and repository
    workflow_id = "manifest.yaml"  # Replace with your workflow file name
    
    
    keywords = session.get('keywords', [])
    keywords_json = json.dumps(keywords)

    # Save keywords to a file
    with open('keywords.json', 'w') as f:
        json.dump(keywords, f)
    
    #upload_to_gcs(storage_client,bucket_name, source_file_name, destination_blob_name)

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.json",
        
    }
    # URL for GitHub API to dispatch a workflow
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_id}/dispatches"

    # The payload that GitHub API expects to trigger a workflow
    payload = {
        "ref": "main",  # Replace with the branch you want to dispatch the workflow on
        #"inputs": {
        #    "keyword_json": keywords_json  # Pass the JSON-encoded keywords as an input
        #}

    }

    response = requests.post(url, headers=headers, json=payload)
    # Change the success check to 200 OK status code instead of 204 No Content
    if response.status_code == 200:
        return jsonify(status="success", message="Workflow triggered successfully.")
    else:
        # Log the detailed response for debugging
        error_details = response.text
        print(f"Failed to trigger workflow. Status code: {response.status_code}, Response: {error_details}")
        # Respond with the status code for better error specificity on the front-end
        return jsonify(status="error", message="Failed to trigger workflow.", details=error_details), response.status_code




if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
