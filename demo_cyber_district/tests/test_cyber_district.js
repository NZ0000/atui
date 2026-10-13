import { Terrain } from '../modules/terrain.js';
import { Buildings } from '../modules/buildings.js';
import { Vegetation } from '../modules/vegetation.js';
import { Props } from '../modules/props.js';

describe('Cyber District Modules Unit Tests', () => {
    test('Terrain module exports and initializes correctly', () => {
        const terrain = new Terrain();
        if (!terrain.group || !terrain.mesh) {
            throw new Error('Terrain initialization failed');
        }
    });

    test('Buildings module exports and initializes correctly', () => {
        const buildings = new Buildings();
        if (!buildings.group || buildings.group.children.length === 0) {
            throw new Error('Buildings initialization failed');
        }
    });

    test('Vegetation module exports and uses InstancedMesh correctly', () => {
        const vegetation = new Vegetation();
        if (!vegetation.instancedMesh || vegetation.instancedMesh.count !== 200) {
            throw new Error('Vegetation InstancedMesh initialization failed');
        }
    });

    test('Props module exports and initializes correctly', () => {
        const props = new Props();
        if (!props.group || props.lamps.length === 0) {
            throw new Error('Props initialization failed');
        }
    });
});
