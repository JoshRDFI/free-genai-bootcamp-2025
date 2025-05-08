import requests
import json
import sys

def test_api():
    """Test the API endpoints"""
    base_url = "http://localhost:5000/api"
    
    # Test health check
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health check: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        print()
    except Exception as e:
        print(f"Error connecting to API: {e}")
        print("Make sure the API server is running on port 5000")
        sys.exit(1)
    
    # Test getting all groups
    try:
        response = requests.get(f"{base_url}/groups")
        print(f"Get all groups: {response.status_code}")
        groups = response.json()
        print(f"Found {len(groups)} groups")
        print()
        
        # Test getting words for the first group
        if groups:
            group_id = groups[0]['id']
            response = requests.get(f"{base_url}/groups/{group_id}/raw")
            print(f"Get words for group {group_id}: {response.status_code}")
            words = response.json()
            print(f"Found {len(words)} words")
            print("Sample words:")
            for word in words[:3]:  # Show first 3 words
                print(f"  - {word['kanji']} ({word['romaji']}): {word['english']}")
    except Exception as e:
        print(f"Error testing API: {e}")

if __name__ == "__main__":
    print("Testing Japanese Vocabulary API...")
    test_api()
    print("\nAPI test completed.")