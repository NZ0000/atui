/**
 * modules/props.js
 * Cyber District Environment Props & Holographic Streetlights Module
 * 
 * Implements:
 * - Holographic Streetlights with PointLight and glowing emissive accents
 * - Energy Beacons with pulsating animation
 * - Procedural textures and instanced or grouped props
 * - Standard lifecycle methods: constructor(), addTo(scene), update(delta)
 */

import * as THREE from 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.module.js';

export class Props {
    constructor(scene) {
        this.scene = scene;
        this.group = new THREE.Group();
        this.group.name = 'CyberPropsGroup';
        
        this.holograms = [];
        this.energyBeacons = [];
        this.time = 0;

        this.initMaterials();
        this.createStreetlights();
        this.createEnergyBeacons();
        this.createCyberBarriers();
    }

    initMaterials() {
        // Create procedural canvas normal & roughness maps for realistic sci-fi metals
        const canvas = document.createElement('canvas');
        canvas.width = 256;
        canvas.height = 256;
        const ctx = canvas.getContext('2d');
        
        // Base normal map color (128, 128, 255)
        ctx.fillStyle = 'rgb(128, 128, 255)';
        ctx.fillRect(0, 0, 256, 256);
        
        // Add panel grid lines
        ctx.strokeStyle = 'rgb(100, 150, 255)';
        ctx.lineWidth = 4;
        for (let i = 0; i <= 256; i += 32) {
            ctx.beginPath();
            ctx.moveTo(i, 0); ctx.lineTo(i, 256);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(0, i); ctx.lineTo(256, i);
            ctx.stroke();
        }
        
        this.propNormalMap = new THREE.CanvasTexture(canvas);
        this.propNormalMap.wrapS = THREE.RepeatWrapping;
        this.propNormalMap.wrapT = THREE.RepeatWrapping;
        this.propNormalMap.repeat.set(2, 2);

        // Materials
        this.metalMaterial = new THREE.MeshStandardMaterial({
            color: 0x1a2130,
            metalness: 0.9,
            roughness: 0.25,
            normalMap: this.propNormalMap,
            normalScale: new THREE.Vector2(0.4, 0.4)
        });

        this.glowBlueMaterial = new THREE.MeshStandardMaterial({
            color: 0x00f0ff,
            emissive: 0x00f0ff,
            emissiveIntensity: 3.0,
            roughness: 0.1
        });

        this.glowPinkMaterial = new THREE.MeshStandardMaterial({
            color: 0xff0055,
            emissive: 0xff0055,
            emissiveIntensity: 3.0,
            roughness: 0.1
        });
    }

    createStreetlights() {
        // Define coordinates for streetlights along main avenues
        const positions = [
            [-35, 0, -35], [35, 0, -35],
            [-35, 0, 35], [35, 0, 35],
            [-35, 0, 0], [35, 0, 0],
            [0, 0, -35], [0, 0, 35],
            [-20, 0, -20], [20, 0, -20],
            [-20, 0, 20], [20, 0, 20]
        ];

        positions.forEach(([x, y, z], index) => {
            const poleGroup = new THREE.Group();
            poleGroup.position.set(x, y, z);

            // Pole Base
            const baseGeo = new THREE.CylinderGeometry(0.8, 1.2, 1, 8);
            const baseMesh = new THREE.Mesh(baseGeo, this.metalMaterial);
            baseMesh.position.y = 0.5;
            baseMesh.castShadow = true;
            baseMesh.receiveShadow = true;
            poleGroup.add(baseMesh);

            // Tall Curved/Segmented Pole
            const poleGeo = new THREE.CylinderGeometry(0.3, 0.5, 14, 8);
            const poleMesh = new THREE.Mesh(poleGeo, this.metalMaterial);
            poleMesh.position.y = 7;
            poleMesh.castShadow = true;
            poleGroup.add(poleMesh);

            // Luminaire Head (Sci-fi ring / projector)
            const headGeo = new THREE.TorusGeometry(1.2, 0.25, 12, 24);
            const isCyan = index % 2 === 0;
            const headMat = isCyan ? this.glowBlueMaterial : this.glowPinkMaterial;
            const headMesh = new THREE.Mesh(headGeo, headMat);
            headMesh.position.set(0, 13.5, 0);
            headMesh.rotation.x = Math.PI / 2;
            poleGroup.add(headMesh);

            // Add Holographic Vertical Ring Beam
            const beamGeo = new THREE.CylinderGeometry(1.0, 1.0, 12, 16, 1, true);
            const beamMat = new THREE.MeshBasicMaterial({
                color: isCyan ? 0x00f0ff : 0xff0055,
                transparent: true,
                opacity: 0.15,
                side: THREE.DoubleSide,
                blending: THREE.AdditiveBlending
            });
            const beamMesh = new THREE.Mesh(beamGeo, beamMat);
            beamMesh.position.set(0, 7, 0);
            poleGroup.add(beamMesh);

            // Point Light for Nighttime illumination & Bloom
            const lightColor = isCyan ? 0x00f0ff : 0xff0055;
            const pointLight = new THREE.PointLight(lightColor, 2.5, 25, 2);
            pointLight.position.set(0, 13, 0);
            pointLight.castShadow = false; // Optimize performance
            poleGroup.add(pointLight);

            // Store reference for animation
            this.holograms.push({
                group: poleGroup,
                beam: beamMesh,
                light: pointLight,
                baseIntensity: 2.5,
                index: index
            });

            this.group.add(poleGroup);
        });
    }

