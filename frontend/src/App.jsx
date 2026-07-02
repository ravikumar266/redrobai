import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';
import Dashboard from './pages/hr/Dashboard';
import CreateJob from './pages/hr/CreateJob';
import Leaderboard from './pages/hr/Leaderboard';
import AgentChat from './pages/hr/AgentChat';
import Selection from './pages/candidate/Selection';
import ApplyJob from './pages/candidate/ApplyJob';
import Playground from './pages/candidate/Playground';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#09090b] text-[#e4e4e7] font-sans">
        <Routes>
          <Route path="/" element={<Landing />} />
          
          {/* HR Routes */}
          <Route path="/hr" element={<Dashboard />} />
          <Route path="/hr/jobs/new" element={<CreateJob />} />
          <Route path="/hr/jobs/:jobId/leaderboard" element={<Leaderboard />} />
          <Route path="/hr/chat/:candidateId/:jobId" element={<AgentChat />} />
          
          {/* Candidate Routes */}
          <Route path="/candidate" element={<Selection />} />
          <Route path="/candidate/apply" element={<ApplyJob />} />
          <Route path="/candidate/playground" element={<Playground />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
