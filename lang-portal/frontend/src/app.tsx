import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';
import StudyActivitiesPage from './pages/StudyActivitiesPage';
import StudyActivityShowPage from './pages/StudyActivityShowPage';
import WordsPage from './pages/WordsPage';
import WordGroupsPage from './pages/WordGroupsPage';
import WordGroupDetailPage from './pages/WordGroupDetailPage';
import SessionsPage from './pages/SessionsPage';
import SettingsPage from './pages/SettingsPage';
import { Quiz } from './components/Quiz';
import { SentenceConstructorPage } from './pages/SentenceConstructorPage';
import KanjiWritingPage from './pages/KanjiWritingPage';
import { Navigation } from './components/Navigation';

const App = () => {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
        <Navigation />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/study-activities" element={<StudyActivitiesPage />} />
            <Route path="/study-activities/:id" element={<StudyActivityShowPage />} />
            <Route path="/words" element={<WordsPage />} />
            <Route path="/word-groups" element={<WordGroupsPage />} />
            <Route path="/word-groups/:groupId" element={<WordGroupDetailPage />} />
            <Route path="/sessions" element={<SessionsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/quiz/select" element={<Quiz />} />
            <Route path="/quiz/:groupId" element={<Quiz />} />
            <Route path="/sentence-constructor" element={<SentenceConstructorPage />} />
            <Route path="/kanji-writing/select" element={<KanjiWritingPage />} />
            <Route path="/kanji-writing/:groupId" element={<KanjiWritingPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
};

export default App; 