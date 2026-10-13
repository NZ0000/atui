/**
 * @file terrain.js
 * @description Sci-Fi Cyber District Terrain & Ground Base Module
 * Features:
 * - Procedural plane with undulating multi-octave sine/cosine height displacement.
 * - Procedural HTML5 Canvas Normal Map & Roughness Map for PBR detail.
 * - Glowing grid lines / glowing neon wireframe overlay.
 * - Receives shadows from buildings and vegetation.
 * - Standard lifecycle contract: constructor(scene, options), addTo(scene), update(delta).
 */

import * as THREE from 'three';

export class Terrain {
    /**
     * @param {THREE.Scene} scene 
     * @param {Object} options 
     */
    constructor(scene, options = {}) {
        this.scene = scene;
        this.options = Object.assign({
            width: 300,
            height: 300,
            widthSegments: 120,
            heightSegments: 120,
            color: 0x0b0f19,
            gridColor: 0x00f3ff,
            roughness: 0.8,
            metalness: 0.2
        }, options);

        this.group = new THREE.Group();
        this.mesh = null;
        this.gridHelper = null;
        this.time = 0;

        this.initTerrain();
    }

    /**
     * Generate procedural HTML5 Canvas Normal Map for micro-surface detailing.
     */
    createProceduralNormalMap() {
        const canvas = document.createElement('canvas');
        canvas.width = 512;
        canvas.height = 512;
        const ctx = canvas.getContext('2d');

        // Flat normal base (128, 128, 255)
        ctx.fillStyle = 'rgb(128, 128, 255)';
        ctx.fillRect(0, 0, 512, 512);

        // Draw circuit / panel grooves
        ctx.strokeStyle = 'rgb(60, 180, 255)';
        ctx.lineWidth = 4;
        for (let i = 0; i < 20; i++) {
            const x = (i * 37) % 512;
            const y = (i * 73) % 512;
            ctx.beginPath();
            ctx.rect(x, y, 40 + (i * 11) % 60, 40 + (i * 13) % 60);
            ctx.stroke();
        }

        // Add noise/ripples for sci-fi plating
        for (let i = 0; i < 500; i++) {
            const nx = Math.random() * 512;
            const ny = Math.random() * 512;
            const val = Math.floor(100 + Math.random() * 55);
            ctx.fillStyle = `rgb(${val}, ${val}, 255)`;
            ctx.fillRect(nx, ny, 2, 2);
        }

        const texture = new THREE.CanvasTexture(canvas);
        texture.wrapS = THREE.RepeatWrapping;
        texture.wrapT = THREE.RepeatWrapping;
        texture.repeat.set(20, 20);
        return texture;
    }

    /**
     * Generate procedural Roughness Map.
     */
    createProceduralRoughnessMap() {
        const canvas = document.createElement('canvas');
        canvas.width = 512;
        canvas.height = 512;
        const ctx = canvas.getContext('2d');

        ctx.fillStyle = 'rgb(200, 200, 200)';
        ctx.fillRect(0, 0, 512, 512);

        // Darker metal channels
        ctx.strokeStyle = 'rgb(80, 80, 80)';
        ctx.lineWidth = 3;
        for (let i = 0; i < 25; i++) {
            ctx.beginPath();
            ctx.arc((i * 41) % 512, (i * 83) % 512, 30 + (i * 7) % 40, 0, Math.PI * 2);
            ctx.stroke();
        }

        const texture = new THREE.CanvasTexture(canvas);
        texture.wrapS = THREE.RepeatWrapping;
        texture.wrapT = THREE.RepeatWrapping;
        texture.repeat.set(20, 20);
        return texture;
    }

    initTerrain() {
        // Create Plane Geometry with high segmentation for undulating hills & valleys
        const geometry = new THREE.PlaneGeometry(
            this.options.width,
            this.options.height,
            this.options.widthSegments,
            this.options.heightSegments
        );
        geometry.rotateX(-Math.PI / 2); // Lay flat on XZ plane

        // Displace vertices to form cyber terrain waves
        const pos = geometry.attributes.position;
        for (let i = 0; i < pos.count; i++) {
            const x = pos.getX(i);
            const z = pos.getZ(i);

            // Center plaza / landing pad stays flatter
            const distFromCenter = Math.sqrt(x * x + z * z);
            let factor = 1.0;
            if (distFromCenter < 50) {
                factor = (distFromCenter / 50) * (distFromCenter / 50);
            }

            const y = (
                Math.sin(x * 0.03) * Math.cos(z * 0.03) * 4.0 +
                Math.sin(x * 0.08 + z * 0.05) * 1.5 +
                Math.cos(distFromCenter * 0.05) * 2.0
            ) * factor;

            pos.setY(i, y);
        }
        geometry.computeVertexNormals();

        // Generate PBR textures
        const normalMap = this.createProceduralNormalMap();
        const roughnessMap = this.createProceduralRoughnessMap();

        const material = new THREE.MeshStandardMaterial({
            color: this.options.color,
            roughness: this.options.roughness,
            metalness: this.options.metalness,
            normalMap: normalMap,
            normalScale: new THREE.Vector2(0.6, 0.6),
            roughnessMap: roughnessMap,
            flatShading: false
        });

        this.mesh = new THREE.Mesh(geometry, material);
        this.mesh.receiveShadow = true;
        this.group.add(this.mesh);

        // Add Sci-Fi glowing grid overlay
        const gridGeometry = new THREE.PlaneGeometry(this.options.width, this.options.height, 40, 40);
        gridGeometry.rotateX(-Math.PI / 2);
        const gridMaterial = new THREE.MeshBasicMaterial({
            color: this.options.gridColor,
            wireframe: true,
            transparent: true,
            opacity: 0.15
        });
        const gridOverlay = new THREE.Mesh(gridGeometry, gridMaterial);
        gridOverlay.position.y = 0.1; // Slightly above terrain to avoid z-fighting
        this.group.add(gridOverlay);

        // Outer glow boundary ring
        const ringGeo = new THREE.RingGeometry(130, 135, 64);
        ringGeo.rotateX(-Math.PI / 2);
        const ringMat = new THREE.MeshBasicMaterial({
            color: 0x00f3ff,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.4
        });
        const ring = new THREE.Mesh(ringGeo, ringMat);
        ring.position.y = 0.2;
        this.group.add(ring);
    }

    /**
     * Add terrain group into the Three.js scene
     * @param {THREE.Scene} scene 
     */
    addTo(scene) {
        if (scene) {
            this.scene = scene;
        }
        this.scene.add(this.group);
    }

    /**
     * Update animation loop (e.g. subtle cyber pulse or energy waves)
     * @param {number} delta 
     */
    update(delta) {
        this.time += delta;
        // Optional subtle material pulse or animations can be added here
    }
}
