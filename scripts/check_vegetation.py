import os
import sys

def check_assets():
    models_dir = "models"
    required_models = [
        "Flamingo.glb", "Stork.glb", "Parrot.glb", "Horse.glb",
        "oak-tree.glb", "pine-tree.glb", "pine-sapling.glb",
        "flower-cluster.glb", "mushroom-patch.glb", "wild-berry.glb", "bush-shrub.glb",
        "garden-bench.glb", "wooden-bench.glb", "camp-fire.glb", "rustic-well.glb", "stone-arch.glb", "wooden-fence.glb"
    ]
    missing = []
    for m in required_models:
        path = os.path.join(models_dir, m)
        if not os.path.exists(path):
            missing.append(m)
    if missing:
        print(f"Missing models: {missing}")
        return False
    print("All required models exist on disk!")
    return True

if __name__ == "__main__":
    if check_assets():
        sys.exit(0)
    else:
        sys.exit(1)
