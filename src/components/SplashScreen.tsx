import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, Zap, ScanLine, Shield } from "lucide-react";
import logo from "@/assets/hedera-flow-logo.png";

const slides = [
  {
    icon: Zap,
    title: "Fair Bills, Verified in Seconds",
    desc: "AI-powered meter reading ensures you only pay for what you use.",
  },
  {
    icon: ScanLine,
    title: "Snap. Verify. Pay.",
    desc: "Point your camera at the meter and let our AI handle the rest.",
  },
  {
    icon: Shield,
    title: "Transparent & Audit-Proof",
    desc: "Every bill is recorded with immutable proof you can trust.",
  },
];

const SplashScreen = ({ onComplete }: { onComplete: () => void }) => {
  const [step, setStep] = useState(0);

  return (
    <div className="fixed inset-0 z-50 bg-background flex flex-col">
      <AnimatePresence mode="wait">
        {step === 0 ? (
          <motion.div
            key="splash"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.5 }}
            className="flex-1 flex flex-col items-center justify-center px-8 relative overflow-hidden"
          >
            {/* Background wave accents */}
            <div className="absolute inset-0 pointer-events-none">
              <div className="absolute top-1/3 left-0 right-0 h-px energy-wave animate-wave-flow" />
              <div className="absolute top-1/3 translate-y-3 left-0 right-0 h-px energy-wave animate-wave-flow" style={{ animationDelay: "0.5s" }} />
              <div className="absolute top-1/3 translate-y-6 left-0 right-0 h-px energy-wave animate-wave-flow" style={{ animationDelay: "1s" }} />
            </div>

            <motion.img
              src={logo}
              alt="Hedera Flow"
              className="w-28 h-28 rounded-3xl mb-8"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.2, duration: 0.6, ease: "easeOut" as const }}
            />

            <motion.h1
              className="text-3xl font-bold text-foreground text-center leading-tight"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.5 }}
            >
              Hedera Flow
            </motion.h1>

            <motion.p
              className="text-base text-muted-foreground text-center mt-3 max-w-[260px]"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7, duration: 0.5 }}
            >
              Fair Bills, Verified in Seconds
            </motion.p>

            <motion.div
              className="absolute bottom-0 left-0 right-0 h-1 gradient-accent"
              initial={{ scaleX: 0, originX: 0 }}
              animate={{ scaleX: 1 }}
              transition={{ delay: 0.3, duration: 2.5, ease: "easeInOut" as const }}
              onAnimationComplete={() => setStep(1)}
            />
          </motion.div>
        ) : (
          <OnboardingSlides onComplete={onComplete} />
        )}
      </AnimatePresence>
    </div>
  );
};

const OnboardingSlides = ({ onComplete }: { onComplete: () => void }) => {
  const [current, setCurrent] = useState(0);
  const slide = slides[current];
  const isLast = current === slides.length - 1;

  return (
    <motion.div
      key="onboarding"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex-1 flex flex-col"
    >
      <AnimatePresence mode="wait">
        <motion.div
          key={current}
          initial={{ opacity: 0, x: 40 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -40 }}
          transition={{ duration: 0.3 }}
          className="flex-1 flex flex-col items-center justify-center px-10 text-center"
        >
          <div className="w-20 h-20 rounded-3xl gradient-navy flex items-center justify-center mb-8">
            <slide.icon className="w-9 h-9 text-primary-foreground" />
          </div>
          <h2 className="text-2xl font-bold text-foreground leading-snug">{slide.title}</h2>
          <p className="text-sm text-muted-foreground mt-3 max-w-[280px]">{slide.desc}</p>
        </motion.div>
      </AnimatePresence>

      <div className="px-8 pb-12 space-y-5">
        {/* Dots */}
        <div className="flex items-center justify-center gap-2">
          {slides.map((_, i) => (
            <div
              key={i}
              className={`h-1.5 rounded-full transition-all duration-300 ${
                i === current ? "w-6 bg-accent" : "w-1.5 bg-border"
              }`}
            />
          ))}
        </div>

        <button
          onClick={() => (isLast ? onComplete() : setCurrent(current + 1))}
          className="tap-scale w-full py-4 rounded-2xl gradient-accent text-accent-foreground font-semibold text-base flex items-center justify-center gap-2"
        >
          {isLast ? "Get Started" : "Next"}
          <ArrowRight className="w-5 h-5" />
        </button>

        {!isLast && (
          <button
            onClick={onComplete}
            className="w-full text-center text-sm text-muted-foreground"
          >
            Skip
          </button>
        )}
      </div>
    </motion.div>
  );
};

export default SplashScreen;
