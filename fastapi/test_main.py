from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

url = "/token"
json_data = {"username": "h", "password": "h"}

response = client.post(url, data=json_data, auth=("client_id", "client_secret"))     #login to get the access token
ACCESS_TOKEN = response.json()["access_token"]    #capture test user's access token
header = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

selected_doc="Thermodynamic Equilibrium Analysis of Steam Reforming Reaction of Radioactive Waste Oil"
username="h"
target_lang="fr"
smart_doc_query="How are you?"

# Test login_for_access_token
def test_login_for_access_token():
    response = client.post(
        url = "/token",
        data = {"username": "h", "password": "h"},
        auth=("client_id", "client_secret")
    )
    assert response.status_code == 200

#Tests existing user
def test_check_user_exists():
    response = client.post(
            url = f'/check-user-exists?username={username}',
            )
    assert response.status_code == 200
    message=response.json()['user']
    assert message == False # Existing user

#Tests the summarization method
def test_summary_generation():
    response = client.post(
        url = f"/summary-generation?user_doc_title={selected_doc}&username={username}",
        headers = header
        )
    assert response.status_code == 200
    message = response.json()
    assert len(message)>0

#Tests the translation method
def test_translation_generation():
    response = client.post(
            url = f'/translation-generation?filename={selected_doc}&username={username}&translate_to={target_lang}',
            headers = header
            )
    assert response.status_code == 200

#Tests the recommendation method
def test_recommendation_generation():
    response = client.post(
            url = f'/recommendation-generation?user_doc_title={selected_doc}&username={username}',
            headers = header
            )
    assert response.status_code == 200

#Tests the smart-doc method
def test_doc_query_smart_doc():
    response = client.post(
            url = f'/doc-query-smart-doc?user_doc_title={smart_doc_query}&username={username}',
            headers = header
            )
    assert response.status_code == 200
    message=response.json()['answer']
    assert len(message) > 0