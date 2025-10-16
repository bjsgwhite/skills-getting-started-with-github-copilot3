import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_root_redirect():
    response = client.get("/")
    assert response.status_code in [200, 307]  # Allow both direct response and redirect
    if response.status_code == 307:
        assert response.headers["location"] == "/static/index.html"

def test_get_activities():
    response = client.get("/activities")
    assert response.status_code == 200
    activities = response.json()
    
    # Check if response contains expected activities
    assert "Chess Club" in activities
    assert "Programming Class" in activities
    
    # Verify activity structure
    chess_club = activities["Chess Club"]
    assert "description" in chess_club
    assert "schedule" in chess_club
    assert "max_participants" in chess_club
    assert "participants" in chess_club
    assert isinstance(chess_club["participants"], list)

def test_signup_success():
    # Test successful signup
    response = client.post("/activities/Chess Club/signup?email=new_student@mergington.edu")
    assert response.status_code == 200
    assert "Signed up" in response.json()["message"]
    
    # Verify student was added
    activities = client.get("/activities").json()
    assert "new_student@mergington.edu" in activities["Chess Club"]["participants"]

def test_signup_duplicate():
    # Try to sign up same student twice
    email = "duplicate@mergington.edu"
    
    # First signup should succeed
    response = client.post(f"/activities/Programming Class/signup?email={email}")
    assert response.status_code == 200
    
    # Second signup should fail
    response = client.post(f"/activities/Programming Class/signup?email={email}")
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]

def test_signup_nonexistent_activity():
    response = client.post("/activities/NonexistentClub/signup?email=student@mergington.edu")
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]

def test_unregister_success():
    # First sign up a student
    email = "to_remove@mergington.edu"
    activity = "Art Club"
    client.post(f"/activities/{activity}/signup?email={email}")
    
    # Then unregister them
    response = client.post(f"/activities/{activity}/unregister?email={email}")
    assert response.status_code == 200
    assert "Unregistered" in response.json()["message"]
    
    # Verify student was removed
    activities = client.get("/activities").json()
    assert email not in activities[activity]["participants"]

def test_unregister_not_registered():
    response = client.post(
        "/activities/Drama Society/unregister?email=not_registered@mergington.edu"
    )
    assert response.status_code == 404
    assert "Student not found" in response.json()["detail"]

def test_unregister_nonexistent_activity():
    response = client.post(
        "/activities/NonexistentClub/unregister?email=student@mergington.edu"
    )
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]

def test_activity_full():
    activity = "Programming Class"  # Using Programming Class instead of Chess Club
    
    # First, unregister any existing participants
    activities = client.get("/activities").json()
    for participant in activities[activity]["participants"]:
        client.post(f"/activities/{activity}/unregister?email={participant}")
    
    max_participants = activities[activity]["max_participants"]
    
    # Fill up the activity
    for i in range(max_participants + 1):
        email = f"full_test_student{i}@mergington.edu"
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        if i < max_participants:
            assert response.status_code == 200, f"Failed to add student {i} when activity wasn't full"
        else:
            # This should fail as the activity is full
            assert response.status_code == 400, "Activity should be full"
            assert "Activity is full" in response.json()["detail"]
            
    # Clean up - unregister test participants
    for i in range(max_participants):
        email = f"full_test_student{i}@mergington.edu"
        client.post(f"/activities/{activity}/unregister?email={email}")