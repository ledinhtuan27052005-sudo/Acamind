'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import {
  Brain,
  MessageSquare,
  ArrowRight,
  BookOpen,
  ShieldCheck,
  Activity,
  Sparkles,
  GraduationCap,
  ChevronRight,
  Share2,
  Scale,
  Database,
  Heart,
  CheckCircle2,
  ArrowUpRight,
  FileText,
  Zap,
  Users,
} from 'lucide-react';
import { NeuralCard } from '@/components/ui/NeuralCard';
import { NeuralBadge } from '@/components/ui/NeuralBadge';
import { NeuralButton } from '@/components/ui/NeuralButton';

// ─── Animated Counter ───────────────────────────────────────────────
function AnimatedCounter({ target, suffix = '', duration = 1500 }: { target: number; suffix?: string; duration?: number }) {
  const [count, setCount] = useState(0);
  const elementRef = useRef<HTMLDivElement>(null);
  const [hasStarted, setHasStarted] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasStarted) {
          setHasStarted(true);
        }
      },
      { threshold: 0.1 }
    );

    if (elementRef.current) {
      observer.observe(elementRef.current);
    }

    return () => observer.disconnect();
  }, [hasStarted]);

  useEffect(() => {
    if (!hasStarted) return;
    let start = 0;
    const end = target;
    if (start === end) return;

    const totalMiliseconds = duration;
    const incrementTime = 30;
    const step = (end - start) / (totalMiliseconds / incrementTime);

    const timer = setInterval(() => {
      start += step;
      if (start >= end) {
        clearInterval(timer);
        setCount(end);
      } else {
        setCount(Math.floor(start));
      }
    }, incrementTime);

    return () => clearInterval(timer);
  }, [hasStarted, target, duration]);

  const formatNumber = (num: number) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(0) + 'k+';
    if (num % 1 !== 0) return num.toFixed(1);
    return num.toLocaleString('en-US');
  };

  return (
    <div ref={elementRef} className="font-bold text-3xl md:text-4xl text-neural-600 dark:text-neural-400">
      {formatNumber(count)}{suffix}
    </div>
  );
}

// ─── Brainwave Canvas ───────────────────────────────────────────────
function BrainwaveCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;
    let width = (canvas.width = canvas.offsetWidth || 500);
    let height = (canvas.height = canvas.offsetHeight || 300);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = canvas.offsetWidth || 500;
      height = canvas.height = canvas.offsetHeight || 300;
    };
    window.addEventListener('resize', handleResize);

    let phase = 0;
    const waves = [
      { amplitude: 35, frequency: 0.008, speed: 0.015, color: 'rgba(13, 148, 136, 0.45)' },
      { amplitude: 25, frequency: 0.014, speed: 0.025, color: 'rgba(139, 92, 246, 0.35)' },
      { amplitude: 20, frequency: 0.006, speed: 0.01, color: 'rgba(245, 158, 11, 0.35)' },
    ];

    const particles: Array<{ x: number; speed: number; waveIndex: number; size: number }> = [];
    for (let i = 0; i < 20; i++) {
      particles.push({
        x: Math.random() * width,
        speed: 0.3 + Math.random() * 1.0,
        waveIndex: Math.floor(Math.random() * waves.length),
        size: 1.2 + Math.random() * 2,
      });
    }

    const draw = () => {
      ctx.clearRect(0, 0, width, height);

      waves.forEach((wave, index) => {
        ctx.beginPath();
        ctx.lineWidth = index === 0 ? 2.5 : 1.2;

        const gradient = ctx.createLinearGradient(0, 0, width, 0);
        gradient.addColorStop(0, 'rgba(13, 148, 136, 0.05)');
        gradient.addColorStop(0.5, wave.color);
        gradient.addColorStop(1, 'rgba(139, 92, 246, 0.05)');
        ctx.strokeStyle = gradient;

        for (let x = 0; x < width; x += 5) {
          const y =
            height / 2 +
            Math.sin(x * wave.frequency + phase * wave.speed) * wave.amplitude *
            Math.sin(x * 0.002);
          if (x === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }
        ctx.stroke();
      });

      particles.forEach((p) => {
        const wave = waves[p.waveIndex];
        p.x += p.speed;
        if (p.x > width) p.x = 0;

        const y =
          height / 2 +
          Math.sin(p.x * wave.frequency + phase * wave.speed) * wave.amplitude *
          Math.sin(p.x * 0.002);

        ctx.beginPath();
        ctx.arc(p.x, y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = p.waveIndex === 0 ? '#0D9488' : p.waveIndex === 1 ? '#7C3AED' : '#F59E0B';
        ctx.shadowBlur = 8;
        ctx.shadowColor = ctx.fillStyle;
        ctx.fill();
        ctx.shadowBlur = 0;
      });

      phase += 0.4;
      animationId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationId);
    };
  }, []);

  return <canvas ref={canvasRef} className="w-full h-full block opacity-80" />;
}

