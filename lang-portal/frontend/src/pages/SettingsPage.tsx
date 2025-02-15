import React from 'react';

const SettingsPage: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      <h1 className="text-3xl font-bold dark:text-gray-100">Settings</h1>
      <div className="space-y-4">
        <p className="text-lg text-gray-600 dark:text-gray-300">This is the settings page. You can add settings options here.</p>
      </div>
    </div>
  );
};

export default SettingsPage;