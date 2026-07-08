import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Dashboard from './pages/hr/Dashboard';
import CreateJob from './pages/hr/CreateJob';
import Leaderboard from './pages/hr/Leaderboard';
import AgentChat from './pages/hr/AgentChat';
import Selection from './pages/candidate/Selection';
import ApplyJob from './pages/candidate/ApplyJob';
import Playground from './pages/candidate/Playground';

// Simple Protected Route wrapper
const ProtectedRoute = ({ children, requireRole }) => {
  const token = localStorage.getItem('access_token');
  const role = localStorage.getItem('user_role');
  
  if (!token) return <Navigate to="/login" replace />;
  if (requireRole && role !== requireRole) return <Navigate to="/login" replace />;
  
  return children;
};

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#09090b] text-[#e4e4e7] font-sans">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          
          {/* HR Routes (Protected) */}
          <Route path="/hr" element={<ProtectedRoute requireRole="hr"><Dashboard /></ProtectedRoute>} />
          <Route path="/hr/jobs/new" element={<ProtectedRoute requireRole="hr"><CreateJob /></ProtectedRoute>} />
          <Route path="/hr/jobs/:jobId/leaderboard" element={<ProtectedRoute requireRole="hr"><Leaderboard /></ProtectedRoute>} />
          <Route path="/hr/chat/:candidateId/:jobId" element={<ProtectedRoute requireRole="hr"><AgentChat /></ProtectedRoute>} />
          
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
