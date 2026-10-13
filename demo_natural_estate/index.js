/**
 * index.js - Master Integration Script for demo_natural_estate (Upgraded Version)
 * 
 * Responsibilities:
 * 1. Initialize Three.js WebGLRenderer with hardware 4x MSAA, ACESFilmicToneMapping, shadows.
 * 2. Setup PerspectiveCamera and OrbitControls with smooth damping.
 * 3. Configure robust natural lighting: HemisphereLight, directional sun with soft contact shadows, RoomEnvironment, volumetric lighting rays.
 * 4. Import and instantiate all modules: Terrain, Buildings, Vegetation, Props.
 * 5. Setup post-processing pipeline: EffectComposer, RenderPass, UnrealBloomPass.
 * 6. Bind interactive HUD controls (lighting time presets, camera tour viewpoints, layer visibility toggles).
 * 7. Implement main render loop with clock delta updates and post-processing composer render.
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';

import { Terrain } from './modules/terrain.js';
import { Buildings } from './modules/buildings.js';
import { Vegetation } from './modules/vegetation.js';
import { Props } from './modules/props.js';

class NaturalEstateApp {
    constructor() {
        this.container = document.getElementById('webgl-container');
        this.clock = new THREE.Clock();
        this.modules = {};

        this._initEngine();
        this._initLighting();
        this._initSceneContent();
        this._initPostProcessing();
        this._initEvents();

        // Hide loading mask
        setTimeout(() => {
            const loaderMask = document.getElementById('loader-mask');
            if (loaderMask) {
                loaderMask.style.opacity = '0';
                setTimeout(() => loaderMask.remove(), 600);
            }
        }, 800);

        this._animate();
    }

    _initEngine() {
        // Scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x87ceeb); // Sky blue
        this.scene.fog = new THREE.FogExp2(0xa1c4df, 0.0032);

        // Camera
        this.camera = new THREE.PerspectiveCamera(
            45,
            window.innerWidth / window.innerHeight,
            0.5,
            1000
        );
        this.camera.position.set(-36, 14, 58);

        // Renderer with Hardware 4x MSAA & ACESFilmicToneMapping
        this.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.15;
        this.container.appendChild(this.renderer.domElement);

        // OrbitControls
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.maxPolarAngle = Math.PI / 2 - 0.02; // Don't go below ground
        this.controls.minDistance = 5;
        this.controls.maxDistance = 250;
        this.controls.target.set(-4, 4, 12);
    }

    _initLighting() {
        // 1. Hemisphere Light (Sky & Ground bounce)
        this.hemiLight = new THREE.HemisphereLight(0xe8f4f8, 0x4d6138, 0.9);
        this.hemiLight.position.set(0, 50, 0);
        this.scene.add(this.hemiLight);

        // 2. Main Directional Sunlight (Warm natural noon sun)
        this.dirLight = new THREE.DirectionalLight(0xfffaed, 2.3);
        this.dirLight.position.set(60, 80, 40);
        this.dirLight.castShadow = true;
        this.dirLight.shadow.mapSize.width = 2048;
        this.dirLight.shadow.mapSize.height = 2048;
        this.dirLight.shadow.camera.near = 0.5;
        this.dirLight.shadow.camera.far = 250;
        
        const d = 75;
        this.dirLight.shadow.camera.left = -d;
        this.dirLight.shadow.camera.right = d;
        this.dirLight.shadow.camera.top = d;
        this.dirLight.shadow.camera.bottom = -d;
        this.dirLight.shadow.bias = -0.0005;
        this.scene.add(this.dirLight);

        // 3. Environment lighting for realistic reflections
        const pmremGenerator = new THREE.PMREMGenerator(this.renderer);
        this.scene.environment = pmremGenerator.fromScene(new RoomEnvironment(), 0.04).texture;

        // 4. Atmospheric Volumetric Light Beams (Sun Rays)
        this._initVolumetricRays();
    }

    _initVolumetricRays() {
        this.rayGroup = new THREE.Group();
        const rayGeo = new THREE.ConeGeometry(8, 60, 16, 1, true);
        const rayMat = new THREE.MeshBasicMaterial({
            color: 0xfffae0,
            transparent: true,
            opacity: 0.12,
            blending: THREE.AdditiveBlending,
            side: THREE.DoubleSide,
            depthWrite: false
        });

        for (let i = 0; i < 4; i++) {
            const rayMesh = new THREE.Mesh(rayGeo, rayMat);
            rayMesh.position.set(-20 + i * 15, 30, -10 + i * 10);
            rayMesh.rotation.x = 0.35;
            rayMesh.rotation.z = -0.2 - i * 0.1;
            this.rayGroup.add(rayMesh);
        }
        this.scene.add(this.rayGroup);
    }

    _initSceneContent() {
        // Instantiate all modular components
        this.modules.terrain = new Terrain(this.scene);
        this.modules.terrain.addTo(this.scene);

        this.modules.buildings = new Buildings(this.scene, {
            position: new THREE.Vector3(-15, 2.5, 38),
            scale: 1.0,
            enableLights: true
        });
        this.modules.buildings.addTo(this.scene);

        this.modules.vegetation = new Vegetation(this.scene, 800);

        this.modules.props = new Props(this.scene);
    }

    _initPostProcessing() {
        // Create WebGL 2 RenderTarget with 4x MSAA samples to prevent shader jagged edges & optical bloom clipping
        const renderTarget = new THREE.WebGLRenderTarget(
            window.innerWidth * window.devicePixelRatio,
            window.innerHeight * window.devicePixelRatio,
            { samples: 4 }
        );

        this.composer = new EffectComposer(this.renderer, renderTarget);
        
        const renderPass = new RenderPass(this.scene, this.camera);
        this.composer.addPass(renderPass);

        // Cinematic UnrealBloomPass for glowing lights, windows, water specualrs and atmospheric rays
        const bloomPass = new UnrealBloomPass(
            new THREE.Vector2(window.innerWidth, window.innerHeight),
            0.42,  // strength
            0.45,  // radius
            0.82   // threshold
        );
        this.composer.addPass(bloomPass);
    }

    _initEvents() {
        // Window resize
        window.addEventListener('resize', () => {
            const width = window.innerWidth;
            const height = window.innerHeight;
            this.camera.aspect = width / height;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(width, height);
            this.composer.setSize(width, height);
        });

        // HUD: Time of Day buttons
        const btnNoon = document.getElementById('btn-noon');
        const btnSunset = document.getElementById('btn-sunset');
        const btnNight = document.getElementById('btn-night');

        const setTimePreset = (preset) => {
            [btnNoon, btnSunset, btnNight].forEach(b => b.classList.remove('active'));
            
            if (preset === 'noon') {
                btnNoon.classList.add('active');
                this.scene.background.set(0x87ceeb);
                this.scene.fog.color.set(0xa1c4df);
                this.hemiLight.color.set(0xffffff);
                this.hemiLight.groundColor.set(0x445533);
                this.hemiLight.intensity = 0.9;
                this.dirLight.color.set(0xfffaed);
                this.dirLight.intensity = 2.3;
                this.dirLight.position.set(60, 80, 40);
                this.renderer.toneMappingExposure = 1.15;
                if (this.rayGroup) this.rayGroup.visible = true;
            } else if (preset === 'sunset') {
                btnSunset.classList.add('active');
                this.scene.background.set(0x483248);
                this.scene.fog.color.set(0x523d4c);
                this.hemiLight.color.set(0xff9e64);
                this.hemiLight.groundColor.set(0x2a2421);
                this.hemiLight.intensity = 0.95;
                this.dirLight.color.set(0xff7b39);
                this.dirLight.intensity = 2.8;
                this.dirLight.position.set(-80, 25, 60);
                this.renderer.toneMappingExposure = 1.25;
                if (this.rayGroup) this.rayGroup.visible = true;
            } else if (preset === 'night') {
                btnNight.classList.add('active');
                this.scene.background.set(0x070b12);
                this.scene.fog.color.set(0x0b1320);
                this.hemiLight.color.set(0x1e3a8a);
                this.hemiLight.groundColor.set(0x090d16);
                this.hemiLight.intensity = 0.25;
                this.dirLight.color.set(0x93c5fd);
                this.dirLight.intensity = 0.4;
                this.dirLight.position.set(20, 60, -40);
                this.renderer.toneMappingExposure = 0.85;
                if (this.rayGroup) this.rayGroup.visible = false;
            }
        };

        if (btnNoon) btnNoon.addEventListener('click', () => setTimePreset('noon'));
        if (btnSunset) btnSunset.addEventListener('click', () => setTimePreset('sunset'));
        if (btnNight) btnNight.addEventListener('click', () => setTimePreset('night'));

        // HUD: Camera Viewpoints
        const camOverview = document.getElementById('cam-overview');
        const camChalet = document.getElementById('cam-chalet');
        const camDock = document.getElementById('cam-dock');

        if (camOverview) camOverview.addEventListener('click', () => {
            this._tweenCamera(new THREE.Vector3(40, 22, 58), new THREE.Vector3(5, 4, 10), 1200);
        });
        if (camChalet) camChalet.addEventListener('click', () => {
            this._tweenCamera(new THREE.Vector3(-6, 4.5, 22), new THREE.Vector3(-15, 4.5, 38), 1200);
        });
        if (camDock) camDock.addEventListener('click', () => {
            this._tweenCamera(new THREE.Vector3(28, 4.0, -6), new THREE.Vector3(20, 1.0, -14), 1200);
        });

        // HUD: Component Visibility Toggles
        const toggleTerrain = document.getElementById('toggle-terrain');
        const toggleBuildings = document.getElementById('toggle-buildings');
        const toggleVegetation = document.getElementById('toggle-vegetation');
        const toggleProps = document.getElementById('toggle-props');

        if (toggleTerrain) toggleTerrain.addEventListener('change', (e) => {
            if (this.modules.terrain) this.modules.terrain.group.visible = e.target.checked;
        });
        if (toggleBuildings) toggleBuildings.addEventListener('change', (e) => {
            if (this.modules.buildings) this.modules.buildings.group.visible = e.target.checked;
        });
        if (toggleVegetation) toggleVegetation.addEventListener('change', (e) => {
            if (this.modules.vegetation) this.modules.vegetation.group.visible = e.target.checked;
        });
        if (toggleProps) toggleProps.addEventListener('change', (e) => {
            if (this.modules.props) this.modules.props.propsGroup.visible = e.target.checked;
        });
    }

    _tweenCamera(targetPos, targetLookAt, duration = 1000) {
        const startPos = this.camera.position.clone();
        const startTarget = this.controls.target.clone();
        const startTime = performance.now();

        const updateTween = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1.0);
            const ease = 1.0 - (1.0 - progress) * (1.0 - progress);

            this.camera.position.lerpVectors(startPos, targetPos, ease);
            this.controls.target.lerpVectors(startTarget, targetLookAt, ease);
            this.controls.update();

            if (progress < 1.0) {
                requestAnimationFrame(updateTween);
            }
        };
        requestAnimationFrame(updateTween);
    }

    _animate() {
        requestAnimationFrame(() => this._animate());

        const delta = this.clock.getDelta();

        // Update all active modules implementing lifecycle update(delta)
        if (this.modules.terrain) this.modules.terrain.update(delta);
        if (this.modules.buildings) this.modules.buildings.update(delta);
        if (this.modules.vegetation) this.modules.vegetation.update(delta);
        if (this.modules.props) this.modules.props.update(delta);

        // Gentle floating animation for volumetric sun rays
        if (this.rayGroup) {
            this.rayGroup.children.forEach((ray, i) => {
                ray.rotation.y += delta * 0.05 * (i % 2 === 0 ? 1 : -1);
            });
        }

        this.controls.update();
        this.composer.render();
    }
}

// Start application when DOM is ready
window.addEventListener('DOMContentLoaded', () => {
    new NaturalEstateApp();
});
