import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

/**
 * 乡村度假木屋与田园庄园建筑组件 (Chalet & Architecture Module)
 * 职责：
 * 1. 加载高精欧洲原木度假木屋 (cottage.glb 或程序化多级复合木屋集群降级渲染)
 * 2. 布设湖畔露台、石砌基底、木栅栏围栏与温馨暖色窗户灯光
 * 3. 实现标准生命周期：constructor(scene, options)、addTo(scene)、update(delta)
 */
export class Buildings {
    constructor(scene, options = {}) {
        this.scene = scene;
        this.options = Object.assign({
            position: new THREE.Vector3(0, 0, 0),
            scale: 1.0,
            enableLights: true
        }, options);

        this.group = new THREE.Group();
        this.group.name = "ChaletArchitectureGroup";
        this.group.position.copy(this.options.position);

        this.loaded = false;
        this.chaletMesh = null;
        this.windowsLights = [];
        this.chimneySmokeParticles = [];

        this.initProceduralChaletAndTerrace();
        this.loadExternalAsset();
    }

    /**
     * 生成程序化法线和粗糙度纹理（石砌与原木质感）
     */
    createWoodAndStoneTextures() {
        const canvas = document.createElement('canvas');
        canvas.width = 256;
        canvas.height = 256;
        const ctx = canvas.getContext('2d');

        // 木纹法线贴图基底 (平整法线 rgb: 128, 128, 255)
        ctx.fillStyle = 'rgb(128, 128, 255)';
        ctx.fillRect(0, 0, 256, 256);

        // 绘制原木纹理线条
        ctx.strokeStyle = 'rgb(100, 150, 255)';
        ctx.lineWidth = 2;
        for (let i = 0; i < 256; i += 16) {
            ctx.beginPath();
            ctx.moveTo(0, i);
            ctx.lineTo(256, i + (Math.random() * 4 - 2));
            ctx.stroke();
        }
        const woodNormal = new THREE.CanvasTexture(canvas);
        woodNormal.wrapS = THREE.RepeatWrapping;
        woodNormal.wrapT = THREE.RepeatWrapping;

        // 石砌法线
        ctx.fillStyle = 'rgb(128, 128, 255)';
        ctx.fillRect(0, 0, 256, 256);
        ctx.strokeStyle = 'rgb(180, 100, 200)';
        ctx.lineWidth = 3;
        for (let x = 0; x < 256; x += 32) {
            ctx.strokeRect(x + 2, 2, 28, 28);
            ctx.strokeRect(x + 16, 34, 28, 28);
        }
        const stoneNormal = new THREE.CanvasTexture(canvas);
        stoneNormal.wrapS = THREE.RepeatWrapping;
        stoneNormal.wrapT = THREE.RepeatWrapping;

        return { woodNormal, stoneNormal };
    }

