import React from 'react';
import { Link } from 'react-router-dom';

const Navigation: React.FC = () => {
  return (
    <nav className="bg-white dark:bg-gray-800 shadow-md">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <div className="text-xl font-bold text-gray-800 dark:text-gray-100">Language Learning Portal</div>
        <div className="flex space-x-4">
          <Link to="/" className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white">Dashboard</Link>
          <Link to="/study-activities" className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white">Study Activities</Link>
          <Link to="/words" className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white">Words</Link>
          <Link to="/word-groups" className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white">Word Groups</Link>
          <Link to="/sessions" className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white">Sessions</Link>
          <Link to="/settings" className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white">Settings</Link>
        </div>
      </div>
    </nav>
  );
};

export { Navigation };