import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FileBadge, Beaker, ArrowLeft } from 'lucide-react';

export default function Selection() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 relative overflow-hidden">
      <Link to="/" className="absolute top-6 left-6 inline-flex items-center text-zinc-400 hover:text-white transition-colors z-20">
        <ArrowLeft className="w-4 h-4 mr-2" /> Back to Home
      </Link>

      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-12 z-10"
      >
        <h1 className="text-4xl md:text-5xl font-bold mb-4 tracking-tight">
          Candidate Portal
        </h1>
        <p className="text-zinc-400 text-lg max-w-xl mx-auto">
          Choose how you want to proceed with your application journey.
        </p>
      </motion.div>

      <div className="grid md:grid-cols-2 gap-6 w-full max-w-4xl z-10">
        <motion.button
          whileHover={{ scale: 1.02, y: -5 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => navigate('/candidate/apply')}
          className="glass-card p-8 flex flex-col items-center justify-center text-center group cursor-pointer border-transparent hover:border-brand-500/50 transition-all"
        >
          <div className="w-16 h-16 bg-brand-500/10 rounded-2xl flex items-center justify-center mb-6 group-hover:bg-brand-500/20 transition-colors">
            <FileBadge className="w-8 h-8 text-brand-400" />
          </div>
          <h2 className="text-2xl font-semibold mb-2">Apply for a Job</h2>
          <p className="text-zinc-400 text-sm">Select an official job posting and submit your resume for review by HR.</p>
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.02, y: -5 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => navigate('/candidate/playground')}
          className="glass-card p-8 flex flex-col items-center justify-center text-center group cursor-pointer border-transparent hover:border-purple-500/50 transition-all"
        >
          <div className="w-16 h-16 bg-purple-500/10 rounded-2xl flex items-center justify-center mb-6 group-hover:bg-purple-500/20 transition-colors">
            <Beaker className="w-8 h-8 text-purple-400" />
          </div>
          <h2 className="text-2xl font-semibold mb-2">Test Playground</h2>
          <p className="text-zinc-400 text-sm">Paste any custom job description to privately test your resume score without saving data.</p>
        </motion.button>
      </div>
    </div>
  );
}
