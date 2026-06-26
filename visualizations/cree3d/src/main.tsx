import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Activity, BarChart3, Box, Eye, EyeOff, Gauge, RotateCcw } from 'lucide-react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import './styles.css';

type MetricPoint = {
  step: number;
  done_frac: number | null;
  reward_mean: number | null;
  target_cree_char_f1: number | null;
  target_english_char_f1: number | null;
  target_cree_orthography: number | null;
  target_english_orthography: number | null;
  target_cree_exact: number | null;
  target_cree_containment: number | null;
  entropy: number | null;
  kl_v1: number | null;
  kl_v2: number | null;
  loss_sum: number | null;
  tokens_per_sec: number | null;
  samples_per_sec: number | null;
  step_time: number | null;
  expert_token_utilization: number | null;
};

type MetricsPayload = {
  run: {
    name: string;
    id: string;
    url: string;
    planned_steps: number;
  };
  summary: {
    rows: number;
    latest_step: number;
    latest_done_frac: number;
    latest_reward_mean: number;
    latest_entropy: number;
    run_url: string;
  };
  points: MetricPoint[];
};

type MetricDefinition = {
  key: keyof MetricPoint;
  label: string;
  group: 'Reward' | 'Cree' | 'Policy' | 'System';
  color: number;
  description: string;
};

const METRICS: MetricDefinition[] = [
  {
    key: 'reward_mean',
    label: 'Reward mean',
    group: 'Reward',
    color: 0x4f46e5,
    description: 'Average verifier reward for sampled completions.',
  },
  {
    key: 'target_cree_char_f1',
    label: 'Cree char F1',
    group: 'Cree',
    color: 0x0891b2,
    description: 'Spelling-level overlap when the target answer is Cree.',
  },
  {
    key: 'target_cree_orthography',
    label: 'Cree orthography',
    group: 'Cree',
    color: 0x16a34a,
    description: 'Preservation of Cree marks, hyphens, and apostrophes.',
  },
  {
    key: 'target_cree_exact',
    label: 'Cree exact',
    group: 'Cree',
    color: 0xdc2626,
    description: 'Strict exact match for English-to-Cree lookup prompts.',
  },
  {
    key: 'target_english_char_f1',
    label: 'English char F1',
    group: 'Cree',
    color: 0x0f766e,
    description: 'Spelling-level overlap when translating Cree forms to English glosses.',
  },
  {
    key: 'entropy',
    label: 'Entropy',
    group: 'Policy',
    color: 0x9333ea,
    description: 'Policy uncertainty. Falling values mean the model is becoming more decisive.',
  },
  {
    key: 'kl_v1',
    label: 'KL v1',
    group: 'Policy',
    color: 0xf97316,
    description: 'One sampled KL estimate tracking policy drift.',
  },
  {
    key: 'expert_token_utilization',
    label: 'Expert tokens',
    group: 'System',
    color: 0x64748b,
    description: 'Fraction of expert-parallel token slots carrying real sampled tokens.',
  },
  {
    key: 'samples_per_sec',
    label: 'Samples/sec',
    group: 'System',
    color: 0xca8a04,
    description: 'Sampling throughput. Useful for run ETA, not model quality.',
  },
];

const DEFAULT_VISIBLE = new Set<keyof MetricPoint>([
  'reward_mean',
  'target_cree_char_f1',
  'target_cree_orthography',
  'target_english_char_f1',
  'entropy',
  'kl_v1',
]);

function normalize(values: Array<number | null>): number[] {
  const finite = values.filter((value): value is number => typeof value === 'number' && Number.isFinite(value));
  if (!finite.length) return values.map(() => 0);
  const min = Math.min(...finite);
  const max = Math.max(...finite);
  const span = max - min || 1;
  return values.map((value) => {
    if (typeof value !== 'number' || !Number.isFinite(value)) return 0;
    return (value - min) / span;
  });
}

function formatValue(value: number | null | undefined): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return 'n/a';
  if (Math.abs(value) >= 100) return value.toFixed(1);
  return value.toFixed(4);
}

function formatPercent(value: number | null | undefined): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return 'n/a';
  return `${(value * 100).toFixed(1)}%`;
}

