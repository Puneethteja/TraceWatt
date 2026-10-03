import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
export default function GridScene({ pulse = 0, conceptual = false, consumer = null }) {
  const host = useRef(null), trigger = useRef(-Infinity);
  const [fallback, setFallback] = useState(false);
  useEffect(() => { if (pulse > 0) trigger.current = performance.now(); }, [pulse]);
  useEffect(() => {
    const element = host.current; let renderer;
    try { renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true }); }
    // WebGL availability can only be established after the canvas mounts.
    // oxlint-disable-next-line react/set-state-in-effect
    catch { setFallback(true); return; }
    renderer.setPixelRatio(Math.min(devicePixelRatio, 1.6)); element.appendChild(renderer.domElement);
    const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera(38, 1, .1, 100);
    camera.position.set(10, 10, 13); camera.lookAt(0,0,0);
    scene.add(new THREE.HemisphereLight(0xe4fff0, 0x122c27, 3));
    const light = new THREE.DirectionalLight(0xffffff, 3); light.position.set(5,10,5); scene.add(light);
    const group = new THREE.Group(); scene.add(group);
    const grid = new THREE.GridHelper(20, 24, 0x30594d, 0x173d34); grid.position.y=-.15; group.add(grid);
    const positions = [[-5,0,0],[-2.6,0,0],[0,0,0],[2.8,0,-3],[2.8,0,0],[2.8,0,3],[5.2,0,0]];
    const material = new THREE.MeshStandardMaterial({ color:0x73c99b, metalness:.35, roughness:.4 });
    const detailMaterial = new THREE.MeshStandardMaterial({color:0x417d61,metalness:.45,roughness:.45});
    positions.forEach((p,i) => {
      const h = i===0 ? 2.8 : i===1 ? 1.6 : i===6 ? 2.1 : .8;
      const mesh = new THREE.Mesh(new THREE.BoxGeometry(i===1?1.3:.8,h,.8),material);
      mesh.position.set(p[0],h/2,p[2]); group.add(mesh);
      if(i===1) {
        for(let fin=0;fin<6;fin++) {
          const cooling=new THREE.Mesh(new THREE.BoxGeometry(.09,1.15,1.05),detailMaterial);
          cooling.position.set(p[0]-.5+fin*.2,.85,p[2]);group.add(cooling);
        }
        for(const x of [-.35,.35]) {
          const insulator=new THREE.Mesh(new THREE.CylinderGeometry(.12,.12,.45,8),detailMaterial);
          insulator.position.set(p[0]+x,1.82,p[2]);group.add(insulator);
        }
      }
      if(i>2&&i<6) {
        const roof=new THREE.Mesh(new THREE.ConeGeometry(.72,.48,4),detailMaterial);
        roof.rotation.y=Math.PI/4;roof.position.set(p[0],1.04,p[2]);group.add(roof);
      }
      if(i===6) {
        for(let row=0;row<4;row++) {
          const slot=new THREE.Mesh(new THREE.BoxGeometry(.57,.07,.03),detailMaterial);
          slot.position.set(p[0],.55+row*.35,p[2]+.42);group.add(slot);
        }
      }
      const base = new THREE.Mesh(new THREE.BoxGeometry(1.6,.13,1.6), new THREE.MeshStandardMaterial({color:0x214e3f}));
      base.position.set(...p); group.add(base);
      if(i>2 && i<6) {
        const meter = new THREE.Mesh(new THREE.BoxGeometry(.22,.3,.12),new THREE.MeshStandardMaterial({color:0xe9f6a0,emissive:0x657437}));
        meter.position.set(p[0],.7,p[2]+.46); group.add(meter);
      }
    });
    const edges=[[0,1],[1,2],[2,3],[2,4],[2,5],[4,6]];
    edges.forEach(([a,b])=>{
      const points=[new THREE.Vector3(positions[a][0],.18,positions[a][2]),new THREE.Vector3(positions[b][0],.18,positions[b][2])];
      group.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), new THREE.LineBasicMaterial({color:0x609781})));
    });
    const particle=new THREE.Mesh(new THREE.SphereGeometry(.13,10,8),new THREE.MeshBasicMaterial({color:0xe3ff9a})); group.add(particle);
    const path = [new THREE.Vector3(2.8,.7,3),new THREE.Vector3(2.8,.7,3.46),new THREE.Vector3(0,.3,0),new THREE.Vector3(5.2,1,0)];
    const resize = new ResizeObserver(()=>{ const w=element.clientWidth,h=element.clientHeight; renderer.setSize(w,h); camera.aspect=w/h; camera.updateProjectionMatrix(); }); resize.observe(element);
    const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
    let frame, visible=true, lastFrame=0;
    const observer=new IntersectionObserver(([entry])=>{visible=entry.isIntersecting;}); observer.observe(element);
    function animate(t) {
      frame=requestAnimationFrame(animate);
      if(document.hidden || !visible || t-lastFrame<33) return;
      lastFrame=t;
      group.rotation.y = reduced ? 0 : Math.sin(t*.00014)*.08;
      const active=conceptual || t-trigger.current<2600;
      particle.visible=active && !reduced;
      const progress=(conceptual?t%3600:(t-trigger.current))/2600%1;
      const segment=Math.min(2,Math.floor(progress*3));
      if(active) particle.position.lerpVectors(path[segment],path[segment+1],progress*3-segment);
      renderer.render(scene,camera);
    }
    frame=requestAnimationFrame(animate);
    return ()=>{cancelAnimationFrame(frame);resize.disconnect();observer.disconnect();scene.traverse(o=>{o.geometry?.dispose();if(o.material) o.material.dispose();});renderer.dispose();renderer.domElement.remove();};
  }, [conceptual]);
  return <div className="scene-wrap"><div className="scene" ref={host} role="img" aria-label="Conceptual 3D electricity network: grid, transformer, feeder, consumers and meters, connected to TraceWatt."/>{fallback&&<div className="scene-fallback">Grid → Transformer → Feeder → Meter → TraceWatt<br/>3D is unavailable on this device.</div>}<div className="scene-labels"><span>01 / GRID</span><span>02 / TRANSFORMER</span><span>03 / FEEDER</span><span>04 / METERS</span></div><div className="scene-caption"><span className="dot"/> {consumer ? `Selected consumer · ${consumer}` : 'Conceptual network · not a geographic map'}</div></div>;
}

