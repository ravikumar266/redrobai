import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Loader2, MessageSquare, Award, CheckCircle2 } from 'lucide-react';
import api from '../../lib/api';

export default function Leaderboard() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLeaderboard = async () => {
      try {
        const response = await api.get(`/api/v1/jobs/${jobId}/candidates`);
        setLeaderboard(Array.isArray(response.data?.leaderboard) ? response.data.leaderboard : []);
      } catch (error) {
        console.error('Failed to fetch leaderboard:', error);
        setLeaderboard([]);
      } finally {
        setLoading(false);
      }
    };
    fetchLeaderboard();
  }, [jobId]);

  return (
    <div className="max-w-6xl mx-auto p-6">
      <Link to="/hr" className="inline-flex items-center text-zinc-400 hover:text-white mb-6 transition-colors">
        <ArrowLeft className="w-4 h-4 mr-2" /> Back to Dashboard
      </Link>
      
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Candidate Leaderboard</h1>
          <p className="text-zinc-400 mt-2">Ranked by AI evaluation score</p>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
        </div>
      ) : leaderboard.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <Award className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-zinc-300 mb-2">No candidates yet</h3>
          <p className="text-zinc-500">Share this job posting to start receiving applications.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {leaderboard.map((item, index) => {
            const { candidate, ranking } = item;
            return (
              <div key={candidate.id} className="glass-card p-6 flex flex-col md:flex-row items-center gap-6 hover:border-zinc-600 transition-colors">
                <div className="flex-shrink-0 w-16 h-16 rounded-full bg-zinc-800 flex items-center justify-center text-2xl font-bold border-2 border-brand-500/30 text-brand-400">
                  #{index + 1}
                </div>
                
                <div className="flex-grow text-center md:text-left">
                  <h3 className="text-xl font-semibold text-white">{candidate.name}</h3>
                  <div className="flex flex-wrap items-center justify-center md:justify-start gap-4 mt-2 text-sm text-zinc-400">
                    <span>{candidate.email}</span>
                    <span>•</span>
                    <span>{candidate.experience_years} YOE</span>
                  </div>
                  {ranking.rank_tier && (
                    <div className="mt-3 inline-flex items-center px-3 py-1.5 rounded-full bg-brand-500/10 text-brand-400 text-sm font-medium border border-brand-500/20 shadow-sm">
                      <CheckCircle2 className="w-4 h-4 mr-1.5" />
                      {ranking.rank_tier} ({ranking.final_score ? Math.round(ranking.final_score) : 0}/100)
                    </div>
                  )}
                </div>

                <div className="flex-shrink-0 w-full md:w-auto mt-4 md:mt-0">
                  <button
                    onClick={() => navigate(`/hr/chat/${candidate.id}/${jobId}`)}
                    className="w-full md:w-auto bg-brand-500 hover:bg-brand-600 text-white px-6 py-3 rounded-lg font-medium inline-flex items-center justify-center transition-colors shadow-lg shadow-brand-500/20"
                  >
                    <MessageSquare className="w-5 h-5 mr-2" /> Chat with AI
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
