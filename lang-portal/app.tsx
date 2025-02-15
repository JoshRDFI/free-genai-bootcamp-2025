import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { DashboardPage } from './pages/DashboardPage';
import { StudyActivitiesPage } from './pages/StudyActivitiesPage';
import { StudyActivityShowPage } from './pages/StudyActivityShowPage';
import { WordsPage } from './pages/WordsPage';
import { WordShowPage } from './pages/WordShowPage';
import { WordGroupsPage } from './pages/WordGroupsPage';
import { WordGroupShowPage } from './pages/WordGroupShowPage';
import { SessionsPage } from './pages/SessionsPage';
import { SessionShowPage } from './pages/SessionShowPage';
import { SettingsPage } from './pages/SettingsPage';
import { Layout } from './components/Layout';
import './index.css';

const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement);
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/study-activities" element={<StudyActivitiesPage />} />
          <Route path="/study-activities/:id" element={<StudyActivityShowPage />} />
          <Route path="/words" element={<WordsPage />} />
          <Route path="/words/:id" element={<WordShowPage />} />
          <Route path="/word-groups" element={<WordGroupsPage />} />
          <Route path="/word-groups/:id" element={<WordGroupShowPage />} />
          <Route path="/sessions" element={<SessionsPage />} />
          <Route path="/sessions/:id" element={<SessionShowPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  </React.StrictMode>
);