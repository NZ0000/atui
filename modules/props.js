/**
 * modules/props.js - Props Module for garden benches, campfires, wells, arches, and fences
 * Upgraded in Phase 6 to ensure robust GLB asset loading, shadows, and clean rendering.
 */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

export class Props {
    constructor(scene, options = {}) {
        this.scene = scene;
        this.propsGroup = new THREE.Group();
        this.propsGroup.name = 'PropsGroup';
        this.loader = new GLTFLoader();
        this._initProps();
    }

    _initProps() {
        const propConfigs = [
            { path: 'models/garden-bench.glb', pos: [-5, 0.2, 10], rot: [0, Math.PI / 4, 0], scale: [1, 1, 1] },
            { path: 'models/wooden-bench.glb', pos: [6, 0.2, 12], rot: [0, -Math.PI / 6, 0], scale: [1, 1, 1] },
            { path: 'models/camp-fire.glb', pos: [0, 0.2, 15], rot: [0, 0, 0], scale: [1, 1, 1] },
            { path: 'models/rustic-well.glb', pos: [-12, 0.2, 5], rot: [0, 0, 0], scale: [1, 1, 1] },
            { path: 'models/stone-arch.glb', pos: [0, 0.2, 32], rot: [0, 0, 0], scale: [1.2, 1.2, 1.2] },
            { path: 'models/wooden-fence.glb', pos: [-20, 0.2, 22], rot: [0, Math.PI / 2, 0], scale: [1, 1, 1] }
        ];

        propConfigs.forEach(cfg => {
            this.loader.load(cfg.path, (gltf) => {
                if (gltf && gltf.scene) {
                    const model = gltf.scene;
                    model.position.set(...cfg.pos);
                    model.rotation.set(...cfg.rot);
                    model.scale.set(...cfg.scale);
                    model.traverse(child => {
                        if (child.isMesh) {
                            child.castShadow = true;
                            child.receiveShadow = true;
                            child.material.flatShading = false;
                            if (child.geometry) child.geometry.computeVertexNormals();
                        }
                    });
                    this.propsGroup.add(model);
                }
            }, undefined, () => {
                // Fallback box/cylinder prop
                const fallback = new THREE.Mesh(
                    new THREE.BoxGeometry(1.5, 1, 1),
                    new THREE.MeshStandardMaterial({ color: 0x8b5a2b, roughness: 0.8 })
                );
                fallback.position.set(...cfg.pos);
                fallback.castShadow = true;
                this.propsGroup.add(fallback);
            });
        });
    }

    addTo(scene) {
        if (scene) scene.add(this.propsGroup);
        else if (this.scene) this.scene.add(this.propsGroup);
    }

    update(delta) {}
}
