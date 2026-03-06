from flask import Flask
import pytest

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, World!'

def test_home():
    client = app.test_client()
    response = client.get('/')
    assert response.data == b'Hello, World!'
    assert response.status_code == 200