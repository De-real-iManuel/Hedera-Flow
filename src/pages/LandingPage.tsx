import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ArrowRight, Zap, Globe, Shield, Link2, Layers, Moon, Sun } from "lucide-react";
import { useNavigate } from "react-router-dom";
import logo from "@/assets/hedera-flow-logo.png";
import chainHedera from "@/assets/chain-hedera.png";
import chainSolana from "@/assets/chain-solana.png";
import chainEthereum from "@/assets/chain-ethereum.png";
import chainPolygon from "@/assets/chain-polygon.png";
import chainZetachain from "@/assets/chain-zetachain.png";

const FLAG_ROWS = [
  ["us", "gb", "de", "fr", "jp", "kr", "br", "in", "au", "ca"],
  ["ng", "za", "ke", "gh", "ae", "sg", "mx", "co", "ar", "eg"],
  ["id", "tr", "sa", "ph", "vn", "th", "pk", "bd", "et", "tz"],
];

const CHAINS = [
  { name: "Hedera", logo: chainHedera, tag: "Native" },
  { name: "Solana", logo: chainSolana, tag: "SPL" },
  { name: "Ethereum", logo: chainEthereum, tag: "ERC-20" },
  { name: "Polygon", logo: chainPolygon, tag: "Bridge" },
];

const ZETACHAIN_LOGO = chainZetachain;

const FEATURES = [
  {
    icon: Zap,
    title: "Instant Settlement",
    desc: "Sub-second finality on Hedera's hashgraph consensus for real-time cross-border payments.",
  },
  {
    icon: Shield,
    title: "Enterprise Security",
    desc: "aBFT-grade security with Hedera's governance council of global enterprises.",
  },
  {
    icon: Globe,
    title: "Global Reach",
    desc: "Pay utility bills across 50+ countries using HBAR, SOL, or stablecoins.",
  },
  {
    icon: Link2,
    title: "Cross-Chain Bridges",
    desc: "Native interoperability pipeline connecting Hedera to Solana, Ethereum and more.",
  },
];

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
};

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" as const } },
};

