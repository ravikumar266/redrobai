import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Plus, Users, ArrowLeft, Loader2 } from 'lucide-react';
import api from '../../lib/api';

export default function Dashboard() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const response = await api.get('/api/v1/jobs');
        setJobs(Array.isArray(response.data) ? response.data : []);
      } catch (error) {
        console.error('Failed to fetch jobs:', error);
        setJobs([]);
      } finally {
        setLoading(false);
      }
    };
    fetchJobs();
  }, []);

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <Link to="/" className="inline-flex items-center text-zinc-400 hover:text-white mb-4 transition-colors">
            <ArrowLeft className="w-4 h-4 mr-2" /> Back to Home
          </Link>
          <h1 className="text-3xl font-bold">HR Dashboard</h1>
        </div>
        <button
          onClick={() => navigate('/hr/jobs/new')}
          className="bg-brand-500 hover:bg-brand-600 text-white px-6 py-3 rounded-lg font-medium inline-flex items-center transition-colors shadow-lg shadow-brand-500/20"
        >
          <Plus className="w-5 h-5 mr-2" /> Create New Job
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
        </div>
      ) : jobs.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <h3 className="text-xl font-medium text-zinc-300 mb-2">No jobs created yet</h3>
          <p className="text-zinc-500">Create your first job posting to start receiving applications.</p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {jobs.map((job) => (
            <div key={job.id || job._id} className="glass-card p-6 flex flex-col">
              <h3 className="text-xl font-semibold mb-2">{job.title}</h3>
              <p className="text-zinc-400 text-sm mb-4 line-clamp-2">{job.job_description}</p>
              
              <div className="mt-auto">
                <div className="flex flex-wrap gap-2 mb-4">
                  {job.required_skills?.slice(0, 3).map(skill => (
                    <span key={skill} className="px-2 py-1 bg-zinc-800 rounded text-xs text-zinc-300">
                      {skill}
                    </span>
                  ))}
                  {job.required_skills?.length > 3 && (
                    <span className="px-2 py-1 bg-zinc-800 rounded text-xs text-zinc-300">
                      +{job.required_skills.length - 3} more
                    </span>
                  )}
                </div>
                
                <button
                  onClick={() => navigate(`/hr/jobs/${job.id || job._id}/leaderboard`)}
                  className="w-full bg-zinc-800 hover:bg-zinc-700 text-white px-4 py-2 rounded-lg font-medium inline-flex items-center justify-center transition-colors"
                >
                  <Users className="w-4 h-4 mr-2" /> View Leaderboard
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
