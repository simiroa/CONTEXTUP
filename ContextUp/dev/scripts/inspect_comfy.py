
import urllib.request
import json
import sys

def inspect_nodes():
    url = "http://127.0.0.1:8190/object_info"
    print(f"Querying {url}...")
    
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
            
        nodes_to_check = ["CLIPLoader", "UNETLoader", "VAELoader", "CheckpointLoaderSimple"]
        
        for node_name in nodes_to_check:
             if node_name in data:
                 print(f"\n[{node_name}]")
                 inputs = data[node_name]['input']['required']
                 for key, val in inputs.items():
                     if isinstance(val[0], list):
                         print(f"  {key}: {val[0][:10]} ... (Total: {len(val[0])})")
                     else:
                         print(f"  {key}: {val}")
             else:
                 print(f"\n[{node_name}] NOT FOUND")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_nodes()
