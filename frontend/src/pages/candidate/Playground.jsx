import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Upload, Loader2, Beaker, ShieldAlert } from 'lucide-react';
import api from '../../lib/api';

export default function Playground() {
  const [customJd, setCustomJd] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!customJd.trim() || !file) return;

    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append('custom_job_description', customJd);
    formData.append('file', file);

    try {
      const response = await api.post('/api/v1/recruitment/evaluate', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(response.data);
    } catch (error) {
      console.error('Evaluation failed:', error);
      alert('Playground evaluation failed. Check console.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <Link to="/candidate" className="inline-flex items-center text-zinc-400 hover:text-white mb-6 transition-colors">
        <ArrowLeft className="w-4 h-4 mr-2" /> Back
      </Link>
      
      <div className="glass-card p-8 border-purple-500/20">
        <div className="flex items-center mb-8">
          <Beaker className="w-8 h-8 text-purple-400 mr-3" />
          <div>
            <h1 className="text-3xl font-bold">Resume Testing Playground</h1>
            <p className="text-zinc-400 mt-1">Privately test your resume against any custom job description.</p>
          </div>
        </div>

        <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-4 mb-8 flex items-start">
          <ShieldAlert className="w-5 h-5 text-purple-400 mr-3 mt-0.5 flex-shrink-0" />
          <p className="text-sm text-purple-200">
            <strong>Privacy Note:</strong> In Playground mode, your resume, name, and evaluation scores are 
            <strong> NOT saved</strong> to the database. HR will not see these results.
          </p>
        </div>
        
        {!result ? (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-2">Paste a Job Description</label>
              <textarea
                required
                rows={6}
                value={customJd}
                onChange={e => setCustomJd(e.target.value)}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-purple-500 transition-colors"
                placeholder="Paste the requirements or description of a job you want to test your resume against..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-2">Upload Resume (PDF)</label>
              <div className="border-2 border-dashed border-zinc-700 rounded-xl p-8 text-center hover:border-purple-500 transition-colors bg-zinc-900/50 cursor-pointer relative">
                <input
                  required
                  type="file"
                  accept="application/pdf"
                  onChange={e => setFile(e.target.files[0])}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <Upload className="w-10 h-10 text-zinc-500 mx-auto mb-3" />
                <p className="text-zinc-300 font-medium">
                  {file ? file.name : "Click or drag to upload your PDF resume"}
                </p>
              </div>
            </div>

            <div className="pt-4">
              <button
                type="submit"
                disabled={loading || !customJd.trim() || !file}
                className="w-full bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white px-6 py-4 rounded-lg font-medium inline-flex items-center justify-center transition-colors shadow-lg shadow-purple-500/20"
              >
                {loading ? (
                  <><Loader2 className="w-5 h-5 animate-spin mr-2" /> Evaluating privately...</>
                ) : (
                  'Test Resume Score'
                )}
              </button>
            </div>
          </form>
        ) : (
          <div className="py-4">
            <h2 className="text-2xl font-bold mb-6 text-center">Playground Results</h2>
            
            <div className="bg-zinc-900/80 rounded-xl p-8 border border-purple-500/30 shadow-2xl shadow-purple-900/20 backdrop-blur-sm">
              <div className="grid md:grid-cols-2 gap-8 mb-8">
                <div className="text-center p-6 bg-zinc-950/80 rounded-xl border border-zinc-800 shadow-inner">
                  <p className="text-zinc-400 mb-2 font-medium tracking-wide uppercase text-sm">Match Tier</p>
                  <p className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-400">
                    {result.ranking?.rank_tier || 'N/A'}
                  </p>
                </div>
                <div className="text-center p-6 bg-zinc-950/80 rounded-xl border border-zinc-800 shadow-inner">
                  <p className="text-zinc-400 mb-2 font-medium tracking-wide uppercase text-sm">Final Score</p>
                  <p className="text-5xl font-black text-purple-400 drop-shadow-md">
                    {result.ranking?.final_score ? Math.round(result.ranking.final_score) : 0}
                    <span className="text-2xl text-zinc-600 font-bold ml-1">/100</span>
                  </p>
                </div>
              </div>
              
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-white">AI Feedback</h3>
                <div className="text-zinc-300 bg-zinc-950 p-6 rounded-lg leading-relaxed border border-zinc-800 whitespace-pre-wrap">
                  {result.ranking?.reason || result.reason}
                </div>
              </div>
            </div>
            
            <div className="mt-8 text-center">
              <button
                onClick={() => {
                  setResult(null);
                  setFile(null);
                }}
                className="bg-zinc-800 hover:bg-zinc-700 text-white px-8 py-3 rounded-lg font-medium transition-colors"
              >
                Test Another Resume
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