const LandingPage = () => {
  const navigate = useNavigate();
  const [dark, setDark] = useState(() => document.documentElement.classList.contains("dark"));

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  return (
    <div className="min-h-screen bg-background overflow-hidden">
      {/* Dark mode toggle */}
      <button
        onClick={() => setDark((d) => !d)}
        className="fixed top-4 right-4 z-50 w-10 h-10 rounded-full glass-card-elevated flex items-center justify-center tap-scale"
        aria-label="Toggle dark mode"
      >
        {dark ? <Sun className="w-5 h-5 text-warning" /> : <Moon className="w-5 h-5 text-foreground" />}
      </button>

      {/* ─── Hero ─── */}
      <section className="relative px-6 pt-12 pb-16 text-center overflow-hidden">
        {/* Animated accent lines */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-24 left-0 right-0 h-px energy-wave animate-wave-flow" />
          <div className="absolute top-24 translate-y-3 left-0 right-0 h-px energy-wave animate-wave-flow" style={{ animationDelay: "0.5s" }} />
          <div className="absolute bottom-0 left-0 right-0 h-px glow-line opacity-30" />
        </div>

        <motion.div initial="hidden" animate="show" variants={stagger} className="relative z-10 max-w-2xl mx-auto">
          {/* Logo */}
          <motion.div variants={fadeUp} className="flex justify-center mb-6">
            <div className="relative">
              <img src={logo} alt="Hedera Flow" className="w-24 h-24 rounded-3xl shadow-lg" />
              <div className="absolute -inset-2 rounded-[1.75rem] border border-accent/20 animate-pulse-glow" />
            </div>
          </motion.div>

          <motion.h1 variants={fadeUp} className="text-4xl sm:text-5xl font-extrabold text-foreground leading-tight tracking-tight">
            Pay Bills <span className="text-accent">Globally</span>,
            <br />
            Powered by <span className="text-accent">Hedera</span>
          </motion.h1>

          <motion.p variants={fadeUp} className="mt-4 text-base sm:text-lg text-muted-foreground max-w-md mx-auto leading-relaxed">
            Cross-chain interoperability meets real-world utility. Verify meters and pay electricity bills using Hedera's native pipeline — across borders, in seconds.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div variants={fadeUp} className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={() => navigate("/auth")}
              className="tap-scale w-full sm:w-auto px-8 py-4 rounded-2xl gradient-accent text-accent-foreground font-semibold text-base flex items-center justify-center gap-2"
            >
              Get Started <ArrowRight className="w-5 h-5" />
            </button>
            <button
              onClick={() => {
                document.getElementById("interop")?.scrollIntoView({ behavior: "smooth" });
              }}
              className="tap-scale w-full sm:w-auto px-8 py-4 rounded-2xl glass-card-elevated font-semibold text-base text-foreground flex items-center justify-center gap-2"
            >
              Learn More
            </button>
          </motion.div>
        </motion.div>
      </section>

      {/* ─── Country Flags Marquee ─── */}
      <section className="py-8 overflow-hidden">
        <p className="text-xs text-muted-foreground uppercase tracking-widest font-semibold text-center mb-5">
          Serving Users in 50+ Countries
        </p>
        <div className="space-y-3">
          {FLAG_ROWS.map((row, rowIdx) => (
            <div key={rowIdx} className="relative overflow-hidden">
              <motion.div
                className="flex gap-4 whitespace-nowrap"
                animate={{ x: rowIdx % 2 === 0 ? ["0%", "-50%"] : ["-50%", "0%"] }}
                transition={{ duration: 18 + rowIdx * 4, ease: "linear", repeat: Infinity }}
              >
                {[...row, ...row].map((code, i) => (
                  <div
                    key={i}
                    className="flex-shrink-0 w-14 h-10 glass-card flex items-center justify-center overflow-hidden"
                  >
                    <img
                      src={`https://flagcdn.com/w40/${code}.png`}
                      srcSet={`https://flagcdn.com/w80/${code}.png 2x`}
                      alt={code.toUpperCase()}
                      className="w-8 h-6 object-cover rounded-sm"
                      loading="lazy"
                    />
                  </div>
                ))}
              </motion.div>
            </div>
          ))}
        </div>
      </section>

      {/* ─── Interoperability Section ─── */}
      <section id="interop" className="px-6 py-16">
        <motion.div
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-60px" }}
          variants={stagger}
          className="max-w-2xl mx-auto"
        >
          <motion.div variants={fadeUp} className="text-center mb-10">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-accent/10 text-accent text-xs font-semibold uppercase tracking-wider mb-4">
              <Layers className="w-3.5 h-3.5" />
              Cross-Chain Native Pipeline
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-foreground leading-tight">
              Interoperability via <span className="text-accent">Hedera</span>
            </h2>
            <p className="mt-3 text-muted-foreground max-w-md mx-auto">
              Hedera acts as the settlement backbone — bridging chains, tokens, and fiat rails into one seamless payment pipeline.
            </p>
          </motion.div>

          {/* Chain visualization */}
          <motion.div variants={fadeUp} className="glass-card-elevated p-6 mb-10">
            <div className="flex items-center justify-center gap-3 flex-wrap">
              {CHAINS.map((chain, i) => (
                <div key={chain.name} className="flex items-center gap-3">
                  <div className="flex flex-col items-center gap-1.5">
                    <div className="w-14 h-14 rounded-2xl bg-card border border-border flex items-center justify-center p-2 shadow-sm">
                      <img src={chain.logo} alt={chain.name} className="w-9 h-9 object-contain" />
                    </div>
                    <span className="text-[11px] font-bold text-foreground">{chain.name}</span>
                    <span className="text-[10px] font-semibold text-muted-foreground">{chain.tag}</span>
                  </div>
                  {i < CHAINS.length - 1 && (
                    <div className="flex flex-col items-center mx-1">
                      {/* Animated connection line top */}
                      <div className="relative w-8 h-1 rounded-full overflow-hidden bg-accent/10">
                        <div className="absolute inset-0 bg-accent/40 animate-bridge-pulse origin-center" />
                        <div className="absolute top-0 w-1.5 h-1 rounded-full bg-accent animate-data-flow" />
                      </div>
                      {/* ZetaChain connector */}
                      <div className="w-8 h-8 rounded-full bg-success/15 border border-success/30 flex items-center justify-center my-1.5 relative">
                        <img src={ZETACHAIN_LOGO} alt="ZetaChain" className="w-4 h-4 object-contain" />
                        <div className="absolute inset-0 rounded-full border border-success/20 animate-pulse-glow" />
                      </div>
                      {/* Animated connection line bottom */}
                      <div className="relative w-8 h-1 rounded-full overflow-hidden bg-accent/10">
                        <div className="absolute inset-0 bg-accent/40 animate-bridge-pulse origin-center" style={{ animationDelay: "0.5s" }} />
                        <div className="absolute top-0 w-1.5 h-1 rounded-full bg-accent animate-data-flow" style={{ animationDelay: "0.7s" }} />
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
            <div className="flex items-center justify-center gap-2 mt-5">
              <img src={ZETACHAIN_LOGO} alt="ZetaChain" className="w-4 h-4 object-contain" />
              <p className="text-center text-xs text-muted-foreground">
                Connected via <span className="text-success font-semibold">ZetaChain</span> — omnichain interoperability layer
              </p>
            </div>
          </motion.div>

          {/* Feature cards */}
          <motion.div variants={stagger} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {FEATURES.map((feat) => (
              <motion.div
                key={feat.title}
                variants={fadeUp}
                className="glass-card p-5 group hover:border-accent/30 transition-colors"
              >
                <div className="w-10 h-10 rounded-xl gradient-accent flex items-center justify-center mb-3">
                  <feat.icon className="w-5 h-5 text-accent-foreground" />
                </div>
                <h3 className="font-bold text-foreground mb-1">{feat.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{feat.desc}</p>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>
      </section>

      {/* ─── Bottom CTA ─── */}
      <section className="px-6 pb-16">
        <motion.div
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
          variants={fadeUp}
          className="max-w-2xl mx-auto gradient-navy rounded-3xl p-8 text-center"
        >
          <h3 className="text-2xl font-bold text-primary-foreground mb-2">
            Ready to go cross-chain?
          </h3>
          <p className="text-primary-foreground/70 text-sm mb-6">
            Start verifying meters and paying bills with Hedera, Solana, and beyond.
          </p>
          <button
            onClick={() => navigate("/auth")}
            className="tap-scale inline-flex items-center gap-2 px-8 py-4 rounded-2xl bg-accent text-accent-foreground font-semibold text-base"
          >
            Launch App <ArrowRight className="w-5 h-5" />
          </button>
        </motion.div>
      </section>
    </div>
  );
};

export default LandingPage;