    /**
     * 构建高质量多级复合度假木屋、露台、石砌基底与栅栏
     */
    initProceduralChaletAndTerrace() {
        const textures = this.createWoodAndStoneTextures();
        this.proceduralBody = new THREE.Group();
        this.group.add(this.proceduralBody);

        // 1. 石砌基底 (Foundation)
        const foundationGeo = new THREE.BoxGeometry(14, 1.8, 10);
        const foundationMat = new THREE.MeshStandardMaterial({
            color: 0x7c7c7c,
            roughness: 0.85,
            metalness: 0.1,
            normalMap: textures.stoneNormal,
            normalScale: new THREE.Vector2(0.6, 0.6)
        });
        const foundation = new THREE.Mesh(foundationGeo, foundationMat);
        foundation.position.set(0, 0.9, 0);
        foundation.castShadow = true;
        foundation.receiveShadow = true;
        this.proceduralBody.add(foundation);

        // 2. 主木屋主体 (Chalet Cabin Body)
        const cabinGeo = new THREE.BoxGeometry(12.8, 5.0, 8.8);
        const cabinMat = new THREE.MeshStandardMaterial({
            color: 0x8b5a2b, // 暖原木色
            roughness: 0.75,
            metalness: 0.05,
            normalMap: textures.woodNormal,
            normalScale: new THREE.Vector2(0.4, 0.4)
        });
        const cabin = new THREE.Mesh(cabinGeo, cabinMat);
        cabin.position.set(0, 4.3, 0);
        cabin.castShadow = true;
        cabin.receiveShadow = true;
        this.proceduralBody.add(cabin);

        // 3. 欧式陡峭双坡屋顶 (Roof - Gabled Roof)
        const roofShape = new THREE.Shape();
        roofShape.moveTo(-7.2, 0);
        roofShape.lineTo(0, 4.5);
        roofShape.lineTo(7.2, 0);
        roofShape.closePath();

        const extrudeSettings = {
            steps: 1,
            depth: 10.4,
            bevelEnabled: true,
            bevelThickness: 0.3,
            bevelSize: 0.3,
            bevelSegments: 3
        };
        const roofGeo = new THREE.ExtrudeGeometry(roofShape, extrudeSettings);
        roofGeo.center();
        const roofMat = new THREE.MeshStandardMaterial({
            color: 0x3d3835, // 深色石板瓦/深灰瓦片
            roughness: 0.6,
            metalness: 0.2
        });
        const roof = new THREE.Mesh(roofGeo, roofMat);
        roof.position.set(0, 9.1, 0);
        roof.castShadow = true;
        roof.receiveShadow = true;
        this.proceduralBody.add(roof);

        // 4. 石砌烟囱 (Chimney)
        const chimneyGeo = new THREE.BoxGeometry(1.6, 4.5, 1.6);
        const chimneyMat = new THREE.MeshStandardMaterial({
            color: 0x6e6e6e,
            roughness: 0.9,
            normalMap: textures.stoneNormal
        });
        const chimney = new THREE.Mesh(chimneyGeo, chimneyMat);
        chimney.position.set(3.8, 9.5, -2.0);
        chimney.castShadow = true;
        this.proceduralBody.add(chimney);

        // 5. 湖畔木质露台与甲板 (Wooden Terrace & Deck)
        const deckGeo = new THREE.BoxGeometry(16, 0.6, 7);
        const deckMat = new THREE.MeshStandardMaterial({
            color: 0xa06d3e,
            roughness: 0.7,
            normalMap: textures.woodNormal
        });
        const deck = new THREE.Mesh(deckGeo, deckMat);
        deck.position.set(0, 0.3, 6.5);
        deck.castShadow = true;
        deck.receiveShadow = true;
        this.group.add(deck);

        // 6. 木栅栏围栏 (Wooden Fences around terrace)
        const fenceGroup = new THREE.Group();
        const postMat = new THREE.MeshStandardMaterial({ color: 0x6b4423, roughness: 0.8 });
        
        // 创建简易栅栏柱与横梁
        for (let x = -7.5; x <= 7.5; x += 2.5) {
            const postGeo = new THREE.BoxGeometry(0.2, 1.2, 0.2);
            const post = new THREE.Mesh(postGeo, postMat);
            post.position.set(x, 1.1, 10.0);
            post.castShadow = true;
            fenceGroup.add(post);
        }
        const rail1Geo = new THREE.BoxGeometry(15.2, 0.15, 0.15);
        const rail1 = new THREE.Mesh(rail1Geo, postMat);
        rail1.position.set(0, 1.4, 10.0);
        fenceGroup.add(rail1);
        
        const rail2 = rail1.clone();
        rail2.position.set(0, 0.8, 10.0);
        fenceGroup.add(rail2);
        this.group.add(fenceGroup);

        // 7. 温馨窗户发光与点光源 (Warm Windows & Lights)
        // NOTE: window planes are placed inside proceduralBody so they hide along with it
        if (this.options.enableLights) {
            const windowGeos = [
                new THREE.PlaneGeometry(1.5, 2.2),
                new THREE.PlaneGeometry(1.5, 2.2)
            ];
            const windowMat = new THREE.MeshBasicMaterial({
                color: 0xffe082,
                side: THREE.DoubleSide
            });

            const win1 = new THREE.Mesh(windowGeos[0], windowMat);
            win1.position.set(-3.0, 4.5, 4.41);
            // Add to proceduralBody so it hides when cottage.glb loads
            this.proceduralBody.add(win1);

            const win2 = new THREE.Mesh(windowGeos[1], windowMat);
            win2.position.set(3.0, 4.5, 4.41);
            this.proceduralBody.add(win2);

            // 暖色点光源照亮露台 (kept always for ambience, but at lower intensity)
            const porchLight = new THREE.PointLight(0xffb74d, 1.8, 22);
            porchLight.position.set(0, 6.5, 4.0);
            porchLight.castShadow = true;
            porchLight.shadow.bias = -0.002;
            this.group.add(porchLight);
            this.windowsLights.push(porchLight);
        }
    }

    /**
     * 尝试异步加载高精欧洲原木度假木屋 (cottage.glb 或备用 CDN 资产)
     */
    loadExternalAsset() {
        const loader = new GLTFLoader();
        // 尝试加载 cottage.glb (若存在) 或兜底使用程序化高级木屋
        loader.load(
            'models/cottage.glb',
            (gltf) => {
                const model = gltf.scene;
                model.scale.set(11.0, 11.0, 11.0);
                model.position.set(0, 5.2, 0);
                model.traverse((child) => {
                    if (child.isMesh) {
                        child.castShadow = true;
                        child.receiveShadow = true;
                        if (child.geometry) {
                            child.geometry.computeVertexNormals();
                        }
                        if (child.material) {
                            child.material.roughness = Math.max(child.material.roughness, 0.45);
                            child.material.needsUpdate = true;
                        }
                    }
                });
                if (this.proceduralBody) {
                    this.proceduralBody.visible = false;
                }
                this.group.add(model);
                this.loaded = true;
                console.log("[Buildings] Successfully loaded cottage.glb model.");
            },
            (xhr) => {
                // progress
            },
            (error) => {
                // 容灾降级：若外部模型未就绪，程序化精细木屋已在 initProceduralChaletAndTerrace 中完美呈现
                console.log("[Buildings] External cottage.glb not found or failed. Using high-detail procedural chalet architecture fallback.");
                this.loaded = true;
            }
        );
    }

    addTo(scene) {
        if (scene && !scene.getObjectById(this.group.id)) {
            scene.add(this.group);
        }
    }

    update(delta) {
        // 可选：动态更新灯光微弱闪烁或烟囱粒子动画
        if (this.windowsLights.length > 0) {
            const time = Date.now() * 0.002;
            const intensity = 2.3 + Math.sin(time * 3.0) * 0.2;
            this.windowsLights.forEach(light => {
                light.intensity = intensity;
            });
        }
    }
}
