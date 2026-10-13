import os
import sys

def test_assets():
    models = ['Flamingo.glb', 'Stork.glb', 'Parrot.glb', 'Horse.glb']
    for m in models:
        p = os.path.join('models', m)
        assert os.path.exists(p), f"Asset {m} not found in models/"
        print(f"Verified asset: {p} (size: {os.path.getsize(p)} bytes)")
    
    terrain_path = 'modules/terrain.js'
    assert os.path.exists(terrain_path), "modules/terrain.js missing"
    with open(terrain_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert 'Horse.glb' in content, "Horse.glb missing in terrain.js"
        assert 'Flamingo.glb' in content, "Flamingo.glb missing in terrain.js"
        assert 'Stork.glb' in content, "Stork.glb missing in terrain.js"
        assert 'Parrot.glb' in content, "Parrot.glb missing in terrain.js"
    print("Terrain asset reference check passed successfully.")

if __name__ == '__main__':
    test_assets()
