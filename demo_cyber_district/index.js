import * as THREE from './vendor/three/three.module.js';
import { OrbitControls } from './vendor/three/OrbitControls.js';
import { RoomEnvironment } from './vendor/three/RoomEnvironment.js';
import { GLTFLoader } from './vendor/three/GLTFLoader.js';
import { EffectComposer } from './vendor/three/EffectComposer.js';
import { RenderPass } from './vendor/three/RenderPass.js';
import { UnrealBloomPass } from './vendor/three/UnrealBloomPass.js';
import { GammaCorrectionShader } from './vendor/three/GammaCorrectionShader.js';
import { ShaderPass } from './vendor/three/ShaderPass.js';

import { Terrain } from './modules/terrain.js';
import { Buildings } from './modules/buildings.js';
import { Vegetation } from './modules/vegetation.js';
import { Props } from './modules/props.js';

let container, stats;
let camera, scene, renderer, controls;
let composer;
let terrain, buildings, vegetation, props;
let robotMixer = null;
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
    renderer.toneMappingExposure = 1.2;
    container.appendChild(renderer.domElement);

    // Camera
    camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 1, 1000);
    camera.position.set(0, 35, 75);

    // Scene & 360 Studio Room Environment Reflection
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x050811);
    scene.fog = new THREE.FogExp2(0x050811, 0.008);

    const pmremGenerator = new THREE.PMREMGenerator(renderer);
    scene.environment = pmremGenerator.fromScene(new RoomEnvironment(), 0.04).texture;

    // Controls
    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2 - 0.02;
    controls.minDistance = 10;
    controls.maxDistance = 200;

    // Lights
    const ambientLight = new THREE.AmbientLight(0x1a233a, 1.5);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x00f0ff, 2.0);
    dirLight.position.set(50, 80, 50);
    dirLight.castShadow = true;
    dirLight.shadow.camera.top = 100;
    dirLight.shadow.camera.bottom = -100;
    dirLight.shadow.camera.left = -100;
    dirLight.shadow.camera.right = 100;
    dirLight.shadow.camera.near = 0.1;
    dirLight.shadow.camera.far = 300;
    dirLight.shadow.mapSize.width = 2048;
    dirLight.shadow.mapSize.height = 2048;
    scene.add(dirLight);

    // Initialize Modular Components
    terrain = new Terrain();
    terrain.addTo(scene);

    buildings = new Buildings();
    buildings.addTo(scene);

    vegetation = new Vegetation();
    vegetation.addTo(scene);

    props = new Props();
    props.addTo(scene);

    // Load Robot Expressive Asset
    const gltfLoader = new GLTFLoader();
    gltfLoader.load('./models/RobotExpressive.glb', (gltf) => {
        const robot = gltf.scene;
        robot.scale.set(1.5, 1.5, 1.5);
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
            // Play waving or walking animation if available
            const clip = THREE.AnimationClip.findByName(gltf.animations, 'Idle') || gltf.animations[0];
            if (clip) {
                const action = robotMixer.clipAction(clip);
                action.play();
            }
        }
    }, undefined, (error) => {
        console.warn('Robot model load error (fallback active):', error);
    });

    // Post Processing / Bloom Pipeline
    const renderScene = new RenderPass(scene, camera);
    const bloomPass = new UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), 1.5, 0.4, 0.85);
    bloomPass.threshold = 0.15;
    bloomPass.strength = 1.2;
    bloomPass.radius = 0.5;

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
            camera.position.set(0, 35, 75);
            controls.target.set(0, 0, 0);
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

    controls.update();
    composer.render();
}