    createEnergyBeacons() {
        // High-tech energy pillars at district hubs
        const beaconPositions = [
            [-12, 0, -12], [12, 0, -12],
            [-12, 0, 12], [12, 0, 12],
            [0, 0, 0]
        ];

        beaconPositions.forEach(([x, y, z], idx) => {
            const beaconGroup = new THREE.Group();
            beaconGroup.position.set(x, y, z);

            // Foundation pad
            const padGeo = new THREE.CylinderGeometry(3, 3.5, 0.4, 16);
            const padMesh = new THREE.Mesh(padGeo, this.metalMaterial);
            padMesh.position.y = 0.2;
            padMesh.receiveShadow = true;
            beaconGroup.add(padMesh);

            // Core energy crystal/column
            const coreGeo = new THREE.OctahedronGeometry(1.8, 0);
            const coreMat = new THREE.MeshStandardMaterial({
                color: 0x9900ff,
                emissive: 0xbd00ff,
                emissiveIntensity: 4.0,
                roughness: 0.1,
                metalness: 0.8
            });
            const coreMesh = new THREE.Mesh(coreGeo, coreMat);
            coreMesh.position.y = 5.0;
            beaconGroup.add(coreMesh);

            // Floating ring around core
            const ringGeo = new THREE.TorusGeometry(2.5, 0.15, 16, 32);
            const ringMat = this.glowBlueMaterial;
            const ringMesh = new THREE.Mesh(ringGeo, ringMat);
            ringMesh.position.y = 5.0;
            ringMesh.rotation.x = Math.PI / 2;
            beaconGroup.add(ringMesh);

            // Point light
            const beaconLight = new THREE.PointLight(0xbd00ff, 3.0, 30, 2);
            beaconLight.position.set(0, 5, 0);
            beaconGroup.add(beaconLight);

            this.energyBeacons.push({
                core: coreMesh,
                ring: ringMesh,
                light: beaconLight,
                initialY: 5.0,
                index: idx
            });

            this.group.add(beaconGroup);
        });
    }

    createCyberBarriers() {
        // Sci-fi hazard/barrier blocks near streets
        const barrierGeo = new THREE.BoxGeometry(3, 1.2, 0.6);
        const stripeCanvas = document.createElement('canvas');
        stripeCanvas.width = 128;
        stripeCanvas.height = 128;
        const sCtx = stripeCanvas.getContext('2d');
        sCtx.fillStyle = '#ffcc00';
        sCtx.fillRect(0, 0, 128, 128);
        sCtx.fillStyle = '#111111';
        sCtx.beginPath();
        sCtx.moveTo(0, 0); sCtx.lineTo(64, 0); sCtx.lineTo(0, 64); sCtx.fill();
        sCtx.beginPath();
        sCtx.moveTo(128, 0); sCtx.lineTo(128, 64); sCtx.lineTo(64, 128); sCtx.lineTo(0, 128); sCtx.fill();

        const stripeTexture = new THREE.CanvasTexture(stripeCanvas);
        stripeTexture.wrapS = THREE.RepeatWrapping;
        stripeTexture.wrapT = THREE.RepeatWrapping;
        stripeTexture.repeat.set(2, 1);

        const barrierMat = new THREE.MeshStandardMaterial({
            map: stripeTexture,
            roughness: 0.4,
            metalness: 0.6
        });

        // Place a few roadside barriers
        const barrierCoords = [
            [-8, 0.6, -18], [-5, 0.6, -18],
            [18, 0.6, -8], [18, 0.6, -5],
            [-18, 0.6, 8], [-18, 0.6, 5]
        ];

        barrierCoords.forEach(([x, y, z]) => {
            const mesh = new THREE.Mesh(barrierGeo, barrierMat);
            mesh.position.set(x, y, z);
            mesh.castShadow = true;
            mesh.receiveShadow = true;
            this.group.add(mesh);
        });
    }

    addTo(scene) {
        scene.add(this.group);
    }

    update(delta) {
        this.time += delta;

        // Animate streetlight hologram beams and slight flicker
        this.holograms.forEach(h => {
            if (h.beam) {
                h.beam.rotation.y += delta * 0.8;
            }
            if (h.light) {
                // Subtle pulse
                const pulse = Math.sin(this.time * 3.0 + h.index) * 0.3;
                h.light.intensity = h.baseIntensity + pulse;
            }
        });

        // Animate energy beacons (floating core rotation & pulsing)
        this.energyBeacons.forEach(b => {
            if (b.core) {
                b.core.rotation.y += delta * 1.5;
                b.core.rotation.x += delta * 0.5;
                b.core.position.y = b.initialY + Math.sin(this.time * 2.5 + b.index) * 0.4;
            }
            if (b.ring) {
                b.ring.rotation.z -= delta * 2.0;
            }
            if (b.light) {
                b.light.intensity = 3.0 + Math.sin(this.time * 4.0 + b.index) * 1.0;
            }
        });
    }
}
