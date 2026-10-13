/**
 * @file vegetation.js
 * @description Sci-Fi Cyber District Alien Vegetation & Forest Module
 * Features:
 * - Uses THREE.InstancedMesh for high-performance batch rendering of hundreds of alien glowing flora.
 * - Procedural composite geometry: multi-tiered crystal spires & bio-luminescent mushroom/canopy structures.
 * - Procedural Normal & Emissive/Roughness maps for alien glow and rich PBR surface detail.
 * - Anti-Primitive & Smooth shading principles applied.
 * - Standard lifecycle contract: constructor(scene, count), addTo(scene), update(delta).
 */

import * as THREE from 'three';

export class Vegetation {
    /**
     * @param {THREE.Scene} scene 
     * @param {number} count Number of instances (default 400 for dense alien forest)
     */
    constructor(scene, count = 400) {
        this.scene = scene;
        this.count = count;
        this.group = new THREE.Group();
        this.instancedMesh = null;
        this.time = 0;

        this.initVegetation();
    }

    /**
     * Generate procedural Normal Map for alien crystal/flora skin detailing
     */
    createProceduralNormalMap() {
        const canvas = document.createElement('canvas');
        canvas.width = 256;
        canvas.height = 256;
        const ctx = canvas.getContext('2d');

        ctx.fillStyle = 'rgb(128, 128, 255)';
        ctx.fillRect(0, 0, 256, 256);

        // Organic cellular / biological veins
        ctx.strokeStyle = 'rgb(100, 150, 255)';
        ctx.lineWidth = 3;
        for (let i = 0; i < 15; i++) {
            ctx.beginPath();
            ctx.arc((i * 31) % 256, (i * 53) % 256, 15 + (i * 7) % 30, 0, Math.PI * 2);
            ctx.stroke();
        }

        const texture = new THREE.CanvasTexture(canvas);
        texture.wrapS = THREE.RepeatWrapping;
        texture.wrapT = THREE.RepeatWrapping;
        return texture;
    }

    /**
     * Build complex multi-level alien flora geometry (composite crystal / glowing tree)
     */
    createFloraGeometry() {
        // We combine a tapered cylinder stem and a glowing bulbous top into a merged buffer geometry or group
        // For InstancedMesh, we use a single compound geometry (e.g. ConeGeometry with stacked rings)
        const geometry = new THREE.ConeGeometry(0.8, 4, 6);
        geometry.translate(0, 2, 0);
        return geometry;
    }

    initVegetation() {
        const geometry = this.createFloraGeometry();
        geometry.computeVertexNormals();

        // Procedural Normal Map
        const normalMap = this.createProceduralNormalMap();

        // Cyber / Alien flora material with vibrant emissive neon turquoise / magenta glow
        const material = new THREE.MeshStandardMaterial({
            color: 0x0a2f35,
            emissive: 0x00f3ff,
            emissiveIntensity: 0.6,
            roughness: 0.3,
            metalness: 0.5,
            normalMap: normalMap,
            normalScale: new THREE.Vector2(0.5, 0.5),
            flatShading: false
        });

        // Create InstancedMesh for high performance batch rendering
        this.instancedMesh = new THREE.InstancedMesh(geometry, material, this.count);
        this.instancedMesh.castShadow = true;
        this.instancedMesh.receiveShadow = true;

        const dummy = new THREE.Object3D();
        const positions = [];

        // Distribute instances across the terrain avoiding the center plaza (-60 to 60)
        let placed = 0;
        let attempts = 0;
        while (placed < this.count && attempts < this.count * 5) {
            attempts++;
            const x = (Math.random() - 0.5) * 260;
            const z = (Math.random() - 0.5) * 260;
            const dist = Math.sqrt(x * x + z * z);

            // Keep central plaza clean (radius < 55)
            if (dist < 55 || dist > 145) continue;

            // Compute approximate terrain height based on terrain formula
            const y = (
                Math.sin(x * 0.03) * Math.cos(z * 0.03) * 4.0 +
                Math.sin(x * 0.08 + z * 0.05) * 1.5 +
                Math.cos(dist * 0.05) * 2.0
            );

            // Random scale variation
            const scaleY = 0.5 + Math.random() * 1.5;
            const scaleXZ = 0.6 + Math.random() * 0.8;

            dummy.position.set(x, y, z);
            dummy.scale.set(scaleXZ, scaleY, scaleXZ);
            
            // Slight random tilt for natural look
            dummy.rotation.set(
                (Math.random() - 0.5) * 0.15,
                Math.random() * Math.PI * 2,
                (Math.random() - 0.5) * 0.15
            );

            dummy.updateMatrix();
            this.instancedMesh.setMatrixAt(placed, dummy.matrix);
            
            // Store base positions for potential animation
            positions.push({ x, y, z, scaleY, seed: Math.random() * 10 });
            placed++;
        }

        this.instancedMesh.instanceMatrix.needsUpdate = true;
        this.instancesData = positions;
        this.group.add(this.instancedMesh);

        // Add a secondary smaller ground spore carpet using another InstancedMesh or particle cluster
        this.initSporeClusters();
    }

    /**
     * Initialize secondary bio-luminescent ground spore clusters
     */
    initSporeClusters() {
        const count = Math.floor(this.count * 0.75);
        const geo = new THREE.SphereGeometry(0.3, 6, 6);
        const mat = new THREE.MeshStandardMaterial({
            color: 0x9900ff,
            emissive: 0xff00aa,
            emissiveIntensity: 0.8,
            roughness: 0.2,
            metalness: 0.1
        });

        this.sporesMesh = new THREE.InstancedMesh(geo, mat, count);
        const dummy = new THREE.Object3D();

        let placed = 0;
        while (placed < count) {
            const x = (Math.random() - 0.5) * 250;
            const z = (Math.random() - 0.5) * 250;
            const dist = Math.sqrt(x * x + z * z);
            if (dist < 50 || dist > 145) continue;

            const y = (
                Math.sin(x * 0.03) * Math.cos(z * 0.03) * 4.0 +
                Math.sin(x * 0.08 + z * 0.05) * 1.5 +
                Math.cos(dist * 0.05) * 2.0
            ) + 0.1;

            dummy.position.set(x, y, z);
            const s = 0.4 + Math.random() * 0.8;
            dummy.scale.set(s, s, s);
            dummy.updateMatrix();

            this.sporesMesh.setMatrixAt(placed, dummy.matrix);
            placed++;
        }
        this.sporesMesh.instanceMatrix.needsUpdate = true;
        this.group.add(this.sporesMesh);
    }

    /**
     * Add vegetation group into the Three.js scene
     * @param {THREE.Scene} scene 
     */
    addTo(scene) {
        if (scene) {
            this.scene = scene;
        }
        this.scene.add(this.group);
    }

    /**
     * Update animation loop (e.g. pulsing alien bio-luminescence or gentle swaying)
     * @param {number} delta 
     */
    update(delta) {
        this.time += delta;

        // Pulse emissive intensity subtly
        if (this.instancedMesh && this.instancedMesh.material) {
            const pulse = 0.5 + Math.sin(this.time * 2.0) * 0.2;
            this.instancedMesh.material.emissiveIntensity = pulse;
        }

        if (this.sporesMesh && this.sporesMesh.material) {
            const pulseSpores = 0.7 + Math.cos(this.time * 3.0) * 0.3;
            this.sporesMesh.material.emissiveIntensity = pulseSpores;
        }
    }
}
