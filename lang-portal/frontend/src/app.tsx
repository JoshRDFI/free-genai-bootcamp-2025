import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
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

const App = () => {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
        <nav className="bg-white dark:bg-gray-800 shadow-md p-4">
          <div className="container mx-auto flex justify-between items-center">
            <h1 className="text-xl font-bold text-gray-800 dark:text-gray-100">Language Learning Portal</h1>
            <div className="flex space-x-6">
              <Link to="/" className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white px-3 py-2">Dashboard</Link>
              <Link to="/study-activities" className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white px-3 py-2">Study Activities</Link>
              <Link to="/words" className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white px-3 py-2">Words</Link>
              <Link to="/word-groups" className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white px-3 py-2">Word Groups</Link>
              <Link to="/sessions" className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white px-3 py-2">Sessions</Link>
              <Link to="/sentence-constructor" className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white px-3 py-2">Sentence Constructor</Link>
              <Link to="/settings" className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white px-3 py-2">Settings</Link>
            </div>
          </div>
        </nav>
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
            <Route path="/quiz/:groupId" element={<Quiz />} />
            <Route path="/sentence-constructor" element={<SentenceConstructorPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
};

export default App; 