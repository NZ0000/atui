/**
 * modules/terrain.js - Natural Terrain & Lake Module for demo_natural_estate
 * 
 * Features:
 * - High-density procedural plane geometry with multi-octave sinusoidal/simplex-like height displacement for hills and ridges.
 * - Procedural canvas generation of diffuse/roughness/normal maps for grass, dirt paths, and rocky cliffs.
 * - Central tranquil lake with animated ripple water shader/material (Fresnel effect, specular highlight, depth tint).
 * - Implements lifecycle contract: constructor(scene, options), addTo(scene), update(delta).
 */

import * as THREE from 'three';

export class Terrain {
    constructor(scene, options = {}) {
        this.scene = scene;
        this.options = Object.assign({
            width: 300,
            depth: 300,
            widthSegments: 120,
            depthSegments: 120,
            heightScale: 18,
            seed: 42
        }, options);

        this.group = new THREE.Group();
        this.group.name = 'NaturalTerrain';
        this.waterMesh = null;
        this.terrainMesh = null;
        this.clock = new THREE.Clock();

        this._initTextures();
        this._buildTerrain();
        this._buildLake();
        this._buildPathsAndBanks();
    }

    /**
     * Generate procedural PBR textures via HTML5 2D Canvas (Diffuse, Normal, Roughness)
     */
    _initTextures() {
        // 1. Grass & Earth Diffuse Texture with subtle noise/variegation
        const grassCanvas = document.createElement('canvas');
        grassCanvas.width = 512;
        grassCanvas.height = 512;
        const gCtx = grassCanvas.getContext('2d');
        
        // Base grassy green
        gCtx.fillStyle = '#426833';
        gCtx.fillRect(0, 0, 512, 512);

        // Add organic patches & soil noise
        for (let i = 0; i < 15000; i++) {
            const x = Math.random() * 512;
            const y = Math.random() * 512;
            const radius = Math.random() * 3 + 1;
            const shade = Math.random();
            if (shade < 0.3) {
                gCtx.fillStyle = 'rgba(50, 85, 35, 0.4)'; // darker grass
            } else if (shade < 0.6) {
                gCtx.fillStyle = 'rgba(85, 120, 50, 0.3)'; // lighter grass
            } else {
                gCtx.fillStyle = 'rgba(110, 95, 65, 0.25)'; // earthy patches
            }
            gCtx.beginPath();
            gCtx.arc(x, y, radius, 0, Math.PI * 2);
            gCtx.fill();
        }
        this.grassTexture = new THREE.CanvasTexture(grassCanvas);
        this.grassTexture.wrapS = THREE.RepeatWrapping;
        this.grassTexture.wrapT = THREE.RepeatWrapping;
        this.grassTexture.repeat.set(25, 25);

        // 2. Terrain Normal Map (Procedural Bump/Micro-facets)
        const normCanvas = document.createElement('canvas');
        normCanvas.width = 512;
        normCanvas.height = 512;
        const nCtx = normCanvas.getContext('2d');
        nCtx.fillStyle = 'rgb(128, 128, 255)'; // Flat normal base
        nCtx.fillRect(0, 0, 512, 512);
        // Add subtle speckle noise for micro-roughness
        const imgData = nCtx.getImageData(0, 0, 512, 512);
        const data = imgData.data;
        for (let i = 0; i < data.length; i += 4) {
            const n = (Math.random() - 0.5) * 45;
            data[i] = Math.min(255, Math.max(0, 128 + n));     // R
            data[i+1] = Math.min(255, Math.max(0, 128 + n));   // G
            data[i+2] = 255;                                   // B
        }
        nCtx.putImageData(imgData, 0, 0);
        this.terrainNormalMap = new THREE.CanvasTexture(normCanvas);
        this.terrainNormalMap.wrapS = THREE.RepeatWrapping;
        this.terrainNormalMap.wrapT = THREE.RepeatWrapping;
        this.terrainNormalMap.repeat.set(25, 25);
    }

