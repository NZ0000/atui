import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

/**
 * Props module for Lakeside Life & Waterfront Eco-Components
 * Generates wooden dock, rowboat, campfire stone ring, wooden bench, and animated wandering cat.
 */
export class Props {
    constructor(scene) {
        this.scene = scene;
        this.propsGroup = new THREE.Group();
        this.propsGroup.name = "LakesideProps";
        
        // Animation mixer for dynamic elements (like cat or campfire flicker)
        this.mixers = [];
        this.clock = new THREE.Clock();
        this.campfireLights = [];
        this.catModel = null;
        this.catWalkSpeed = 0.8;
        this.catAngle = 0;
        this.catRadius = 12;
        this.catCenter = new THREE.Vector3(15, 0.5, -10);

        this.initMaterials();
        this.buildDock();
        this.buildRowboat();
        this.buildCampfire();
        this.buildBenches();
        this.loadCatModel();
    }

    initMaterials() {
        // Procedural procedural wood texture & normal map generator
        const canvas = document.createElement('canvas');
        canvas.width = 512;
        canvas.height = 512;
        const ctx = canvas.getContext('2d');
        
        // Base wood tone
        ctx.fillStyle = '#8B5A2B';
        ctx.fillRect(0, 0, 512, 512);

        // Wood grain lines
        ctx.fillStyle = '#5C3818';
        for (let i = 0; i < 40; i++) {
            ctx.fillRect(0, i * 14, 512, 3);
        }
        // Grain noise
        ctx.fillStyle = 'rgba(0,0,0,0.15)';
        for (let i = 0; i < 2000; i++) {
            const x = Math.random() * 512;
            const y = Math.random() * 512;
            ctx.fillRect(x, y, Math.random() * 20, 2);
        }

        const woodTexture = new THREE.CanvasTexture(canvas);
        woodTexture.wrapS = THREE.RepeatWrapping;
        woodTexture.wrapT = THREE.RepeatWrapping;
        woodTexture.repeat.set(1, 4);

        // Normal map canvas for wood
        const normCanvas = document.createElement('canvas');
        normCanvas.width = 256;
        normCanvas.height = 256;
        const nCtx = normCanvas.getContext('2d');
        nCtx.fillStyle = 'rgb(128,128,255)';
        nCtx.fillRect(0, 0, 256, 256);
        nCtx.fillStyle = 'rgb(100,150,255)';
        for (let i = 0; i < 30; i++) {
            nCtx.fillRect(0, i * 9, 256, 2);
        }
        const woodNormalMap = new THREE.CanvasTexture(normCanvas);

        this.woodMaterial = new THREE.MeshStandardMaterial({
            map: woodTexture,
            normalMap: woodNormalMap,
            normalScale: new THREE.Vector2(0.4, 0.4),
            roughness: 0.75,
            metalness: 0.05
        });

        // Stone material for campfire ring
        const stoneCanvas = document.createElement('canvas');
        stoneCanvas.width = 256;
        stoneCanvas.height = 256;
        const sCtx = stoneCanvas.getContext('2d');
        sCtx.fillStyle = '#6E6E6E';
        sCtx.fillRect(0, 0, 256, 256);
        for (let i = 0; i < 500; i++) {
            sCtx.fillStyle = Math.random() > 0.5 ? '#555' : '#888';
            sCtx.fillRect(Math.random() * 256, Math.random() * 256, Math.random() * 15, Math.random() * 15);
        }
        const stoneTexture = new THREE.CanvasTexture(stoneCanvas);
        this.stoneMaterial = new THREE.MeshStandardMaterial({
            map: stoneTexture,
            roughness: 0.9,
            metalness: 0.1
        });

        // Metal parts material (iron nails, boat rings)
        this.metalMaterial = new THREE.MeshStandardMaterial({
            color: 0x3a3a3a,
            roughness: 0.4,
            metalness: 0.85
        });
    }

