import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Upload, Loader2, CheckCircle2 } from 'lucide-react';
import api from '../../lib/api';

export default function ApplyJob() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const response = await api.get('/api/v1/jobs');
        setJobs(Array.isArray(response.data) ? response.data : []);
      } catch (error) {
        console.error('Failed to fetch jobs:', error);
        setJobs([]);
      }
    };
    fetchJobs();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedJob || !file) return;

    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append('job_id', selectedJob);
    formData.append('file', file);

    try {
      const response = await api.post('/api/v1/recruitment/evaluate', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(response.data);
    } catch (error) {
      console.error('Evaluation failed:', error);
      alert('Application failed. Check console for details.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-6">
      <Link to="/candidate" className="inline-flex items-center text-zinc-400 hover:text-white mb-6 transition-colors">
        <ArrowLeft className="w-4 h-4 mr-2" /> Back
      </Link>
      
      <div className="glass-card p-8">
        <h1 className="text-3xl font-bold mb-8">Official Job Application</h1>
        
        {!result ? (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-2">Select a Job</label>
              <select
                required
                value={selectedJob}
                onChange={e => setSelectedJob(e.target.value)}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-brand-500 transition-colors"
              >
                <option value="" disabled>-- Choose an open role --</option>
                {jobs.map(job => (
                  <option key={job.id || job._id} value={job.id || job._id}>
                    {job.title}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-2">Upload Resume (PDF)</label>
              <div className="border-2 border-dashed border-zinc-700 rounded-xl p-8 text-center hover:border-brand-500 transition-colors bg-zinc-900/50 cursor-pointer relative">
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
                <p className="text-xs text-zinc-500 mt-1">Maximum file size: 5MB</p>
              </div>
            </div>

            <div className="pt-4">
              <button
                type="submit"
                disabled={loading || !selectedJob || !file}
                className="w-full bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white px-6 py-4 rounded-lg font-medium inline-flex items-center justify-center transition-colors shadow-lg shadow-brand-500/20"
              >
                {loading ? (
                  <><Loader2 className="w-5 h-5 animate-spin mr-2" /> Processing Application & Evaluation...</>
                ) : (
                  'Submit Application'
                )}
              </button>
            </div>
          </form>
        ) : (
          <div className="text-center py-8">
            <div className="w-20 h-20 bg-brand-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle2 className="w-10 h-10 text-brand-400" />
            </div>
            <h2 className="text-3xl font-bold mb-4">Application Submitted!</h2>
            <p className="text-zinc-400 mb-8 max-w-md mx-auto">
              Your resume has been successfully parsed and evaluated by our AI agent.
            </p>
            
            <div className="bg-zinc-900/80 rounded-xl p-6 max-w-md mx-auto text-left mb-8 border border-zinc-800">
              <h3 className="text-lg font-semibold mb-4 text-brand-400">Your Initial AI Score</h3>
              <div className="flex justify-between items-center mb-2">
                <span className="text-zinc-400">Rank Tier:</span>
                <span className="font-medium text-white">{result.ranking?.rank_tier || 'N/A'}</span>
              </div>
              <div className="flex justify-between items-center mb-4">
                <span className="text-zinc-400">Final Score:</span>
                <span className="font-bold text-3xl text-brand-400 drop-shadow-sm">
                  {result.ranking?.final_score ? Math.round(result.ranking.final_score) : 0}
                  <span className="text-lg text-zinc-600">/100</span>
                </span>
              </div>
              <div className="text-sm text-zinc-400 mt-4 p-3 bg-zinc-950 rounded-lg">
                <p className="font-medium text-zinc-300 mb-1">Feedback:</p>
                {result.ranking?.reason || result.reason}
              </div>
            </div>
            
            <button
              onClick={() => {
                setResult(null);
                setFile(null);
                setSelectedJob('');
              }}
              className="bg-zinc-800 hover:bg-zinc-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
            >
              Apply to Another Job
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
