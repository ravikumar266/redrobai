import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Briefcase, UserCircle2 } from 'lucide-react';

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 relative overflow-hidden">
      {/* Background Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-brand-500/10 rounded-full blur-[120px] pointer-events-none" />

      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-16 z-10"
      >
        <h1 className="text-5xl md:text-7xl font-bold mb-4 tracking-tight">
          RedRob <span className="gradient-text">OS</span>
        </h1>
        <p className="text-zinc-400 text-lg md:text-xl max-w-2xl mx-auto">
          The future of AI-assisted recruitment. Please select your portal to continue.
        </p>
      </motion.div>

      <div className="grid md:grid-cols-2 gap-8 w-full max-w-4xl z-10">
        <motion.button
          whileHover={{ scale: 1.02, y: -5 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => navigate('/candidate')}
          className="glass-card p-10 flex flex-col items-center justify-center text-center group cursor-pointer border-transparent hover:border-brand-500/50 transition-all"
        >
          <div className="w-20 h-20 bg-brand-500/10 rounded-2xl flex items-center justify-center mb-6 group-hover:bg-brand-500/20 transition-colors">
            <UserCircle2 className="w-10 h-10 text-brand-400" />
          </div>
          <h2 className="text-2xl font-semibold mb-2">I am a Candidate</h2>
          <p className="text-zinc-400">Apply for open roles or test your resume in the playground.</p>
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.02, y: -5 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => navigate('/hr')}
          className="glass-card p-10 flex flex-col items-center justify-center text-center group cursor-pointer border-transparent hover:border-blue-500/50 transition-all"
        >
          <div className="w-20 h-20 bg-blue-500/10 rounded-2xl flex items-center justify-center mb-6 group-hover:bg-blue-500/20 transition-colors">
            <Briefcase className="w-10 h-10 text-blue-400" />
          </div>
          <h2 className="text-2xl font-semibold mb-2">I am an HR/Manager</h2>
          <p className="text-zinc-400">Manage job postings, view leaderboards, and chat with AI.</p>
        </motion.button>
      </div>
    </div>
  );
}