// ─── Feature Data ───────────────────────────────────────────────────
const features = [
  {
    icon: <BookOpen className="w-6 h-6" />,
    title: 'Document Library',
    description: 'Upload bulk clinical PDFs and literature. AI auto-categorizes, extracts, and lists precise page citations.',
    href: '/library',
    color: '#0D9488',
  },
  {
    icon: <MessageSquare className="w-6 h-6" />,
    title: 'AI Psychology Q&A',
    description: 'Ask questions in natural language. AI answers with interactive annotations that take you straight to the source page.',
    href: '/chat',
    color: '#7C3AED',
  },
  {
    icon: <GraduationCap className="w-6 h-6" />,
    title: 'Revision Quiz',
    description: 'Automatically convert raw documents into multiple-choice questions and quick quizzes for clinical study.',
    href: '/quiz',
    color: '#F59E0B',
  },
  {
    icon: <Activity className="w-6 h-6" />,
    title: '3D Anatomy Atlas',
    description: 'Interactive 3D simulation of body and brain anatomy. Explore functional zones related to stress response.',
    href: '/3d',
    color: '#EC4899',
  },
  {
    icon: <Scale className="w-6 h-6" />,
    title: 'AI Critique',
    description: 'Analyze the validity of scientific arguments and contrast conflicting viewpoints across articles.',
    href: '/debate',
    color: '#06B6D4',
  },
  {
    icon: <Share2 className="w-6 h-6" />,
    title: 'Knowledge Graph',
    description: 'Visualize connection networks between authors and research topics in an interactive 3D graph.',
    href: '/graph',
    color: '#10B981',
  },
];

