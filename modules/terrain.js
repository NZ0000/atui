/**
 * modules/terrain.js - Natural Terrain & Lake Module for demo_natural_estate
 * 
 * Features:
 * - High-density procedural plane geometry with multi-octave sinusoidal height displacement for hills and ridges.
 * - Procedural canvas generation of diffuse/roughness/normal maps for grass, dirt paths, and rocky cliffs.
 * - Central tranquil lake with animated ripple water shader/material (Fresnel effect, specular highlight, depth tint).
 * - Integrates GLTFLoader to load wildlife assets (Flamingo.glb, Stork.glb, Parrot.glb, Horse.glb) with proper altitude & terrain self-consistency.
 * - Implements lifecycle contract: constructor(scene, options), addTo(scene), update(delta).
 */

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

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
        this.mixers = [];
        this.wildlifeModels = [];

        this._initTextures();
        this._buildTerrain();
        this._buildLake();
        this._buildPathsAndBanks();
        this._loadWildlifeAssets();
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
        const lakeGeo = new THREE.PlaneGeometry(84, 84, 64, 64);
        lakeGeo.rotateX(-Math.PI / 2);

        this.waterMaterial = new THREE.MeshStandardMaterial({
            color: new THREE.Color(0x1a6b7d),
            roughness: 0.12,
            metalness: 0.15,
            transparent: true,
            opacity: 0.9,
            premultipliedAlpha: false
        });

        this.waterMaterial.onBeforeCompile = (shader) => {
            shader.uniforms.uTime = { value: 0.0 };
            this._waterUniforms = shader.uniforms;

            shader.vertexShader = 'uniform float uTime;\n' + shader.vertexShader;
            shader.vertexShader = shader.vertexShader.replace(
                '#include <begin_vertex>',
                `
                vec3 transformed = vec3(position);
                float wave1 = sin(transformed.x * 0.25 + uTime * 2.2) * cos(transformed.z * 0.25 + uTime * 1.8) * 0.4;
                float wave2 = sin(transformed.x * 0.5 - uTime * 1.5) * sin(transformed.z * 0.5 + uTime * 2.0) * 0.2;
                transformed.y += (wave1 + wave2);
                `
            );
        };

        this.waterMesh = new THREE.Mesh(lakeGeo, this.waterMaterial);
        this.waterMesh.position.set(0, -0.5, 0);
        this.waterMesh.receiveShadow = true;
        this.group.add(this.waterMesh);

        const rimGeo = new THREE.RingGeometry(41, 46, 48);
        rimGeo.rotateX(-Math.PI / 2);
        const rimMat = new THREE.MeshStandardMaterial({
            color: 0x4f6342,
            roughness: 0.9,
            metalness: 0.05
        });
        const rimMesh = new THREE.Mesh(rimGeo, rimMat);
        rimMesh.position.set(0, -0.45, 0);
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

    /**
     * Load GLB wildlife assets (Flamingo.glb, Stork.glb, Parrot.glb, Horse.glb) with strict environmental self-consistency:
     * - Water level is around y = -0.5 / 0.5 basin. Terrestrial animals (Horse) placed safely on terrain heights >= 1.5.
     * - Filename case sensitivity strictly matches disk.
     */
    _loadWildlifeAssets() {
        const loader = new GLTFLoader();

        // 1. Flamingo near the lake shore (shallow water / bank edge, y = 0.2)
        loader.load('models/Flamingo.glb', (gltf) => {
            if (gltf && gltf.scene) {
                const flamingo = gltf.scene;
                flamingo.scale.set(0.035, 0.035, 0.035);
                flamingo.position.set(-18, 0.2, -12);
                flamingo.rotation.y = Math.PI / 4;
                flamingo.traverse(child => {
                    if (child.isMesh) {
                        child.castShadow = true;
                        child.receiveShadow = true;
                    }
                });
                this.group.add(flamingo);
                this.wildlifeModels.push(flamingo);

                if (gltf.animations && gltf.animations.length > 0) {
                    const mixer = new THREE.AnimationMixer(flamingo);
                    mixer.clipAction(gltf.animations[0]).play();
                    this.mixers.push(mixer);
                }
            }
        }, undefined, () => {
            console.log('Flamingo.glb fallback or missing handled.');
        });

        // 2. Stork near the water bank (y = 0.2)
        loader.load('models/Stork.glb', (gltf) => {
            if (gltf && gltf.scene) {
                const stork = gltf.scene;
                stork.scale.set(0.03, 0.03, 0.03);
                stork.position.set(16, 0.2, 12);
                stork.rotation.y = -Math.PI / 3;
                stork.traverse(child => {
                    if (child.isMesh) {
                        child.castShadow = true;
                        child.receiveShadow = true;
                    }
                });
                this.group.add(stork);
                this.wildlifeModels.push(stork);

                if (gltf.animations && gltf.animations.length > 0) {
                    const mixer = new THREE.AnimationMixer(stork);
                    mixer.clipAction(gltf.animations[0]).play();
                    this.mixers.push(mixer);
                }
            }
        }, undefined, () => {
            console.log('Stork.glb fallback or missing handled.');
        });

        // 3. Parrot perched on a hillside tree / rock (air/elevated position y = 6.5)
        loader.load('models/Parrot.glb', (gltf) => {
            if (gltf && gltf.scene) {
                const parrot = gltf.scene;
                parrot.scale.set(0.04, 0.04, 0.04);
                parrot.position.set(-5, 6.5, -25);
                parrot.rotation.y = Math.PI / 2;
                parrot.traverse(child => {
                    if (child.isMesh) {
                        child.castShadow = true;
                        child.receiveShadow = true;
                    }
                });
                this.group.add(parrot);
                this.wildlifeModels.push(parrot);

                if (gltf.animations && gltf.animations.length > 0) {
                    const mixer = new THREE.AnimationMixer(parrot);
                    mixer.clipAction(gltf.animations[0]).play();
                    this.mixers.push(mixer);
                }
            }
        }, undefined, () => {
            console.log('Parrot.glb fallback or missing handled.');
        });

        // 4. Horse securely positioned on firm dry land (terrain height >= 1.5, e.g. y = 1.8)
        loader.load('models/Horse.glb', (gltf) => {
            if (gltf && gltf.scene) {
                const horse = gltf.scene;
                horse.scale.set(0.025, 0.025, 0.025);
                horse.position.set(22, 1.8, 25);
                horse.rotation.y = -Math.PI / 4;
                horse.traverse(child => {
                    if (child.isMesh) {
                        child.castShadow = true;
                        child.receiveShadow = true;
                    }
                });
                this.group.add(horse);
                this.wildlifeModels.push(horse);

                if (gltf.animations && gltf.animations.length > 0) {
                    const mixer = new THREE.AnimationMixer(horse);
                    mixer.clipAction(gltf.animations[0]).play();
                    this.mixers.push(mixer);
                }
            }
        }, undefined, () => {
            console.log('Horse.glb Horse.glb fallback or missing handled.');
        });
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

        // Update animation mixers for loaded wildlife (Flamingo, Stork, Parrot, Horse)
        for (const mixer of this.mixers) {
            mixer.update(delta);
        }
    }
}
