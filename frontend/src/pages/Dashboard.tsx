import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { LogOut, Plus, RefreshCw } from 'lucide-react';

interface Job {
  job_id: string;
  project_name: string;
  status: string;
  created_at: string;
  result: any;
}

const Dashboard = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNewJob, setShowNewJob] = useState(false);
  const navigate = useNavigate();

  // New Job Form State
  const [projectName, setProjectName] = useState('');
  const [targetUrl, setTargetUrl] = useState('');
  const [jobType, setJobType] = useState('attack_surface');

  const fetchJobs = async () => {
    try {
      const res = await api.get('/jobs');
      setJobs(res.data);
    } catch (err) {
      console.error(err);
      if ((err as any).response?.status === 401) {
        navigate('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000); // Poll every 5s
    return () => clearInterval(interval);
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  const handleCreateJob = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/jobs', {
        project_name: projectName,
        target_url: targetUrl,
        job_type: jobType,
        accept_terms: true,
        scope: [new URL(targetUrl).hostname] // Auto scope for MVP
      });
      setShowNewJob(false);
      setProjectName('');
      setTargetUrl('');
      fetchJobs();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create job');
    }
  };

  return (
    <div>
      <nav>
        <div className="logo">Bounty Platform</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <span>Welcome</span>
          <button onClick={handleLogout} style={{ padding: '0.5em', display: 'flex', alignItems: 'center', gap: '0.5em' }}>
            <LogOut size={16} /> Logout
          </button>
        </div>
      </nav>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1>My Scans</h1>
        <button onClick={() => setShowNewJob(!showNewJob)} style={{ display: 'flex', alignItems: 'center', gap: '0.5em' }}>
          <Plus size={16} /> New Scan
        </button>
      </div>

      {showNewJob && (
        <div className="card">
          <h3>Start New Scan</h3>
          <form onSubmit={handleCreateJob}>
            <div className="form-group">
              <label>Project Name</label>
              <input value={projectName} onChange={e => setProjectName(e.target.value)} required placeholder="My Project" />
            </div>
            <div className="form-group">
              <label>Target URL</label>
              <input value={targetUrl} onChange={e => setTargetUrl(e.target.value)} required placeholder="https://example.com" />
            </div>
            <div className="form-group">
              <label>Scan Type</label>
              <select value={jobType} onChange={e => setJobType(e.target.value)}>
                <option value="attack_surface">Web Attack Surface</option>
                <option value="sca">Source Code Analysis</option>
                <option value="smart_contract">Smart Contract</option>
              </select>
            </div>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button type="submit">Start Scan</button>
              <button type="button" onClick={() => setShowNewJob(false)} style={{ backgroundColor: '#444' }}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <p>Loading jobs...</p>
      ) : (
        <div className="card" style={{ overflowX: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th>Project</th>
                <th>Type</th>
                <th>Target</th>
                <th>Status</th>
                <th>Created At</th>
                <th>Findings</th>
              </tr>
            </thead>
            <tbody>
              {jobs.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center' }}>No scans found. Start one!</td>
                </tr>
              ) : (
                jobs.map(job => (
                  <tr key={job.job_id}>
                    <td>{job.project_name}</td>
                    <td>{job.job_id}</td>
                    <td>{job.result?.target_url || '-'}</td>
                    <td>
                      <span className={`badge ${job.status}`}>
                        {job.status}
                      </span>
                    </td>
                    <td>{new Date(job.created_at).toLocaleString()}</td>
                    <td>
                      {job.result ? (
                        <div style={{ fontSize: '0.8rem' }}>
                          {job.result.web_scan && `Web: ${job.result.web_scan.vulnerabilities?.length || 0} `}
                          {job.result.nuclei && `Nuclei: ${job.result.nuclei.findings?.length || 0}`}
                        </div>
                      ) : '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
