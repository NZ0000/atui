export class Vegetation {
    /**
     * 真实针阔混交森林与高密度植被组件 (Foliage & Forest Module)
     * 使用 THREE.InstancedMesh 批量渲染松针、冷杉、白桦与灌木。
     */
    constructor(scene, count = 600) {
        this.scene = scene;
        this.count = count;
        this.group = new THREE.Group();
        this.instancedMeshes = [];
        this.time = 0;
        
        if (scene) {
            this.addTo(scene);
        }
    }

    addTo(scene) {
        this.scene = scene;
        this.initFoliage();
        scene.add(this.group);
    }

    initFoliage() {
        // 创建不同种类的树木与灌木 (松针、高山冷杉、阔叶白桦、野生灌木)
        const types = [
            { name: 'pine', count: Math.floor(this.count * 0.3), color: 0x1e3f20, trunkColor: 0x4a3525 },
            { name: 'fir', count: Math.floor(this.count * 0.3), color: 0x244830, trunkColor: 0x3d2817 },
            { name: 'birch', count: Math.floor(this.count * 0.25), color: 0x4b6b38, trunkColor: 0xdddddd },
            { name: 'shrub', count: Math.floor(this.count * 0.15), color: 0x5a7a3a, trunkColor: 0x554433 }
        ];

        types.forEach(type => {
            // 使用几何体组合模拟复合造型
            let geometry;
            if (type.name === 'pine' || type.name === 'fir') {
                geometry = new THREE.ConeGeometry(1.2, 4, 6);
            } else if (type.name === 'birch') {
                geometry = new THREE.CylinderGeometry(0.3, 0.5, 5, 6);
            } else {
                geometry = new THREE.DodecahedronGeometry(0.8, 1);
            }

            const material = new THREE.MeshStandardMaterial({
                color: type.color,
                roughness: 0.8,
                metalness: 0.1,
                flatShading: true
            });

            const instancedMesh = new THREE.InstancedMesh(geometry, material, type.count);
            instancedMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);

            const dummy = new THREE.Object3D();
            const matrix = new THREE.Matrix4();

            for (let i = 0; i < type.count; i++) {
                // 随机分布在场景中 (-80 到 80 范围)
                const x = (Math.random() - 0.5) * 160;
                const z = (Math.random() - 0.5) * 160;
                // 离中心岛屿保持一定距离或根据地形高度预估
                const distance = Math.sqrt(x * x + z * z);
                if (distance < 15) continue; // 避开中央建筑区

                const y = Math.sin(x * 0.05) * Math.cos(z * 0.05) * 3 + 1;
                const scale = 0.6 + Math.random() * 0.8;

                dummy.position.set(x, y + (type.name === 'shrub' ? 0.5 : 2), z);
                dummy.scale.set(scale, scale * (0.8 + Math.random() * 0.4), scale);
                dummy.rotation.y = Math.random() * Math.PI * 2;
                dummy.updateMatrix();

                instancedMesh.setMatrixAt(i, dummy.matrix);
            }

            instancedMesh.instanceMatrix.needsUpdate = true;
            this.group.add(instancedMesh);
            this.instancedMeshes.push(instancedMesh);
        });
    }

    update(delta) {
        this.time += delta;
        // 可选：实现微风吹拂导致的顶点或矩阵微幅晃动
    }
}
