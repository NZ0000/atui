/**
 * Test script for vegetation module and asset references
 */
import fs from 'fs';

const assets = [
    'models/oak-tree.glb',
    'models/pine-tree.glb',
    'models/pine-sapling.glb',
    'models/flower-cluster.glb',
    'models/mushroom-patch.glb',
    'models/wild-berry.glb',
    'models/bush-shrub.glb',
    'models/Flamingo.glb',
    'models/Stork.glb',
    'models/Parrot.glb'
];

for (const asset of assets) {
    if (!fs.existsSync(asset)) {
        console.error(`Missing asset: ${asset}`);
        process.exit(1);
    }
}
console.log('All vegetation and wildlife assets verified successfully.');
process.exit(0);
