import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';

const Navigation: React.FC = () => {
  return (
    <nav className="bg-white dark:bg-gray-800 shadow-md">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <div className="text-xl font-bold text-gray-800 dark:text-gray-100">Language Learning Portal</div>
        <div className="flex space-x-4">
          <Button asChild>
            <Link to="/">Dashboard</Link>
          </Button>
          <Button asChild>
            <Link to="/study-activities">Study Activities</Link>
          </Button>
          <Button asChild>
            <Link to="/words">Words</Link>
          </Button>
          <Button asChild>
            <Link to="/word-groups">Word Groups</Link>
          </Button>
          <Button asChild>
            <Link to="/sessions">Sessions</Link>
          </Button>
          <Button asChild>
            <Link to="/settings">Settings</Link>
          </Button>
        </div>
      </div>
    </nav>
  );
};

export { Navigation };