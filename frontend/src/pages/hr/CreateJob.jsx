import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Loader2, Save } from 'lucide-react';
import api from '../../lib/api';

export default function CreateJob() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    job_description: '',
    required_skills: '',
    preferred_skills: '',
    experience_required_years: 0
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = {
        ...formData,
        required_skills: formData.required_skills.split(',').map(s => s.trim()).filter(Boolean),
        preferred_skills: formData.preferred_skills.split(',').map(s => s.trim()).filter(Boolean),
        experience_required_years: parseFloat(formData.experience_required_years) || 0
      };
      await api.post('/api/v1/jobs', payload);
      navigate('/hr');
    } catch (error) {
      console.error('Failed to create job:', error);
      alert('Failed to create job. Check console.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-6">
      <Link to="/hr" className="inline-flex items-center text-zinc-400 hover:text-white mb-6 transition-colors">
        <ArrowLeft className="w-4 h-4 mr-2" /> Back to Dashboard
      </Link>
      
      <div className="glass-card p-8">
        <h1 className="text-3xl font-bold mb-8">Create Job Posting</h1>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">Job Title</label>
            <input
              required
              type="text"
              value={formData.title}
              onChange={e => setFormData({...formData, title: e.target.value})}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-brand-500 transition-colors"
              placeholder="e.g. Senior Frontend Developer"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">Job Description</label>
            <textarea
              required
              rows={6}
              value={formData.job_description}
              onChange={e => setFormData({...formData, job_description: e.target.value})}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-brand-500 transition-colors"
              placeholder="Detailed job description..."
            />
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-2">Required Skills (comma separated)</label>
              <input
                required
                type="text"
                value={formData.required_skills}
                onChange={e => setFormData({...formData, required_skills: e.target.value})}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-brand-500 transition-colors"
                placeholder="React, TypeScript, Node.js"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-2">Preferred Skills (comma separated)</label>
              <input
                type="text"
                value={formData.preferred_skills}
                onChange={e => setFormData({...formData, preferred_skills: e.target.value})}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-brand-500 transition-colors"
                placeholder="Docker, AWS, GraphQL"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">Required Experience (Years)</label>
            <input
              required
              type="number"
              step="0.5"
              min="0"
              value={formData.experience_required_years}
              onChange={e => setFormData({...formData, experience_required_years: e.target.value})}
              className="w-full md:w-1/3 bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-brand-500 transition-colors"
            />
          </div>

          <div className="pt-4">
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white px-6 py-4 rounded-lg font-medium inline-flex items-center justify-center transition-colors shadow-lg shadow-brand-500/20"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <><Save className="w-5 h-5 mr-2" /> Save & Publish Job</>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
