import os
import json
from acrcloud.recognizer import ACRCloudRecognizer

def identify_song(filepath):
    config = {
        'host': os.getenv("ACR_HOST", "identify-us-west-2.acrcloud.com"),
        'access_key': os.getenv("ACR_ACCESS_KEY", "2030c86ed830ad800e76bdd06953084c"),
        'access_secret': os.getenv("ACR_ACCESS_SECRET", "kBV7a86QQrhpdRP5XUZ9DA5kmulsyHxCSaQfGuVS"),
        'timeout': 10
    }
    
    try:
        recognizer = ACRCloudRecognizer(config)
        result_str = recognizer.recognize_by_file(filepath, 0)
        result = json.loads(result_str)
        
        print(f"API Response: {result}")
        
        if (result.get('status', {}).get('code') == 0 and 
            'metadata' in result and 
            'music' in result['metadata'] and 
            len(result['metadata']['music']) > 0):
            
            top = result['metadata']['music'][0]
            title = top.get("title", "Unknown")
            artist = "Unknown"
            
            if "artists" in top and len(top["artists"]) > 0:
                artist = top["artists"][0].get("name", "Unknown")
            
            return {"title": title, "artist": artist}
        else:
            return {"title": "Unknown", "artist": "Song not recognized"}
            
    except Exception as e:
        return {"title": "Error", "artist": str(e)}