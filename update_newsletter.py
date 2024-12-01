import requests
import sys
import json

def update_newsletter(newsletter_id, title, content):
    """
    Update an existing newsletter by its ID.
    
    Args:
        newsletter_id (int): ID of the newsletter to update
        title (str): New title for the newsletter
        content (str): New content for the newsletter
    """
    # Login first
    login_response = requests.post(
        "http://localhost:8000/auth",
        json={"username": "demo", "password": "demo"}
    )
    if login_response.status_code != 200:
        print("Failed to login:", login_response.text)
        return
    
    # Get session cookie
    session_cookie = login_response.cookies.get("session")
    
    url = f"http://localhost:8000/newsletters/{newsletter_id}"
    data = {
        "title": title,
        "content": content
    }
    
    try:
        response = requests.put(url, json=data, cookies={"session": session_cookie})
        response.raise_for_status()
        print(f"Successfully updated newsletter {newsletter_id}")
        print(response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error updating newsletter: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python update_newsletter.py <newsletter_id> <title> <content>")
        sys.exit(1)
    
    try:
        newsletter_id = int(sys.argv[1])
        title = sys.argv[2]
        content = sys.argv[3]
        update_newsletter(newsletter_id, title, content)
    except ValueError:
        print("Error: newsletter_id must be a number")
        sys.exit(1)