    buildDock() {
        const dockGroup = new THREE.Group();
        dockGroup.position.set(20, 0.2, -15);
        dockGroup.rotation.y = Math.PI / 6;

        // Wooden planks on top
        const plankGeo = new THREE.BoxGeometry(4.5, 0.15, 0.6);
        const plankCount = 18;
        for (let i = 0; i < plankCount; i++) {
            const plank = new THREE.Mesh(plankGeo, this.woodMaterial);
            plank.position.set(0, 0, i * 0.65 - (plankCount * 0.65) / 2);
            plank.castShadow = true;
            plank.receiveShadow = true;
            dockGroup.add(plank);
        }

        // Support piles under the dock
        const pileGeo = new THREE.CylinderGeometry(0.2, 0.25, 4, 8);
        const pilePositions = [
            [-2, -1.5, -5], [2, -1.5, -5],
            [-2, -1.5, 0], [2, -1.5, 0],
            [-2, -1.5, 5], [2, -1.5, 5]
        ];

        pilePositions.forEach(pos => {
            const pile = new THREE.Mesh(pileGeo, this.woodMaterial);
            pile.position.set(...pos);
            pile.castShadow = true;
            dockGroup.add(pile);
        });

        // Mooring post (bight) at the end of the dock
        const postGeo = new THREE.CylinderGeometry(0.25, 0.3, 1.2, 8);
        const post = new THREE.Mesh(postGeo, this.woodMaterial);
        post.position.set(0, 0.6, (plankCount * 0.65) / 2 - 0.5);
        post.castShadow = true;
        dockGroup.add(post);

        this.propsGroup.add(dockGroup);
    }

    buildRowboat() {
        const boatGroup = new THREE.Group();
        boatGroup.position.set(24, 0.1, -12);
        boatGroup.rotation.y = -Math.PI / 4;

        // Hull body using curved extrusion or composite shapes
        const hullGeo = new THREE.ConeGeometry(1.2, 3.5, 8);
        hullGeo.scale(1, 0.5, 1.8);
        // Rotate to lay flat horizontally as a hull
        hullGeo.rotateX(Math.PI / 2);
        
        const hullMat = new THREE.MeshStandardMaterial({
            color: 0x5C4033,
            roughness: 0.6,
            metalness: 0.1
        });
        const hull = new THREE.Mesh(hullGeo, hullMat);
        hull.position.y = 0.4;
        hull.castShadow = true;
        hull.receiveShadow = true;
        boatGroup.add(hull);

        // Inner seats
        const seatGeo = new THREE.BoxGeometry(1.8, 0.1, 0.4);
        const seat1 = new THREE.Mesh(seatGeo, this.woodMaterial);
        seat1.position.set(0, 0.65, 0.5);
        boatGroup.add(seat1);

        const seat2 = new THREE.Mesh(seatGeo, this.woodMaterial);
        seat2.position.set(0, 0.65, -0.6);
        boatGroup.add(seat2);

        this.propsGroup.add(boatGroup);
    }

    buildCampfire() {
        const campfireGroup = new THREE.Group();
        campfireGroup.position.set(12, 0.2, -5);

        // Stone circle ring
        const stoneCount = 9;
        const radius = 1.1;
        for (let i = 0; i < stoneCount; i++) {
            const angle = (i / stoneCount) * Math.PI * 2;
            const stoneGeo = new THREE.DodecahedronGeometry(0.35 + Math.random() * 0.1, 1);
            const stone = new THREE.Mesh(stoneGeo, this.stoneMaterial);
            stone.position.set(Math.cos(angle) * radius, 0.2, Math.sin(angle) * radius);
            stone.rotation.set(Math.random(), Math.random(), Math.random());
            stone.castShadow = true;
            stone.receiveShadow = true;
            campfireGroup.add(stone);
        }

        // Logs inside
        const logGeo = new THREE.CylinderGeometry(0.12, 0.15, 1.4, 6);
        logGeo.rotateX(Math.PI / 2);
        for (let i = 0; i < 4; i++) {
            const log = new THREE.Mesh(logGeo, this.woodMaterial);
            log.rotation.y = (i * Math.PI) / 4;
            log.position.y = 0.15;
            log.castShadow = true;
            campfireGroup.add(log);
        }

        // Warm campfire point light + glowing ember mesh
        const emberGeo = new THREE.SphereGeometry(0.4, 8, 8);
        const emberMat = new THREE.MeshStandardMaterial({
            color: 0xff4500,
            emissive: 0xff3300,
            emissiveIntensity: 1.5,
            roughness: 0.5
        });
        const embers = new THREE.Mesh(emberGeo, emberMat);
        embers.position.y = 0.2;
        campfireGroup.add(embers);

        const fireLight = new THREE.PointLight(0xff7722, 2.5, 12, 2);
        fireLight.position.set(0, 0.6, 0);
        fireLight.castShadow = true;
        fireLight.shadow.bias = -0.002;
        campfireGroup.add(fireLight);
        this.campfireLights.push(fireLight);

        this.propsGroup.add(campfireGroup);
    }

