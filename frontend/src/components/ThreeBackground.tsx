import { useEffect, useRef } from "react";
import * as THREE from "three";

export default function ThreeBackground() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0x000000, 1);
    container.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 200);
    camera.position.set(0, 0, 10);

    const uniforms = {
      uTime: { value: 0 },
      uMouse: { value: new THREE.Vector2(0, 0) },
      uResolution: { value: new THREE.Vector2(window.innerWidth, window.innerHeight) }
    };

    // --- Blue Aurora Plane ---
    const auroraGeo = new THREE.PlaneGeometry(160, 100);
    
    const auroraVertexShader = `
      varying vec2 vUv;
      void main() {
        vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `;

    const auroraFragmentShader = `
      uniform float uTime;
      varying vec2 vUv;

      void main() {
        vec2 uv = vUv;
        
        // Deep space dark background
        vec3 col = vec3(0.01, 0.02, 0.05);

        // Calculate smooth flowing aurora waves
        float wave1 = sin(uv.x * 3.0 + uTime * 0.2) * 0.25 + 0.5;
        float wave2 = cos(uv.x * 4.0 - uTime * 0.15) * 0.2 + 0.4;
        float wave3 = sin(uv.x * 2.0 + uTime * 0.1) * 0.3 + 0.6;
        
        // Distance from current pixel to the waves
        float dist1 = abs(uv.y - wave1);
        float dist2 = abs(uv.y - wave2);
        float dist3 = abs(uv.y - wave3);

        // Exponential falloff for soft glowing bands
        float glow1 = exp(-dist1 * 3.5);
        float glow2 = exp(-dist2 * 4.5);
        float glow3 = exp(-dist3 * 2.5);

        // Pure Blue Aurora colors
        vec3 colorCyan = vec3(0.0, 0.8, 1.0);
        vec3 colorRoyalBlue = vec3(0.1, 0.3, 1.0);
        vec3 colorDeepBlue = vec3(0.05, 0.1, 0.6);
        vec3 colorLightBlue = vec3(0.4, 0.9, 1.0);
        
        // Horizontally mix the colors for a dynamic gradient
        vec3 baseColor1 = mix(colorRoyalBlue, colorCyan, sin(uv.x * 3.0) * 0.5 + 0.5);
        vec3 baseColor2 = mix(colorDeepBlue, colorLightBlue, cos(uv.x * 2.0) * 0.5 + 0.5);
        vec3 baseColor3 = mix(colorRoyalBlue, vec3(0.0, 0.5, 1.0), uv.x);
        
        col += baseColor1 * glow1 * 0.5;
        col += baseColor2 * glow2 * 0.4;
        col += baseColor3 * glow3 * 0.3;
        
        // Bottom ambient glow
        float ambient = exp(-uv.y * 2.5);
        col += colorDeepBlue * ambient * 0.3;

        gl_FragColor = vec4(col, 1.0);
      }
    `;

    const auroraMat = new THREE.ShaderMaterial({
      vertexShader: auroraVertexShader,
      fragmentShader: auroraFragmentShader,
      uniforms,
      depthWrite: false
    });
    
    const auroraMesh = new THREE.Mesh(auroraGeo, auroraMat);
    // Push the aurora far into the background
    auroraMesh.position.z = -60;
    scene.add(auroraMesh);

    // --- 3D Starfield ---
    const starCount = 2500;
    const starPositions = new Float32Array(starCount * 3);
    const starRandoms = new Float32Array(starCount);

    for (let i = 0; i < starCount; i++) {
      const i3 = i * 3;
      // Widespread galaxy structure
      starPositions[i3] = (Math.random() - 0.5) * 140;
      starPositions[i3 + 1] = (Math.random() - 0.5) * 90;
      // Stars layered between the aurora and the camera
      starPositions[i3 + 2] = (Math.random() - 0.5) * 60 - 15;
      
      starRandoms[i] = Math.random();
    }

    const starGeo = new THREE.BufferGeometry();
    starGeo.setAttribute("position", new THREE.BufferAttribute(starPositions, 3));
    starGeo.setAttribute("random", new THREE.BufferAttribute(starRandoms, 1));

    const starVertexShader = `
      uniform float uTime;
      attribute float random;
      varying float vRandom;
      
      void main() {
        vRandom = random;
        vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
        // Vary size slightly by randomness and depth
        gl_PointSize = (3.0 + random * 4.0) * (20.0 / -mvPosition.z);
        gl_Position = projectionMatrix * mvPosition;
      }
    `;

    const starFragmentShader = `
      uniform float uTime;
      varying float vRandom;
      
      void main() {
        // Render a perfect soft glowing circle natively
        vec2 uv = gl_PointCoord.xy - 0.5;
        float dist = length(uv);
        if (dist > 0.5) discard;
        
        // Soft dot glow profile
        float alpha = smoothstep(0.5, 0.1, dist);
        
        // Twinkle effect
        float twinkle = sin(uTime * 2.0 + vRandom * 100.0) * 0.5 + 0.5;
        
        // Mostly white, slight blue tint
        vec3 starColor = mix(vec3(0.8, 0.9, 1.0), vec3(1.0, 1.0, 1.0), vRandom);
        
        gl_FragColor = vec4(starColor, alpha * (0.3 + 0.7 * twinkle));
      }
    `;

    const starMat = new THREE.ShaderMaterial({
      vertexShader: starVertexShader,
      fragmentShader: starFragmentShader,
      uniforms,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    });

    const stars = new THREE.Points(starGeo, starMat);
    scene.add(stars);

    let targetX = 0;
    let targetY = 0;

    const onMouseMove = (e: MouseEvent) => {
      targetX = (e.clientX / window.innerWidth) * 2 - 1;
      targetY = -(e.clientY / window.innerHeight) * 2 + 1;
    };

    const onResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      uniforms.uResolution.value.set(window.innerWidth, window.innerHeight);
      renderer.setSize(window.innerWidth, window.innerHeight);
    };

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("resize", onResize);

    let aid = 0;
    const animate = () => {
      aid = requestAnimationFrame(animate);
      uniforms.uTime.value += 0.01;
      
      // Smoothly interpolate mouse for fluid parallax
      uniforms.uMouse.value.x += (targetX - uniforms.uMouse.value.x) * 0.06;
      uniforms.uMouse.value.y += (targetY - uniforms.uMouse.value.y) * 0.06;

      // Parallax effect: camera shifts slightly based on mouse
      camera.position.x += (targetX * 2.0 - camera.position.x) * 0.05;
      camera.position.y += (targetY * 1.5 - camera.position.y) * 0.05;
      camera.lookAt(0, 0, -60);

      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(aid);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("resize", onResize);
      auroraGeo.dispose();
      auroraMat.dispose();
      starGeo.dispose();
      starMat.dispose();
      renderer.dispose();
      if (container) container.innerHTML = "";
    };
  }, []);

  return <div ref={containerRef} className="three-bg" />;
}