// ─── Main Landing Page ─────────────────────────────────────────────
export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-surface-base text-gray-900 dark:text-gray-100 transition-colors duration-500 overflow-x-hidden selection:bg-neural-500/20">

      {/* ─── Hero Section ───────────────────────────────────────────── */}
      <section className="relative min-h-[90vh] flex items-center overflow-hidden">
        {/* Background Gradient Orbs */}
        <div className="absolute top-1/4 left-1/4 w-[600px] h-[600px] rounded-full bg-neural-500/10 dark:bg-neural-500/5 blur-3xl animate-pulse" />
        <div className="absolute top-1/3 right-1/4 w-[500px] h-[500px] rounded-full bg-cortex-500/10 dark:bg-cortex-500/5 blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        <div className="absolute bottom-1/4 left-1/2 w-[400px] h-[400px] rounded-full bg-dopamine-500/10 blur-3xl animate-pulse" style={{ animationDelay: '2s' }} />

        <div className="container relative z-10 mx-auto px-4 md:px-8 max-w-6xl">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left: Text Content */}
            <div className="space-y-8 stagger-children">
              {/* Badge */}
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-neural-50 dark:bg-neural-900/30 border border-neural-200 dark:border-neural-800">
                <span className="w-2 h-2 rounded-full bg-neural-500 animate-pulse" />
                <span className="text-sm text-neural-700 dark:text-neural-300 font-medium">
                  AI Research Assistant
                </span>
              </div>

              {/* Headline */}
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-tight tracking-tight">
                <span className="text-gray-900 dark:text-white">
                  Research
                </span>
                <br />
                <span className="gradient-text-hero">
                  Psychology
                </span>
                <br />
                <span className="text-gray-600 dark:text-gray-300 text-3xl sm:text-4xl lg:text-5xl">
                  Smarter
                </span>
              </h1>

              {/* Subheadline */}
              <p className="text-lg text-gray-600 dark:text-gray-400 max-w-lg leading-relaxed">
                AI RAG platform for psychiatric literature research. Precise retrieval, clear citations, 80% time saved.
              </p>

              {/* CTA Buttons */}
              <div className="flex flex-wrap gap-4">
                <Link href="/chat" className="btn-neural inline-flex items-center gap-2 btn-cta-pulse">
                  <Sparkles className="w-5 h-5" />
                  Try for Free
                </Link>
                <Link href="#features" className="btn-neural-outline inline-flex items-center gap-2">
                  Explore Features
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>

              {/* Trust Badges */}
              <div className="flex flex-wrap items-center gap-6 pt-4 text-sm text-gray-500">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-neural-500" />
                  <span>Security & Privacy</span>
                </div>
                <div className="flex items-center gap-2">
                  <Activity className="w-5 h-5 text-neural-500" />
                  <span>Psychiatry Focused</span>
                </div>
              </div>
            </div>

            {/* Right: Brainwave Visualizer */}
            <div className="relative">
              <div className="aspect-square max-w-md mx-auto rounded-3xl bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl border border-white/50 dark:border-gray-800/50 shadow-2xl overflow-hidden">
                <div className="absolute inset-0 flex items-center justify-center p-6">
                  <BrainwaveCanvas />
                </div>
                {/* Status Badge */}
                <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between text-xs px-4 py-2 bg-white/60 dark:bg-gray-900/60 backdrop-blur rounded-xl border border-white/30 dark:border-gray-800/30">
                  <span className="flex items-center gap-2 font-medium text-gray-700 dark:text-gray-300">
                    <span className="w-2 h-2 rounded-full bg-neural-500 animate-ping" />
                    NEURAL MONITOR
                  </span>
                  <span className="text-gray-500">Status: Active</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Partner Logos ─────────────────────────────────────────── */}
      <section className="py-10 border-y border-gray-200/50 dark:border-gray-800/50 bg-white/50 dark:bg-gray-900/30 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-4">
          <p className="text-center text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-widest mb-6">
            Partnered with Research Centers
          </p>
          <div className="relative w-full overflow-hidden mask-gradient-x">
            <div className="scroll-carousel flex gap-8 py-2">
              {[...Array(2)].map((_, listIdx) => (
                <div key={listIdx} className="flex gap-8 items-center shrink-0">
                  {[
                    { icon: <GraduationCap className="w-5 h-5" />, label: 'NIMH Vietnam' },
                    { icon: <Brain className="w-5 h-5" />, label: 'Stanford Lab' },
                    { icon: <GraduationCap className="w-5 h-5" />, label: 'Harvard Medical' },
                    { icon: <Heart className="w-5 h-5" />, label: 'WHO Mental Health' },
                    { icon: <Users className="w-5 h-5" />, label: 'Bach Mai Hospital' },
                  ].map((partner, i) => (
                    <div key={i} className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gray-100/50 dark:bg-gray-800/50 border border-gray-200/50 dark:border-gray-700/50">
                      <span className="text-neural-500">{partner.icon}</span>
                      <span className="text-sm font-medium text-gray-600 dark:text-gray-400 whitespace-nowrap">{partner.label}</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ─── Features Grid ────────────────────────────────────────── */}
      <section id="features" className="py-20 md:py-28">
        <div className="max-w-6xl mx-auto px-4">
          {/* Section Header */}
          <div className="text-center mb-16 space-y-4">
            <NeuralBadge variant="neural" dot pulse>
              Features
            </NeuralBadge>
            <h2 className="text-3xl md:text-4xl font-extrabold text-gray-900 dark:text-white">
              Advanced Research Suite
            </h2>
            <p className="text-gray-600 dark:text-gray-400 max-w-2xl mx-auto text-lg">
              Acquire the complete academic AI tools, custom-designed for mental health science.
            </p>
          </div>

          {/* Features Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 stagger-children">
            {features.map((feature, index) => (
              <Link key={index} href={feature.href}>
                <NeuralCard
                  variant="elevated"
                  padding="lg"
                  className="h-full group"
                >
                  {/* Icon */}
                  <div
                    className="w-14 h-14 rounded-2xl flex items-center justify-center mb-5 transition-transform duration-300 group-hover:scale-110"
                    style={{
                      background: `linear-gradient(135deg, ${feature.color}20, ${feature.color}10)`,
                    }}
                  >
                    <div style={{ color: feature.color }}>{feature.icon}</div>
                  </div>

                  {/* Title */}
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2 group-hover:text-neural-600 dark:group-hover:text-neural-400 transition-colors">
                    {feature.title}
                  </h3>

                  {/* Description */}
                  <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                    {feature.description}
                  </p>

                  {/* Arrow Link */}
                  <div className="flex items-center gap-1 mt-4 text-sm font-semibold transition-colors group-hover:gap-2" style={{ color: feature.color }}>
                    <span>Explore</span>
                    <ChevronRight className="w-4 h-4" />
                  </div>
                </NeuralCard>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Stats Section ─────────────────────────────────────────── */}
      <section className="py-20 md:py-28 bg-white/50 dark:bg-gray-900/30">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 md:gap-8">
            {[
              { target: 2540000, suffix: '+', label: 'Academic Documents' },
              { target: 12800, suffix: '+', label: 'Active Researchers' },
              { target: 98.4, suffix: '%', label: 'RAGAS Score' },
              { target: 120, suffix: '+', label: 'Partner Institutions' },
            ].map((stat, i) => (
              <div key={i} className="stat-card">
                <AnimatedCounter target={stat.target} suffix={stat.suffix} />
                <p className="text-sm text-gray-500 dark:text-gray-400 uppercase tracking-wider mt-2">
                  {stat.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA Section ──────────────────────────────────────────── */}
      <section className="py-20 md:py-28">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <div className="relative p-8 md:p-12 rounded-3xl bg-gradient-to-br from-neural-500/10 to-cortex-500/10 dark:from-neural-900/20 dark:to-cortex-900/20 border border-neural-200/30 dark:border-neural-800/30 overflow-hidden">
            {/* Background Orbs */}
            <div className="absolute top-0 right-0 w-64 h-64 rounded-full bg-neural-500/20 blur-3xl" />
            <div className="absolute bottom-0 left-0 w-48 h-48 rounded-full bg-cortex-500/20 blur-3xl" />

            <div className="relative z-10 space-y-6">
              <Brain className="w-12 h-12 mx-auto text-neural-500" />
              <h2 className="text-2xl md:text-3xl font-extrabold text-gray-900 dark:text-white">
                Ready to elevate your research?
              </h2>
              <p className="text-gray-600 dark:text-gray-400 max-w-lg mx-auto">
                Join thousands of researchers using Acamind to save time and enhance the quality of scientific work.
              </p>
              <div className="flex flex-wrap justify-center gap-4">
                <Link href="/register" className="btn-neural inline-flex items-center gap-2 btn-cta-pulse">
                  <Sparkles className="w-5 h-5" />
                  Start Free
                </Link>
                <Link href="/chat" className="btn-neural-outline inline-flex items-center gap-2">
                  Try Now
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Footer ─────────────────────────────────────────────── */}
      <footer className="bg-white/80 dark:bg-gray-900/50 border-t border-gray-200/50 dark:border-gray-800/50 py-12">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            {/* Brand */}
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <div className="relative w-8 h-8 rounded-lg overflow-hidden border border-neural-500/20">
                  <Image src="/Logo.jpeg" alt="Acamind Logo" fill className="object-cover" sizes="32px" />
                </div>
                <span className="font-bold text-lg text-gray-900 dark:text-white">ACAMIND</span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                AI platform supporting mental health literature research.
              </p>
            </div>

            {/* Links */}
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Application</h4>
              <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                <li><Link href="/library" className="hover:text-neural-600 transition-colors">PDF Library</Link></li>
                <li><Link href="/chat" className="hover:text-neural-600 transition-colors">AI Q&A</Link></li>
                <li><Link href="/3d" className="hover:text-neural-600 transition-colors">3D Atlas</Link></li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Research</h4>
              <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                <li><Link href="/graph" className="hover:text-neural-600 transition-colors">Knowledge Graph</Link></li>
                <li><Link href="/trends" className="hover:text-neural-600 transition-colors">Trending</Link></li>
                <li><Link href="/debate" className="hover:text-neural-600 transition-colors">AI Critique</Link></li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Contact</h4>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                contact@acamind.ai<br />
                Mental Health & AI Research Institute
              </p>
            </div>
          </div>

          <div className="pt-8 border-t border-gray-200/50 dark:border-gray-800/50 flex flex-col sm:flex-row items-center justify-between text-sm text-gray-500 dark:text-gray-400">
            <p>&copy; {new Date().getFullYear()} ACAMIND. All rights reserved.</p>
            <div className="flex gap-4 mt-4 sm:mt-0">
              <a href="#" className="hover:text-neural-600 transition-colors">Terms</a>
              <a href="#" className="hover:text-neural-600 transition-colors">Privacy</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
