/*
 * Digital CMO AI Landing Page
 * Design: "Editorial Noir" — Dark luxury tech
 * - Deep charcoal canvas (#0A0A0F) with electric cyan (#00D4FF) accents
 * - Space Grotesk display + JetBrains Mono for numerals
 * - Asymmetric layouts, glow effects, dot-grid textures
 */

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Brain,
  BarChart3,
  Palette,
  Users,
  LineChart,
  Plug,
  ArrowRight,
  Check,
  Zap,
  Shield,
  ChevronRight,
  Star,
  Menu,
  X,
} from "lucide-react";
import { motion, useInView, useScroll, useTransform } from "framer-motion";

// CDN image URLs
const HERO_BG = "https://d2xsxph8kpxj0f.cloudfront.net/97052298/ec3jmLUYBGBWUTx254TNQT/hero-bg-bxHYJzE9A64MpaJKsDgDp2.webp";
const BRAIN_IMG = "https://d2xsxph8kpxj0f.cloudfront.net/97052298/ec3jmLUYBGBWUTx254TNQT/brain-module-XDHzf32V9MFX3xW8ZhXbov.webp";
const ANALYTICS_IMG = "https://d2xsxph8kpxj0f.cloudfront.net/97052298/ec3jmLUYBGBWUTx254TNQT/analytics-dashboard-Ebgw9FBifpX9t3uHvKmsB9.webp";
const INTEGRATIONS_IMG = "https://d2xsxph8kpxj0f.cloudfront.net/97052298/ec3jmLUYBGBWUTx254TNQT/integrations-grid-7BgCP7XJHLq6tEnRC9SQLL.webp";
const CREATIVE_IMG = "https://d2xsxph8kpxj0f.cloudfront.net/97052298/ec3jmLUYBGBWUTx254TNQT/creative-module-HsvzvzEg9ZiG9nvibFP3js.webp";

/* ─── Animated counter hook ─── */
function useCounter(end: number, duration = 2000, startOnView = true) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true });

  useEffect(() => {
    if (!startOnView || !inView) return;
    let start = 0;
    const step = end / (duration / 16);
    const timer = setInterval(() => {
      start += step;
      if (start >= end) {
        setCount(end);
        clearInterval(timer);
      } else {
        setCount(Math.floor(start));
      }
    }, 16);
    return () => clearInterval(timer);
  }, [end, duration, inView, startOnView]);

  return { count, ref };
}