function ThreeScene({ payload, visible }: { payload: MetricsPayload; visible: Set<keyof MetricPoint> }) {
  const mountRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, preserveDrawingBuffer: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0xf8fafc, 1);
    mount.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.fog = new THREE.Fog(0xf8fafc, 18, 52);

    const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
    camera.position.set(10, 9, 16);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.target.set(0, 2.2, 0);
    controls.maxDistance = 38;
    controls.minDistance = 8;

    scene.add(new THREE.AmbientLight(0xffffff, 1.5));
    const keyLight = new THREE.DirectionalLight(0xffffff, 2.2);
    keyLight.position.set(8, 12, 8);
    scene.add(keyLight);

    const axis = new THREE.Group();
    const grid = new THREE.GridHelper(22, 22, 0x94a3b8, 0xd7dee8);
    grid.position.y = -0.05;
    axis.add(grid);

    const xAxis = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(-10, 0, -5), new THREE.Vector3(10, 0, -5)]),
      new THREE.LineBasicMaterial({ color: 0x334155 }),
    );
    axis.add(xAxis);
    scene.add(axis);

    const dataGroup = new THREE.Group();
    scene.add(dataGroup);

    const points = payload.points;
    const maxStep = Math.max(1, payload.run.planned_steps || points.at(-1)?.step || 800);
    const selectedMetrics = METRICS.filter((metric) => visible.has(metric.key));
    const laneSpan = Math.max(1, selectedMetrics.length - 1);

    selectedMetrics.forEach((metric, metricIndex) => {
      const values = normalize(points.map((point) => point[metric.key] as number | null));
      const laneZ = -4.5 + (metricIndex / laneSpan) * 9;
      const vertices: number[] = [];
      const colors: number[] = [];
      const color = new THREE.Color(metric.color);

      points.forEach((point, index) => {
        const x = (point.step / maxStep) * 20 - 10;
        const y = values[index] * 6;
        vertices.push(x, y, laneZ);
        colors.push(color.r, color.g, color.b);
      });

      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
      geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
      const material = new THREE.LineBasicMaterial({ vertexColors: true, linewidth: 2 });
      const line = new THREE.Line(geometry, material);
      dataGroup.add(line);

      const pointGeometry = new THREE.BufferGeometry();
      const sampled: number[] = [];
      for (let pointIndex = 0; pointIndex < points.length; pointIndex += 8) {
        sampled.push(vertices[pointIndex * 3], vertices[pointIndex * 3 + 1], vertices[pointIndex * 3 + 2]);
      }
      pointGeometry.setAttribute('position', new THREE.Float32BufferAttribute(sampled, 3));
      const pointMaterial = new THREE.PointsMaterial({ color: metric.color, size: 0.08, transparent: true, opacity: 0.72 });
      dataGroup.add(new THREE.Points(pointGeometry, pointMaterial));
    });

    const cursorGeometry = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(-10, -0.02, -5.2),
      new THREE.Vector3(-10, 6.4, 5.2),
    ]);
    const cursor = new THREE.Line(cursorGeometry, new THREE.LineBasicMaterial({ color: 0x111827, transparent: true, opacity: 0.35 }));
    scene.add(cursor);

    let frame = 0;

    const resize = () => {
      const width = mount.clientWidth;
      const height = mount.clientHeight;
      camera.aspect = width / Math.max(height, 1);
      camera.updateProjectionMatrix();
      renderer.setSize(width, height, false);
    };
    resize();
    window.addEventListener('resize', resize);

    let animationId = 0;
    const animate = () => {
      frame += 1;
      const latestStep = points.at(-1)?.step ?? 0;
      const cursorX = (latestStep / maxStep) * 20 - 10;
      cursor.position.x = cursorX + Math.sin(frame * 0.02) * 0.04;
      dataGroup.rotation.y = Math.sin(frame * 0.002) * 0.025;
      controls.update();
      renderer.render(scene, camera);
      animationId = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener('resize', resize);
      controls.dispose();
      renderer.dispose();
      mount.removeChild(renderer.domElement);
    };
  }, [payload, visible]);

  return <div className="scene" ref={mountRef} aria-label="3D metric ribbons" />;
}

function App() {
  const [payload, setPayload] = useState<MetricsPayload | null>(null);
  const [visible, setVisible] = useState<Set<keyof MetricPoint>>(DEFAULT_VISIBLE);

  useEffect(() => {
    fetch('./cree_metrics.json')
      .then((response) => {
        if (!response.ok) throw new Error(`Failed to load metrics: ${response.status}`);
        return response.json() as Promise<MetricsPayload>;
      })
      .then(setPayload)
      .catch((error) => {
        console.error(error);
      });
  }, []);

  const latest = payload?.points.at(-1);
  const visibleMetrics = useMemo(() => METRICS.filter((metric) => visible.has(metric.key)), [visible]);

  const toggle = (key: keyof MetricPoint) => {
    setVisible((current) => {
      const next = new Set(current);
      if (next.has(key)) {
        if (next.size > 1) next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  const reset = () => setVisible(new Set(DEFAULT_VISIBLE));

  if (!payload) {
    return (
      <main className="loading">
        <Activity aria-hidden="true" />
        <span>Loading Cree1865 metrics</span>
      </main>
    );
  }

  return (
    <main className="app">
      <ThreeScene payload={payload} visible={visible} />
      <aside className="panel left">
        <div className="run-title">
          <Box aria-hidden="true" />
          <div>
            <h1>Cree1865 3D Metrics</h1>
            <a href={payload.run.url} target="_blank" rel="noreferrer">
              W&B run {payload.run.id}
            </a>
          </div>
        </div>
        <div className="stats-grid">
          <div>
            <span>Step</span>
            <strong>{latest?.step ?? 0} / {payload.run.planned_steps}</strong>
          </div>
          <div>
            <span>Done</span>
            <strong>{formatPercent(latest?.done_frac)}</strong>
          </div>
          <div>
            <span>Reward</span>
            <strong>{formatValue(latest?.reward_mean)}</strong>
          </div>
          <div>
            <span>Entropy</span>
            <strong>{formatValue(latest?.entropy)}</strong>
          </div>
        </div>
        <p className="note">
          Each ribbon is one metric over training step. Height is normalized per metric, so this view shows shape and
          timing, not shared units.
        </p>
      </aside>

      <aside className="panel right">
        <div className="section-heading">
          <BarChart3 aria-hidden="true" />
          <h2>Metric Ribbons</h2>
          <button className="icon-button" type="button" onClick={reset} title="Reset visible metrics">
            <RotateCcw aria-hidden="true" />
          </button>
        </div>
        <div className="toggles">
          {METRICS.map((metric) => {
            const active = visible.has(metric.key);
            return (
              <button
                key={metric.key}
                className={`toggle ${active ? 'active' : ''}`}
                type="button"
                onClick={() => toggle(metric.key)}
                title={metric.description}
              >
                <span className="swatch" style={{ backgroundColor: `#${metric.color.toString(16).padStart(6, '0')}` }} />
                <span>{metric.label}</span>
                {active ? <Eye aria-hidden="true" /> : <EyeOff aria-hidden="true" />}
              </button>
            );
          })}
        </div>
        <div className="selected">
          <Gauge aria-hidden="true" />
          <span>{visibleMetrics.length} active metrics</span>
        </div>
      </aside>
    </main>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
