/**
 * modules/vegetation.js - Vegetation Module with real GLB trees and scattered flora
 */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

export class Vegetation {
    constructor(scene, options = {}) {
        this.scene = scene;
        this.group = new THREE.Group();
        this.group.name = 'VegetationGroup';
        this.loader = new GLTFLoader();
        this.mixers = [];
        this._initTrees();
        this._initFlora();
        this._initInstancedGrass();
    }

    _initTrees() {
        const treeConfigs = [
            { path: 'models/oak-tree.glb', pos: [-35, 0.2, -25], scale: [1.2, 1.2, 1.2] },
            { path: 'models/oak-tree.glb', pos: [40, 0.2, 30], scale: [1.0, 1.0, 1.0] },
            { path: 'models/pine-tree.glb', pos: [-45, 0.2, 20], scale: [1.5, 1.5, 1.5] },
            { path: 'models/pine-tree.glb', pos: [35, 0.2, -35], scale: [1.3, 1.3, 1.3] },
            { path: 'models/pine-sapling.glb', pos: [-15, 0.2, 35], scale: [0.8, 0.8, 0.8] },
            { path: 'models/pine-sapling.glb', pos: [18, 0.2, 25], scale: [0.9, 0.9, 0.9] }
        ];

        treeConfigs.forEach(cfg => {
            this.loader.load(cfg.path, (gltf) => {
                if (gltf && gltf.scene) {
                    const model = gltf.scene;
                    model.position.set(...cfg.pos);
                    model.scale.set(...cfg.scale);
                    model.traverse(child => {
                        if (child.isMesh) {
                            child.castShadow = true;
                            child.receiveShadow = true;
                            child.material.flatShading = false;
                            if (child.geometry) child.geometry.computeVertexNormals();
                        }
                    });
                    this.group.add(model);
                }
            }, undefined, () => {
                // Fallback procedural trunk & canopy if glb missing
                const fallbackGroup = new THREE.Group();
                fallbackGroup.position.set(...cfg.pos);
                const trunk = new THREE.Mesh(
                    new THREE.CylinderGeometry(0.5, 0.7, 4, 6),
                    new THREE.MeshStandardMaterial({ color: 0x5c4033, roughness: 0.9 })
                );
                trunk.position.y = 2;
                trunk.castShadow = true;
                const leaves = new THREE.Mesh(
                    new THREE.SphereGeometry(2.5, 7, 7),
                    new THREE.MeshStandardMaterial({ color: 0x2e6b30, roughness: 0.8 })
                );
                leaves.position.y = 4.5;
                leaves.castShadow = true;
                fallbackGroup.add(trunk, leaves);
                this.group.add(fallbackGroup);
            });
        });
    }

    _initFlora() {
        const floraConfigs = [
            { path: 'models/flower-cluster.glb', pos: [-10, 0.1, -10] },
            { path: 'models/flower-cluster.glb', pos: [12, 0.1, -14] },
            { path: 'models/mushroom-patch.glb', pos: [-25, 0.1, -5] },
            { path: 'models/wild-berry.glb', pos: [22, 0.1, 15] },
            { path: 'models/bush-shrub.glb', pos: [-30, 0.1, -18] },
            { path: 'models/bush-shrub.glb', pos: [28, 0.1, -22] }
        ];

        floraConfigs.forEach(cfg => {
            this.loader.load(cfg.path, (gltf) => {
                if (gltf && gltf.scene) {
                    const model = gltf.scene;
                    model.position.set(...cfg.pos);
                    model.scale.set(0.8, 0.8, 0.8);
                    model.traverse(child => {
                        if (child.isMesh) {
                            child.castShadow = true;
                            child.receiveShadow = true;
                            child.material.flatShading = false;
                            if (child.geometry) child.geometry.computeVertexNormals();
                        }
                    });
                    this.group.add(model);
                }
            }, undefined, () => {});
        });
    }

    _initInstancedGrass() {
        const count = 300;
        const geometry = new THREE.PlaneGeometry(0.4, 0.8);
        geometry.translate(0, 0.4, 0);
        const material = new THREE.MeshStandardMaterial({
            color: 0x558833,
            roughness: 0.85,
            side: THREE.DoubleSide
        });

        const instancedMesh = new THREE.InstancedMesh(geometry, material, count);
        const dummy = new THREE.Object3D();

        for (let i = 0; i < count; i++) {
            const angle = Math.random() * Math.PI * 2;
            const r = 25 + Math.random() * 80;
            const x = Math.cos(angle) * r;
            const z = Math.sin(angle) * r;
            dummy.position.set(x, 0.2, z);
            dummy.scale.set(0.6 + Math.random() * 0.8, 0.6 + Math.random() * 0.8, 0.6 + Math.random() * 0.8);
            dummy.rotation.y = Math.random() * Math.PI;
            dummy.updateMatrix();
            instancedMesh.setMatrixAt(i, dummy.matrix);
        }
        instancedMesh.instanceMatrix.needsUpdate = true;
        this.group.add(instancedMesh);
    }

    addTo(scene) {
        if (scene) scene.add(this.group);
        else if (this.scene) this.scene.add(this.group);
    }

    update(delta) {}
}