/* ─── Fade-up animation wrapper ─── */
function FadeUp({ children, delay = 0, className = "" }: { children: React.ReactNode; delay?: number; className?: string }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 24 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

/* ─── Navigation ─── */
function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", handler, { passive: true });
    return () => window.removeEventListener("scroll", handler);
  }, []);

  const links = [
    { label: "Features", href: "#features" },
    { label: "How It Works", href: "#how-it-works" },
    { label: "Pricing", href: "#pricing" },
  ];

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled ? "bg-background/80 backdrop-blur-xl border-b border-border/50" : "bg-transparent"
      }`}
    >
      <div className="container flex items-center justify-between h-16 lg:h-20">
        <a href="#" className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center glow-cyan">
            <Brain className="w-4.5 h-4.5 text-primary" />
          </div>
          <span className="font-bold text-lg tracking-tight text-foreground">
            Digital CMO<span className="text-primary">.ai</span>
          </span>
        </a>

        <div className="hidden md:flex items-center gap-8">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              {l.label}
            </a>
          ))}
        </div>

        <div className="hidden md:flex items-center gap-3">
          <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
            Log in
          </Button>
          <Button size="sm" className="bg-primary text-primary-foreground hover:bg-primary/90 glow-cyan">
            Start Free Trial
            <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
          </Button>
        </div>

        <button className="md:hidden text-foreground" onClick={() => setMobileOpen(!mobileOpen)}>
          {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {mobileOpen && (
        <div className="md:hidden bg-background/95 backdrop-blur-xl border-b border-border/50 px-4 pb-4">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="block py-2.5 text-sm text-muted-foreground hover:text-foreground"
              onClick={() => setMobileOpen(false)}
            >
              {l.label}
            </a>
          ))}
          <Button size="sm" className="w-full mt-3 bg-primary text-primary-foreground">
            Start Free Trial
          </Button>
        </div>
      )}
    </nav>
  );
}

/* ─── Hero Section ─── */
function HeroSection() {
  const { scrollY } = useScroll();
  const bgY = useTransform(scrollY, [0, 600], [0, 150]);

  const metrics = [
    { value: 10, suffix: "x", label: "Faster Campaign Launch" },
    { value: 85, suffix: "%", label: "Cost Reduction" },
    { value: 3, suffix: "M+", label: "Campaigns Optimized" },
  ];

  return (
    <section className="relative min-h-screen flex items-center overflow-hidden pt-20">
      {/* Background */}
      <motion.div className="absolute inset-0 z-0" style={{ y: bgY }}>
        <img
          src={HERO_BG}
          alt=""
          className="w-full h-full object-cover opacity-40"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-background/30 via-background/60 to-background" />
      </motion.div>

      {/* Dot grid overlay */}
      <div className="absolute inset-0 dot-grid opacity-40 z-[1]" />

      <div className="container relative z-10 py-20 lg:py-32">
        <div className="grid lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          {/* Left: Copy */}
          <div className="lg:col-span-7">
            <FadeUp>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-primary/30 bg-primary/5 mb-6">
                <Zap className="w-3.5 h-3.5 text-primary" />
                <span className="text-xs font-medium text-primary tracking-wide uppercase">
                  AI-Powered Marketing
                </span>
              </div>
            </FadeUp>

            <FadeUp delay={0.1}>
              <h1 className="text-4xl sm:text-5xl lg:text-6xl xl:text-7xl font-bold tracking-tight leading-[1.08] mb-6">
                Your entire{" "}
                <span className="text-primary text-glow">marketing team</span>
                <br />
                in one AI system
              </h1>
            </FadeUp>

            <FadeUp delay={0.2}>
              <p className="text-lg lg:text-xl text-muted-foreground max-w-xl mb-8 leading-relaxed">
                Digital CMO AI plans, executes, and analyses marketing campaigns
                with the strategic depth of a seasoned CMO and the speed of
                automation. From market research to creative generation to
                real-time analytics.
              </p>
            </FadeUp>

            <FadeUp delay={0.3}>
              <div className="flex flex-wrap gap-3 mb-12">
                <Button
                  size="lg"
                  className="bg-primary text-primary-foreground hover:bg-primary/90 glow-cyan text-base px-6 h-12"
                >
                  Start Free Trial
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
                <Button
                  variant="outline"
                  size="lg"
                  className="border-border/60 text-foreground hover:bg-secondary h-12 px-6 text-base"
                >
                  Watch Demo
                </Button>
              </div>
            </FadeUp>

            <FadeUp delay={0.4}>
              <div className="flex flex-wrap gap-8 lg:gap-12">
                {metrics.map((m, i) => {
                  const { count, ref } = useCounter(m.value, 1800);
                  return (
                    <div key={i}>
                      <span
                        ref={ref}
                        className="text-3xl lg:text-4xl font-bold text-foreground"
                        style={{ fontFamily: "var(--font-mono)" }}
                      >
                        {count}
                        {m.suffix}
                      </span>
                      <p className="text-sm text-muted-foreground mt-1">
                        {m.label}
                      </p>
                    </div>
                  );
                })}
              </div>
            </FadeUp>
          </div>

          {/* Right: Dashboard preview */}
          <div className="lg:col-span-5">
            <FadeUp delay={0.3}>
              <div className="relative">
                <div className="rounded-xl overflow-hidden border border-border/40 glow-cyan-strong">
                  <img
                    src={ANALYTICS_IMG}
                    alt="Digital CMO AI Dashboard"
                    className="w-full h-auto"
                  />
                </div>
                {/* Floating badge */}
                <div className="absolute -bottom-4 -left-4 bg-card border border-border/50 rounded-lg px-4 py-3 glow-cyan">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="text-xs font-medium text-foreground">
                      AI Agent Active
                    </span>
                  </div>
                </div>
              </div>
            </FadeUp>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ─── Trusted By / Social Proof ─── */
function SocialProof() {
  const logos = [
    "TechCrunch", "Forbes", "Wired", "Product Hunt", "Y Combinator"
  ];
  return (
    <section className="relative py-16 border-y border-border/30">
      <div className="container">
        <FadeUp>
          <p className="text-center text-xs uppercase tracking-[0.2em] text-muted-foreground mb-8">
            Trusted by forward-thinking marketing teams
          </p>
        </FadeUp>
        <FadeUp delay={0.1}>
          <div className="flex flex-wrap justify-center items-center gap-8 lg:gap-16">
            {logos.map((name) => (
              <span
                key={name}
                className="text-lg font-semibold text-muted-foreground/40 hover:text-muted-foreground/60 transition-colors"
                style={{ fontFamily: "var(--font-display)" }}
              >
                {name}
              </span>
            ))}
          </div>
        </FadeUp>
      </div>
    </section>
  );
}

/* ─── Features Section ─── */
function FeaturesSection() {
  const features = [
    {
      icon: Brain,
      title: "Brain & Memory",
      description:
        "Intelligent orchestrator with 4-layer memory system. Learns your brand, remembers context, and gets smarter with every interaction.",
      image: BRAIN_IMG,
      color: "text-cyan-400",
    },
    {
      icon: BarChart3,
      title: "Business Analysis",
      description:
        "SWOT, PESTEL, competitor analysis, and buyer persona generation. Deep market intelligence powered by real-time data.",
      image: null,
      color: "text-emerald-400",
    },
    {
      icon: Palette,
      title: "Creative & Design",
      description:
        "Generate marketing copy, image prompts, A/B test variants, and full content calendars. Your creative department, automated.",
      image: CREATIVE_IMG,
      color: "text-rose-400",
    },
    {
      icon: Users,
      title: "CRM & Campaigns",
      description:
        "Lead management, multi-channel campaigns, automated workflows, and GDPR-compliant contact handling. All in one place.",
      image: null,
      color: "text-amber-400",
    },
    {
      icon: LineChart,
      title: "Analytics & Reporting",
      description:
        "13 KPI dashboard, revenue forecasting, A/B experiment tracking with statistical significance. Data-driven decisions, instantly.",
      image: ANALYTICS_IMG,
      color: "text-violet-400",
    },
    {
      icon: Plug,
      title: "Integrations",
      description:
        "HubSpot, SendGrid, Google Ads, Google Analytics, LinkedIn, and more. Connect your entire marketing stack seamlessly.",
      image: INTEGRATIONS_IMG,
      color: "text-sky-400",
    },
  ];

  return (
    <section id="features" className="relative py-24 lg:py-32">
      <div className="absolute inset-0 dot-grid opacity-20" />
      <div className="container relative">
        <FadeUp>
          <div className="max-w-2xl mb-16">
            <p className="text-sm font-medium text-primary tracking-wide uppercase mb-3">
              Capabilities
            </p>
            <h2 className="text-3xl lg:text-5xl font-bold tracking-tight mb-4">
              Six modules.{" "}
              <span className="text-muted-foreground">One intelligence.</span>
            </h2>
            <p className="text-lg text-muted-foreground leading-relaxed">
              Every module works independently or in concert, orchestrated by the
              Brain to deliver cohesive marketing strategies.
            </p>
          </div>
        </FadeUp>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((f, i) => (
            <FadeUp key={f.title} delay={i * 0.08}>
              <div className="group relative h-full rounded-xl border border-border/40 bg-card/50 backdrop-blur-sm overflow-hidden transition-all duration-300 hover:border-primary/30 hover:glow-cyan gradient-border">
                {f.image && (
                  <div className="h-40 overflow-hidden">
                    <img
                      src={f.image}
                      alt={f.title}
                      className="w-full h-full object-cover opacity-60 group-hover:opacity-80 transition-opacity duration-500 group-hover:scale-105 transition-transform"
                    />
                    <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-card/95" />
                  </div>
                )}
                <div className={`p-6 ${f.image ? "" : "pt-8"}`}>
                  <div
                    className={`w-10 h-10 rounded-lg bg-secondary flex items-center justify-center mb-4 ${f.color}`}
                  >
                    <f.icon className="w-5 h-5" />
                  </div>
                  <h3 className="text-lg font-semibold text-foreground mb-2">
                    {f.title}
                  </h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {f.description}
                  </p>
                </div>
              </div>
            </FadeUp>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── How It Works ─── */
function HowItWorks() {
  const steps = [
    {
      num: "01",
      title: "Connect Your Stack",
      desc: "Link your CRM, ad platforms, analytics, and email tools. Digital CMO AI integrates with your existing workflow in minutes.",
    },
    {
      num: "02",
      title: "Define Your Goals",
      desc: "Set business objectives, target audiences, and brand guidelines. The Brain learns your context and builds a strategic foundation.",
    },
    {
      num: "03",
      title: "Let AI Execute",
      desc: "From market analysis to campaign creation to performance optimization — the AI handles execution while you maintain strategic control.",
    },
    {
      num: "04",
      title: "Measure & Iterate",
      desc: "Real-time dashboards, automated A/B testing, and predictive analytics ensure continuous improvement across all channels.",
    },
  ];

  return (
    <section id="how-it-works" className="relative py-24 lg:py-32 bg-card/30">
      <div className="container">
        <FadeUp>
          <div className="text-center max-w-2xl mx-auto mb-16">
            <p className="text-sm font-medium text-primary tracking-wide uppercase mb-3">
              How It Works
            </p>
            <h2 className="text-3xl lg:text-5xl font-bold tracking-tight mb-4">
              From zero to campaign{" "}
              <span className="text-muted-foreground">in four steps</span>
            </h2>
          </div>
        </FadeUp>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((s, i) => (
            <FadeUp key={s.num} delay={i * 0.1}>
              <div className="relative p-6 rounded-xl border border-border/30 bg-background/50 h-full">
                <span
                  className="text-5xl font-bold text-primary/10 absolute top-4 right-5"
                  style={{ fontFamily: "var(--font-mono)" }}
                >
                  {s.num}
                </span>
                <div className="relative">
                  <div className="w-8 h-8 rounded-full bg-primary/10 border border-primary/30 flex items-center justify-center mb-5">
                    <span
                      className="text-xs font-bold text-primary"
                      style={{ fontFamily: "var(--font-mono)" }}
                    >
                      {s.num}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold text-foreground mb-2">
                    {s.title}
                  </h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {s.desc}
                  </p>
                </div>
              </div>
            </FadeUp>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── Pricing Section ─── */
function PricingSection() {
  const [annual, setAnnual] = useState(true);

  const plans = [
    {
      name: "Starter",
      desc: "For solo marketers and small teams getting started with AI-powered marketing.",
      monthlyPrice: 49,
      annualPrice: 39,
      tokens: "10,000",
      highlight: false,
      features: [
        "10,000 AI tokens / month",
        "Brain & Memory (basic)",
        "Business Analysis module",
        "Creative generation (limited)",
        "Email support",
        "1 integration",
        "Basic analytics dashboard",
      ],
    },
    {
      name: "Pro",
      desc: "For growing teams that need the full power of AI-driven marketing.",
      monthlyPrice: 149,
      annualPrice: 119,
      tokens: "100,000",
      highlight: true,
      features: [
        "100,000 AI tokens / month",
        "Full Brain & Memory system",
        "All 6 modules included",
        "Unlimited creative generation",
        "Priority support",
        "5 integrations",
        "Advanced analytics + forecasting",
        "A/B experiment tracking",
        "Custom brand guidelines",
      ],
    },
    {
      name: "Enterprise",
      desc: "For organizations that need unlimited scale, custom models, and dedicated support.",
      monthlyPrice: null,
      annualPrice: null,
      tokens: "1,000,000+",
      highlight: false,
      features: [
        "1,000,000+ AI tokens / month",
        "Custom LLM fine-tuning",
        "All modules + custom modules",
        "Unlimited integrations",
        "Dedicated account manager",
        "SSO & advanced security",
        "Custom API access",
        "SLA guarantee",
        "On-premise deployment option",
      ],
    },
  ];

  return (
    <section id="pricing" className="relative py-24 lg:py-32">
      <div className="absolute inset-0 dot-grid opacity-15" />
      <div className="container relative">
        <FadeUp>
          <div className="text-center max-w-2xl mx-auto mb-12">
            <p className="text-sm font-medium text-primary tracking-wide uppercase mb-3">
              Pricing
            </p>
            <h2 className="text-3xl lg:text-5xl font-bold tracking-tight mb-4">
              Token-based pricing.{" "}
              <span className="text-muted-foreground">Pay for what you use.</span>
            </h2>
            <p className="text-lg text-muted-foreground">
              Every AI interaction consumes tokens. Choose the tier that matches
              your marketing volume.
            </p>
          </div>
        </FadeUp>

        {/* Toggle */}
        <FadeUp delay={0.1}>
          <div className="flex items-center justify-center gap-3 mb-12">
            <span
              className={`text-sm ${!annual ? "text-foreground" : "text-muted-foreground"}`}
            >
              Monthly
            </span>
            <button
              onClick={() => setAnnual(!annual)}
              className={`relative w-12 h-6 rounded-full transition-colors ${
                annual ? "bg-primary" : "bg-secondary"
              }`}
            >
              <div
                className={`absolute top-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                  annual ? "translate-x-6" : "translate-x-0.5"
                }`}
              />
            </button>
            <span
              className={`text-sm ${annual ? "text-foreground" : "text-muted-foreground"}`}
            >
              Annual{" "}
              <span className="text-primary text-xs font-medium">Save 20%</span>
            </span>
          </div>
        </FadeUp>

        <div className="grid lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {plans.map((plan, i) => (
            <FadeUp key={plan.name} delay={i * 0.1}>
              <div
                className={`relative rounded-xl p-6 lg:p-8 h-full flex flex-col ${
                  plan.highlight
                    ? "border-2 border-primary/50 bg-card glow-cyan-strong"
                    : "border border-border/40 bg-card/50"
                }`}
              >
                {plan.highlight && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-primary text-primary-foreground text-xs font-semibold">
                    Most Popular
                  </div>
                )}

                <div className="mb-6">
                  <h3 className="text-xl font-bold text-foreground mb-1">
                    {plan.name}
                  </h3>
                  <p className="text-sm text-muted-foreground">{plan.desc}</p>
                </div>

                <div className="mb-6">
                  {plan.monthlyPrice ? (
                    <div className="flex items-baseline gap-1">
                      <span
                        className="text-4xl font-bold text-foreground"
                        style={{ fontFamily: "var(--font-mono)" }}
                      >
                        ${annual ? plan.annualPrice : plan.monthlyPrice}
                      </span>
                      <span className="text-muted-foreground text-sm">
                        /month
                      </span>
                    </div>
                  ) : (
                    <span className="text-2xl font-bold text-foreground">
                      Custom
                    </span>
                  )}
                  <p className="text-xs text-muted-foreground mt-1">
                    <span
                      className="text-primary font-medium"
                      style={{ fontFamily: "var(--font-mono)" }}
                    >
                      {plan.tokens}
                    </span>{" "}
                    tokens / month
                  </p>
                </div>

                <ul className="space-y-3 mb-8 flex-1">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-2.5">
                      <Check className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                      <span className="text-sm text-muted-foreground">{f}</span>
                    </li>
                  ))}
                </ul>

                <Button
                  className={`w-full ${
                    plan.highlight
                      ? "bg-primary text-primary-foreground hover:bg-primary/90"
                      : "bg-secondary text-foreground hover:bg-secondary/80"
                  }`}
                  size="lg"
                >
                  {plan.monthlyPrice ? "Start Free Trial" : "Contact Sales"}
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
            </FadeUp>
          ))}
        </div>

        <FadeUp delay={0.4}>
          <p className="text-center text-sm text-muted-foreground mt-8">
            All plans include a 14-day free trial. No credit card required.
          </p>
        </FadeUp>
      </div>
    </section>
  );
}

/* ─── Testimonials ─── */
function Testimonials() {
  const testimonials = [
    {
      quote:
        "Digital CMO AI replaced three separate tools and two contractors. Our campaign launch time dropped from 2 weeks to 2 days.",
      name: "Sarah Chen",
      role: "VP Marketing, ScaleUp Inc.",
      stars: 5,
    },
    {
      quote:
        "The Brain module's memory system is incredible. It remembers our brand guidelines, past campaigns, and audience insights — like working with a CMO who never forgets.",
      name: "Marcus Rivera",
      role: "Head of Growth, NovaTech",
      stars: 5,
    },
    {
      quote:
        "We saw a 124% increase in marketing ROI within the first quarter. The analytics module alone is worth the subscription.",
      name: "Emily Nakamura",
      role: "CEO, Bloom Digital",
      stars: 5,
    },
  ];

  return (
    <section className="relative py-24 lg:py-32 bg-card/30">
      <div className="container">
        <FadeUp>
          <div className="text-center max-w-2xl mx-auto mb-16">
            <p className="text-sm font-medium text-primary tracking-wide uppercase mb-3">
              Testimonials
            </p>
            <h2 className="text-3xl lg:text-5xl font-bold tracking-tight">
              Loved by marketing{" "}
              <span className="text-muted-foreground">leaders</span>
            </h2>
          </div>
        </FadeUp>

        <div className="grid md:grid-cols-3 gap-6">
          {testimonials.map((t, i) => (
            <FadeUp key={t.name} delay={i * 0.1}>
              <div className="rounded-xl border border-border/30 bg-background/50 p-6 h-full flex flex-col gradient-border">
                <div className="flex gap-0.5 mb-4">
                  {Array.from({ length: t.stars }).map((_, j) => (
                    <Star
                      key={j}
                      className="w-4 h-4 fill-primary text-primary"
                    />
                  ))}
                </div>
                <p className="text-sm text-foreground/90 leading-relaxed mb-6 flex-1">
                  "{t.quote}"
                </p>
                <div>
                  <p className="text-sm font-semibold text-foreground">
                    {t.name}
                  </p>
                  <p className="text-xs text-muted-foreground">{t.role}</p>
                </div>
              </div>
            </FadeUp>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── CTA Section ─── */
function CTASection() {
  return (
    <section className="relative py-24 lg:py-32 overflow-hidden">
      <div className="absolute inset-0 dot-grid opacity-30" />
      <div className="absolute inset-0 bg-gradient-to-r from-primary/5 via-transparent to-primary/5" />
      <div className="container relative text-center">
        <FadeUp>
          <div className="max-w-3xl mx-auto">
            <h2 className="text-3xl lg:text-5xl font-bold tracking-tight mb-6">
              Ready to replace your marketing stack{" "}
              <span className="text-primary text-glow">with intelligence?</span>
            </h2>
            <p className="text-lg text-muted-foreground mb-8 max-w-xl mx-auto">
              Join thousands of marketing teams already using Digital CMO AI to
              plan, execute, and optimize campaigns at scale.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Button
                size="lg"
                className="bg-primary text-primary-foreground hover:bg-primary/90 glow-cyan text-base px-8 h-12"
              >
                Start Your Free Trial
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
              <Button
                variant="outline"
                size="lg"
                className="border-border/60 text-foreground hover:bg-secondary h-12 px-8 text-base"
              >
                Book a Demo
              </Button>
            </div>
            <p className="text-sm text-muted-foreground mt-6 flex items-center justify-center gap-4">
              <span className="flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5 text-primary" />
                14-day free trial
              </span>
              <span className="flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5 text-primary" />
                No credit card required
              </span>
              <span className="flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5 text-primary" />
                Cancel anytime
              </span>
            </p>
          </div>
        </FadeUp>
      </div>
    </section>
  );
}

/* ─── Footer ─── */
function Footer() {
  const columns = [
    {
      title: "Product",
      links: ["Features", "Pricing", "Integrations", "Changelog", "Roadmap"],
    },
    {
      title: "Resources",
      links: ["Documentation", "API Reference", "Blog", "Case Studies", "Webinars"],
    },
    {
      title: "Company",
      links: ["About", "Careers", "Contact", "Partners", "Press"],
    },
    {
      title: "Legal",
      links: ["Privacy Policy", "Terms of Service", "GDPR", "Security"],
    },
  ];

  return (
    <footer className="border-t border-border/30 py-16">
      <div className="container">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">
          <div className="col-span-2 md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-7 h-7 rounded-lg bg-primary/20 flex items-center justify-center">
                <Brain className="w-4 h-4 text-primary" />
              </div>
              <span className="font-bold text-foreground">
                Digital CMO<span className="text-primary">.ai</span>
              </span>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed">
              AI-powered Chief Marketing Officer for modern teams.
            </p>
          </div>
          {columns.map((col) => (
            <div key={col.title}>
              <h4 className="text-sm font-semibold text-foreground mb-3">
                {col.title}
              </h4>
              <ul className="space-y-2">
                {col.links.map((link) => (
                  <li key={link}>
                    <a
                      href="#"
                      className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="border-t border-border/30 pt-8 flex flex-col sm:flex-row justify-between items-center gap-4">
          <p className="text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} Digital CMO AI. All rights reserved.
          </p>
          <div className="flex gap-6">
            <a href="#" className="text-xs text-muted-foreground hover:text-foreground transition-colors">
              Twitter
            </a>
            <a href="#" className="text-xs text-muted-foreground hover:text-foreground transition-colors">
              LinkedIn
            </a>
            <a href="#" className="text-xs text-muted-foreground hover:text-foreground transition-colors">
              GitHub
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}

/* ─── Main Page ─── */
export default function Home() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar />
      <HeroSection />
      <SocialProof />
      <FeaturesSection />
      <HowItWorks />
      <PricingSection />
      <Testimonials />
      <CTASection />
      <Footer />
    </div>
  );
}