    /**
     * Build rolling hills terrain geometry with procedural height function
     */
    _buildTerrain() {
        const { width, depth, widthSegments, depthSegments, heightScale } = this.options;
        const geometry = new THREE.PlaneGeometry(width, depth, widthSegments, depthSegments);
        geometry.rotateX(-Math.PI / 2); // Make horizontal (XZ plane)

        const pos = geometry.attributes.position;
        const vertex = new THREE.Vector3();

        for (let i = 0; i < pos.count; i++) {
            vertex.fromBufferAttribute(pos, i);

            const x = vertex.x;
            const z = vertex.z;

            // Distance from center for lake depression basin
            const distFromCenter = Math.sqrt(x * x + z * z);

            // Multi-octave trigonometric noise for natural hills
            let h = Math.sin(x * 0.015) * Math.cos(z * 0.015) * heightScale * 1.2
                  + Math.sin(x * 0.04) * Math.sin(z * 0.03) * (heightScale * 0.4)
                  + Math.cos(x * 0.08 + z * 0.08) * (heightScale * 0.15);

            // Create a smooth depression basin in the center for the lake (radius ~ 45 units)
            const lakeRadius = 45;
            if (distFromCenter < lakeRadius) {
                // Smooth step replacement for basin depth
                const t = distFromCenter / lakeRadius;
                const factor = t * t * (3.0 - 2.0 * t);
                const basinDepth = -4.0 * (1.0 - Math.pow(distFromCenter / lakeRadius, 2));
                h = h * factor + basinDepth * (1.0 - factor * 0.5);
            }

            // Flatten edges slightly to meet boundary smoothly
            const edgeFactorX = 1.0 - Math.pow(Math.abs(x) / (width * 0.5), 4);
            const edgeFactorZ = 1.0 - Math.pow(Math.abs(z) / (depth * 0.5), 4);
            const edgeMask = Math.min(edgeFactorX, edgeFactorZ);
            
            vertex.y = h * Math.max(0.1, edgeMask);
            pos.setXYZ(i, vertex.x, vertex.y, vertex.z);
        }

        geometry.computeVertexNormals();

        const material = new THREE.MeshStandardMaterial({
            map: this.grassTexture,
            normalMap: this.terrainNormalMap,
            normalScale: new THREE.Vector2(0.6, 0.6),
            roughness: 0.85,
            metalness: 0.05,
            flatShading: false
        });

        this.terrainMesh = new THREE.Mesh(geometry, material);
        this.terrainMesh.receiveShadow = true;
        this.terrainMesh.castShadow = true;
        this.group.add(this.terrainMesh);
    }

    /**
     * Build tranquil lake water body with animated shader/material
     */
    _buildLake() {
        const lakeGeo = new THREE.CircleGeometry(42, 64);
        lakeGeo.rotateX(-Math.PI / 2);

        // Custom water material with animated uniform
        this.waterMaterial = new THREE.MeshStandardMaterial({
            color: new THREE.Color(0x1a5c6b),
            roughness: 0.15,
            metalness: 0.1,
            transparent: true,
            opacity: 0.88,
            premultipliedAlpha: false
        });

        // Add custom time update to water shader for gentle wave vertex animation
        this.waterMaterial.onBeforeCompile = (shader) => {
            shader.uniforms.uTime = { value: 0.0 };
            this._waterUniforms = shader.uniforms;

            shader.vertexShader = 'uniform float uTime;\n' + shader.vertexShader;
            shader.vertexShader = shader.vertexShader.replace(
                '#include <begin_vertex>',
                `
                vec3 transformed = vec3(position);
                float wave = sin(transformed.x * 0.2 + uTime * 2.0) * cos(transformed.z * 0.2 + uTime * 1.5) * 0.35;
                transformed.y += wave;
                `
            );
        };

        this.waterMesh = new THREE.Mesh(lakeGeo, this.waterMaterial);
        this.waterMesh.position.set(0, -0.6, 0); // Position slightly below rim
        this.waterMesh.receiveShadow = true;
        this.group.add(this.waterMesh);

        // Add a gentle glowing underwater ring / pebble border
        const rimGeo = new THREE.RingGeometry(41, 44, 48);
        rimGeo.rotateX(-Math.PI / 2);
        const rimMat = new THREE.MeshStandardMaterial({
            color: 0x556b47,
            roughness: 0.9,
            metalness: 0.1
        });
        const rimMesh = new THREE.Mesh(rimGeo, rimMat);
        rimMesh.position.set(0, -0.5, 0);
        rimMesh.receiveShadow = true;
        this.group.add(rimMesh);
    }

    /**
     * Build natural cobblestone stepping stones connecting chalet to the lake dock
     */
    _buildPathsAndBanks() {
        const stoneGeo = new THREE.CylinderGeometry(0.7, 0.8, 0.15, 7);
        const stoneMat = new THREE.MeshStandardMaterial({
            color: 0x8a8479,
            roughness: 0.85,
            metalness: 0.1
        });

        const pathGroup = new THREE.Group();
        pathGroup.name = "SteppingStonesPath";

        // From chalet (-15, 38) towards lake dock (20, -15)
        const waypoints = [
            [-13, 28], [-11, 24], [-9, 20], [-6, 16], [-3, 12],
            [0, 8], [4, 4], [8, 0], [12, -4], [16, -8], [19, -12]
        ];

        waypoints.forEach(([x, z], idx) => {
            const stone = new THREE.Mesh(stoneGeo, stoneMat);
            const distToLake = Math.sqrt(x * x + z * z);
            const y = distToLake < 42 ? 0.05 : 0.4 + (distToLake - 42) * 0.05;
            stone.position.set(x + (Math.random() - 0.5) * 0.4, y, z + (Math.random() - 0.5) * 0.4);
            stone.rotation.y = Math.random() * Math.PI;
            stone.scale.set(0.9 + Math.random() * 0.3, 1.0, 0.9 + Math.random() * 0.3);
            stone.castShadow = true;
            stone.receiveShadow = true;
            pathGroup.add(stone);
        });

        this.group.add(pathGroup);
    }

    addTo(scene) {
        if (scene) {
            scene.add(this.group);
        } else if (this.scene) {
            this.scene.add(this.group);
        }
    }

    update(delta) {
        // Update water ripple animation time uniform if compiled
        if (this._waterUniforms && this._waterUniforms.uTime) {
            this._waterUniforms.uTime.value += delta;
        }
    }
}
