import * as THREE from '../vendor/three/three.module.js';

export class Buildings {
    constructor(scene, count = 24) {
        this.group = new THREE.Group();
        this.buildingCount = count;
        this.init();
        if (scene) {
            this.addTo(scene);
        }
    }

    init() {
        // Procedural futuristic cyber skyscrapers and modular blocks
        const wallMaterial = new THREE.MeshStandardMaterial({
            color: 0x111622,
            roughness: 0.3,
            metalness: 0.8
        });

        const neonColors = [0x00f0ff, 0xff0055, 0x7000ff, 0x00ff88];

        for (let i = 0; i < this.buildingCount; i++) {
            const width = 8 + Math.random() * 12;
            const depth = 8 + Math.random() * 12;
            const height = 25 + Math.random() * 65;

            // Arrange in a circular district layout avoiding center (0,0)
            const angle = (i / this.buildingCount) * Math.PI * 2 + (Math.random() * 0.2);
            const radius = 35 + Math.random() * 70;
            const x = Math.cos(angle) * radius;
            const z = Math.sin(angle) * radius;

            this.createBuildingCluster({ x, z, width, height, depth, wallMaterial, neonColors });
        }
    }

    createBuildingCluster(gridCoords) {
        const { x = 0, z = 0, width = 10, height = 40, depth = 10, wallMaterial, neonColors = [0x00f0ff, 0xff0055] } = gridCoords;

        const buildingGroup = new THREE.Group();
        buildingGroup.position.set(x, 0, z);

        // Main tower body
        const geo = new THREE.BoxGeometry(width, height, depth);
        geo.translate(0, height / 2, 0);
        
        const mat = wallMaterial || new THREE.MeshStandardMaterial({
            color: 0x111622,
            roughness: 0.3,
            metalness: 0.8
        });

        const mesh = new THREE.Mesh(geo, mat);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        buildingGroup.add(mesh);

        // Sci-fi architectural details: glowing vertical window strips / neon ribs
        const ribCount = 3 + Math.floor(Math.random() * 4);
        const colorHex = neonColors[Math.floor(Math.random() * neonColors.length)];
        const neonMat = new THREE.MeshBasicMaterial({ color: colorHex });

        for (let r = 0; r < ribCount; r++) {
            const ribGeo = new THREE.BoxGeometry(0.4, height * 0.9, 0.4);
            const ribMesh = new THREE.Mesh(ribGeo, neonMat);
            const offsetX = (r === 0) ? width / 2 + 0.1 : (r === 1) ? -width / 2 - 0.1 : 0;
            const offsetZ = (r === 2) ? depth / 2 + 0.1 : (r === 3) ? -depth / 2 - 0.1 : 0;
            ribMesh.position.set(offsetX, height / 2, offsetZ);
            buildingGroup.add(ribMesh);
        }

        // Top sci-fi spire or communication dish
        if (Math.random() > 0.4) {
            const spireGeo = new THREE.ConeGeometry(width * 0.3, 12, 4);
            spireGeo.translate(0, height + 6, 0);
            const spireMesh = new THREE.Mesh(spireGeo, mat);
            buildingGroup.add(spireMesh);

            // Beacon light
            const beaconGeo = new THREE.SphereGeometry(0.8, 8, 8);
            beaconGeo.translate(0, height + 12, 0);
            const beaconMesh = new THREE.Mesh(beaconGeo, neonMat);
            buildingGroup.add(beaconMesh);
        }

        this.group.add(buildingGroup);
        return buildingGroup;
    }

    addTo(scene) {
        scene.add(this.group);
    }

    update(delta) {
        // Optional building window flickering or lights animation
    }
}
