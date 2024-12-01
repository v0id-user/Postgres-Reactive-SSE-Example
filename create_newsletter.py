import requests
import sys

def create_newsletter(title, content):
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
    
    # Create newsletter
    create_response = requests.post(
        "http://localhost:8000/newsletters",
        json={"title": title, "content": content},
        cookies={"session": session_cookie}
    )
    
    if create_response.status_code == 200:
        print("Newsletter created successfully:", create_response.json())
    else:
        print("Failed to create newsletter:", create_response.text)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_newsletter.py 'Newsletter Title' 'Newsletter Content'")
        sys.exit(1)
        
    title = sys.argv[1]
    content = sys.argv[2]
    create_newsletter(title, content)
