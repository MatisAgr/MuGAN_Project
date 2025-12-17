import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import APP_NAME from '../constants/AppName';
import { LineChart, Music, Database } from 'lucide-react';
import FloatingLines from '../components/FloatingLines';

export default function Home() {
  const features = [
    {
      title: "Training Dashboard",
      description: "Monitor your AI model training in real-time with detailed charts and metrics",
      icon: LineChart,
      link: "/training",
      color: "from-indigo-500 to-indigo-600"
    },
    {
      title: "Music Generator",
      description: "Generate piano music with AI and visualize the audio spectrum",
      icon: Music,
      link: "/generator",
      color: "from-purple-500 to-purple-600"
    },
    {
      title: "Music Database",
      description: "Explore training samples and community-generated music",
      icon: Database,
      link: "/database",
      color: "from-violet-500 to-violet-600"
    }
  ];

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
            <span className="bg-gradient-to-r from-indigo-300 via-purple-300 to-pink-300 bg-clip-text text-transparent drop-shadow-2xl plus-jakarta-sans-800">
              {APP_NAME}
            </span>
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
          className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl w-full px-4"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.8 }}
        >
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.9 + index * 0.1 }}
              whileHover={{ scale: 1.05, y: -10 }}
              className="group"
            >
              <Link
                to={feature.link}
                className="block h-full bg-slate-800/50 backdrop-blur-xl border border-purple-500/30 rounded-2xl p-8 hover:bg-slate-800/70 hover:border-purple-500/50 transition-all shadow-2xl cursor-pointer"
              >
                <div className={`w-16 h-16 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-6 group-hover:scale-110 transition-transform shadow-lg`}>
                  <feature.icon className="text-3xl text-white" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-3 tracking-tight">{feature.title}</h3>
                <p className="text-slate-100 font-medium leading-relaxed">{feature.description}</p>
                
                <div className="mt-6 flex items-center text-purple-300 group-hover:text-purple-200 transition-colors font-semibold">
                  <span className="mr-2">Explore</span>
                  <svg className="w-5 h-5 group-hover:translate-x-2 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                </div>
              </Link>
            </motion.div>
          ))}
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