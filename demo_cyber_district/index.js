import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { GammaCorrectionShader } from 'three/addons/shaders/GammaCorrectionShader.js';

import { Terrain } from './modules/terrain.js';
import { Buildings } from './modules/buildings.js';
import { Vegetation } from './modules/vegetation.js';
import { Props } from './modules/props.js';

let container, stats;
let camera, scene, renderer, controls;
let composer;
let terrain, buildings, vegetation, props;
let robotMixer = null;
let helmetModel = null;
const clock = new THREE.Clock();

init();
animate();

function init() {
    container = document.createElement('div');
    document.body.appendChild(container);

    // Renderer with Hardware MSAA & Tone Mapping
    renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.25;
    container.appendChild(renderer.domElement);

    // Camera - Vantage perspective overlooking central plaza and cyber boulevard
    camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 1, 1000);
    camera.position.set(0, 45, 110);

    // Scene & 360 Studio Room Environment Reflection
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x050811);
    scene.fog = new THREE.FogExp2(0x050811, 0.007);

    const pmremGenerator = new THREE.PMREMGenerator(renderer);
    scene.environment = pmremGenerator.fromScene(new RoomEnvironment(), 0.04).texture;

    // Controls
    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.target.set(0, 8, 0);
    controls.maxPolarAngle = Math.PI / 2 - 0.02;
    controls.minDistance = 10;
    controls.maxDistance = 250;

    // Lights
    const ambientLight = new THREE.AmbientLight(0x1a233a, 1.8);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x00f0ff, 2.2);
    dirLight.position.set(50, 90, 60);
    dirLight.castShadow = true;
    dirLight.shadow.camera.top = 120;
    dirLight.shadow.camera.bottom = -120;
    dirLight.shadow.camera.left = -120;
    dirLight.shadow.camera.right = 120;
    dirLight.shadow.camera.near = 0.1;
    dirLight.shadow.camera.far = 350;
    dirLight.shadow.mapSize.width = 2048;
    dirLight.shadow.mapSize.height = 2048;
    scene.add(dirLight);

    const warmLight = new THREE.DirectionalLight(0xff0077, 1.4);
    warmLight.position.set(-60, 50, -40);
    scene.add(warmLight);

    // Initialize Modular Components
    terrain = new Terrain();
    terrain.addTo(scene);

    buildings = new Buildings();
    buildings.addTo(scene);

    vegetation = new Vegetation();
    vegetation.addTo(scene);

    props = new Props();
    props.addTo(scene);

    // Draco & GLTF Loaders for 3D Assets
    const dracoLoader = new DRACOLoader();
    dracoLoader.setDecoderPath('./vendor/addons/libs/draco/gltf/');
    const gltfLoader = new GLTFLoader();
    gltfLoader.setDRACOLoader(dracoLoader);

    // 1. Patrol AI Robot
    gltfLoader.load('./models/RobotExpressive.glb', (gltf) => {
        const robot = gltf.scene;
        robot.scale.set(1.8, 1.8, 1.8);
        robot.position.set(0, 0, 15);
        robot.traverse((child) => {
            if (child.isMesh) {
                child.castShadow = true;
                child.receiveShadow = true;
            }
        });
        scene.add(robot);

        if (gltf.animations && gltf.animations.length > 0) {
            robotMixer = new THREE.AnimationMixer(robot);
            const clip = THREE.AnimationClip.findByName(gltf.animations, 'Wave') ||
                         THREE.AnimationClip.findByName(gltf.animations, 'Idle') ||
                         gltf.animations[0];
            if (clip) {
                const action = robotMixer.clipAction(clip);
                action.play();
            }
        }
    }, undefined, (err) => console.warn('Robot load error:', err));

    // 2. Patrol Cyber Vehicle (Ferrari GLB)
    gltfLoader.load('./models/ferrari.glb', (gltf) => {
        const car = gltf.scene;
        car.scale.set(1.6, 1.6, 1.6);
        car.position.set(-20, 0, 16);
        car.rotation.y = 0.35;
        car.traverse((child) => {
            if (child.isMesh) {
                child.castShadow = true;
                child.receiveShadow = true;
                const matName = (child.material && child.material.name ? child.material.name : '').toLowerCase();
                if (matName.includes('body') || matName.includes('red') || matName.includes('paint')) {
                    child.material = new THREE.MeshPhysicalMaterial({
                        color: 0x00d9ff,
                        metalness: 0.85,
                        roughness: 0.15,
                        clearcoat: 1.0,
                        clearcoatRoughness: 0.05
                    });
                }
            }
        });
        scene.add(car);
    }, undefined, (err) => console.warn('Car load error:', err));

    // 3. Futuristic Battle Monument (Damaged Helmet GLB on glowing Pedestal)
    const pedestalGeo = new THREE.CylinderGeometry(3.5, 4.5, 2.5, 8);
    const pedestalMat = new THREE.MeshStandardMaterial({
        color: 0x111928,
        metalness: 0.9,
        roughness: 0.2,
        emissive: 0x00f0ff,
        emissiveIntensity: 0.2
    });
    const pedestal = new THREE.Mesh(pedestalGeo, pedestalMat);
    pedestal.position.set(22, 1.25, 16);
    pedestal.castShadow = true;
    pedestal.receiveShadow = true;
    scene.add(pedestal);

    gltfLoader.load('./models/DamagedHelmet.glb', (gltf) => {
        helmetModel = gltf.scene;
        helmetModel.scale.set(3.2, 3.2, 3.2);
        helmetModel.position.set(22, 4.2, 16);
        helmetModel.traverse((child) => {
            if (child.isMesh) {
                child.castShadow = true;
                child.receiveShadow = true;
            }
        });
        scene.add(helmetModel);
    }, undefined, (err) => console.warn('Helmet load error:', err));

    // Post Processing / Bloom Pipeline
    const renderScene = new RenderPass(scene, camera);
    const bloomPass = new UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), 1.2, 0.4, 0.85);
    bloomPass.threshold = 0.2;
    bloomPass.strength = 1.0;
    bloomPass.radius = 0.4;

    composer = new EffectComposer(renderer);
    composer.addPass(renderScene);
    composer.addPass(bloomPass);
    composer.addPass(new ShaderPass(GammaCorrectionShader));

    // UI Event Listeners
    window.addEventListener('resize', onWindowResize);
    setupUIControls();
}

function setupUIControls() {
    const btnReset = document.getElementById('btn-reset');
    if (btnReset) {
        btnReset.addEventListener('click', () => {
            camera.position.set(0, 45, 110);
            controls.target.set(0, 8, 0);
            controls.update();
        });
    }

    const btnTime = document.getElementById('btn-time');
    if (btnTime) {
        let night = true;
        btnTime.addEventListener('click', () => {
            night = !night;
            if (night) {
                scene.background.set(0x050811);
                scene.fog.color.set(0x050811);
                btnTime.innerText = 'Switch Day/Night (Night)';
            } else {
                scene.background.set(0x1a2b4c);
                scene.fog.color.set(0x1a2b4c);
                btnTime.innerText = 'Switch Day/Night (Day)';
            }
        });
    }
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    composer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
    requestAnimationFrame(animate);

    const delta = clock.getDelta();

    // Update modules
    if (terrain) terrain.update(delta);
    if (buildings) buildings.update(delta);
    if (vegetation) vegetation.update(delta);
    if (props) props.update(delta);

    if (robotMixer) {
        robotMixer.update(delta);
    }
    if (helmetModel) {
        helmetModel.rotation.y += delta * 0.4;
    }

    controls.update();
    composer.render();
}