    buildBenches() {
        const benchGroup = new THREE.Group();
        benchGroup.position.set(10, 0.2, -8);
        benchGroup.rotation.y = Math.PI / 3;

        // Seat plank
        const seatGeo = new THREE.BoxGeometry(2.4, 0.12, 0.7);
        const seat = new THREE.Mesh(seatGeo, this.woodMaterial);
        seat.position.y = 0.9;
        seat.castShadow = true;
        benchGroup.add(seat);

        // Backrest plank
        const backGeo = new THREE.BoxGeometry(2.4, 0.6, 0.1);
        const back = new THREE.Mesh(backGeo, this.woodMaterial);
        back.position.set(0, 1.3, -0.3);
        back.castShadow = true;
        benchGroup.add(back);

        // Support legs
        const legGeo = new THREE.BoxGeometry(0.15, 0.9, 0.6);
        const leg1 = new THREE.Mesh(legGeo, this.woodMaterial);
        leg1.position.set(-1.0, 0.45, 0);
        leg1.castShadow = true;
        benchGroup.add(leg1);

        const leg2 = new THREE.Mesh(legGeo, this.woodMaterial);
        leg2.position.set(1.0, 0.45, 0);
        leg2.castShadow = true;
        benchGroup.add(leg2);

        this.propsGroup.add(benchGroup);
    }

    loadCatModel() {
        // Fallback procedural resting cat if GLTF fails or before load
        const catGroup = new THREE.Group();
        catGroup.name = "WanderingCat";
        catGroup.position.copy(this.catCenter);

        const bodyGeo = new THREE.SphereGeometry(0.4, 12, 12);
        bodyGeo.scale(1.3, 0.9, 1.8);
        const catMat = new THREE.MeshStandardMaterial({
            color: 0xd48347,
            roughness: 0.8,
            metalness: 0.05
        });
        const body = new THREE.Mesh(bodyGeo, catMat);
        body.position.y = 0.35;
        body.castShadow = true;
        catGroup.add(body);

        const headGeo = new THREE.SphereGeometry(0.28, 10, 10);
        const head = new THREE.Mesh(headGeo, catMat);
        head.position.set(0, 0.65, 0.75);
        head.castShadow = true;
        catGroup.add(head);

        // Ears
        const earGeo = new THREE.ConeGeometry(0.1, 0.18, 4);
        const leftEar = new THREE.Mesh(earGeo, catMat);
        leftEar.position.set(0.15, 0.9, 0.75);
        leftEar.rotation.z = -0.2;
        catGroup.add(leftEar);

        const rightEar = new THREE.Mesh(earGeo, catMat);
        rightEar.position.set(-0.15, 0.9, 0.75);
        rightEar.rotation.z = 0.2;
        catGroup.add(rightEar);

        this.catModel = catGroup;
        this.propsGroup.add(catGroup);

        // Attempt loading external catv2.glb or fallback gracefully
        const loader = new GLTFLoader();
        loader.load('models/catv2.glb', (gltf) => {
            if (gltf && gltf.scene) {
                this.propsGroup.remove(this.catModel);
                this.catModel = gltf.scene;
                this.catModel.scale.set(0.6, 0.6, 0.6);
                this.catModel.position.copy(this.catCenter);
                this.catModel.traverse(child => {
                    if (child.isMesh) {
                        child.castShadow = true;
                        child.receiveShadow = true;
                    }
                });
                this.propsGroup.add(this.catModel);

                if (gltf.animations && gltf.animations.length > 0) {
                    const mixer = new THREE.AnimationMixer(this.catModel);
                    const action = mixer.clipAction(gltf.animations[0]);
                    action.play();
                    this.mixers.push(mixer);
                }
            }
        }, undefined, (err) => {
            // Graceful fallback to procedural cat if file doesn't exist yet
            console.log('catv2.glb not found, using procedural stylized cat model.');
        });
    }

    addTo(scene) {
        scene.add(this.propsGroup);
    }

    update(delta) {
        // Update animation mixers
        for (const mixer of this.mixers) {
            mixer.update(delta);
        }

        // Campfire subtle flicker
        for (const light of this.campfireLights) {
            light.intensity = 2.3 + Math.sin(Date.now() * 0.012) * 0.3 + (Math.random() - 0.5) * 0.2;
        }

        // Wandering cat movement along a tranquil lakeside path
        if (this.catModel) {
            this.catAngle += this.catWalkSpeed * delta * 0.5;
            const x = this.catCenter.x + Math.cos(this.catAngle) * this.catRadius;
            const z = this.catCenter.z + Math.sin(this.catAngle) * (this.catRadius * 0.6);
            this.catModel.position.x = x;
            this.catModel.position.z = z;

            // Face direction of movement
            const nextX = this.catCenter.x + Math.cos(this.catAngle + 0.05) * this.catRadius;
            const nextZ = this.catCenter.z + Math.sin(this.catAngle + 0.05) * (this.catRadius * 0.6);
            this.catModel.lookAt(nextX, this.catModel.position.y, nextZ);
        }
    }
}
