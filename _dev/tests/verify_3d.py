import pymeshlab
from pathlib import Path

def test_pymeshlab():
    print("Testing PyMeshLab...")
    try:
        ms = pymeshlab.MeshSet()
        
        # Create a cube
        print("Creating Cube...")
        ms.create_cube()
        
        # Save it
        output = Path("tests/test_cube.obj")
        ms.save_current_mesh(str(output))
        
        if output.exists():
            print(f"✅ Success: Saved {output}")
            return True
        else:
            print("❌ Failed: Output file not found")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_pymeshlab()
