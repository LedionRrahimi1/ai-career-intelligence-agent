import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/AppShell';
import { SessionProvider } from './lib/session';
import { CVAnalyzerPage } from './pages/CVAnalyzerPage';
import { DashboardPage } from './pages/DashboardPage';
import { InterviewPage } from './pages/InterviewPage';
import { LandingPage } from './pages/LandingPage';
import { RoadmapPage } from './pages/RoadmapPage';

export default function App() {
  return (
    <SessionProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<LandingPage />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="cv-analyzer" element={<CVAnalyzerPage />} />
            <Route path="interview" element={<InterviewPage />} />
            <Route path="roadmap" element={<RoadmapPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </SessionProvider>
  );
}
