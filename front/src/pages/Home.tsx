import { useRef } from 'react';
import { motion } from 'framer-motion';
import APP_NAME from '../constants/AppName';
import FloatingLines from '../components/FloatingLines';
import VariableProximity from '../components/VariableProximity';

export default function Home() {

const containerRef = useRef(null);

  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-950">
      <div className="absolute inset-0 pointer-events-auto">
        <FloatingLines
          linesGradient={['#6366f1', '#8b5cf6', '#a855f7']}
          enabledWaves={['middle', 'bottom']}
          lineCount={[8, 6]}
          lineDistance={[4, 5]}
          animationSpeed={0.8}
          interactive={true}
          bendRadius={3.0}
          bendStrength={-0.8}
          mouseDamping={0.08}
          mixBlendMode="screen"
        />
      </div>
      
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen p-4 pt-24 pointer-events-none">
        <div className="pointer-events-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          <motion.h1 
            className="text-7xl md:text-9xl font-black mb-6 tracking-tight"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            <div
            ref={containerRef}
            style={{position: 'relative'}}
            >
              <VariableProximity
                label={APP_NAME}
                className={'variable-proximity-demo text-7xl md:text-9xl mb-6 tracking-tight text-white'}
                style={{
                  textShadow: '0 0 30px rgba(139, 92, 246, 0.8), 0 0 60px rgba(168, 85, 247, 0.6), 0 10px 30px rgba(0, 0, 0, 0.8), 0 20px 50px rgba(99, 102, 241, 0.4)',
                  filter: 'drop-shadow(0 0 20px rgba(139, 92, 246, 0.6))',
                }}
                fromFontVariationSettings="'wght' 400, 'opsz' 9"
                toFontVariationSettings="'wght' 1000, 'opsz' 40"
                containerRef={containerRef}
                radius={300}
                falloff='linear'
              />
            </div>
          </motion.h1>
          
          <motion.p 
            className="text-2xl md:text-3xl text-white font-semibold mb-4 drop-shadow-lg"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            AI-Powered Music Generation
          </motion.p>

        </motion.div>

        <motion.div
          className="mt-20 text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 1.4 }}
        >
          <p className="text-slate-200 text-sm font-medium">
            Made by Matis, Julien, Carl & Sedanur
          </p>
        </motion.div>
        </div>
      </div>
    </div>
  );
}