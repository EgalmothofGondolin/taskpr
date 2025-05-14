from fastapi.testclient import TestClient
# from app.main import app 


def test_read_root(client: TestClient): 
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "User Service is running!"}