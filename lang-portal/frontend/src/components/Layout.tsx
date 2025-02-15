import React from 'react';
import { Navigation } from './Navigation';
import { Breadcrumbs } from './Breadcrumbs';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <Navigation />
      <div className="container mx-auto px-4 py-8">
        <Breadcrumbs />
        <div className="mt-8">
          {children}
        </div>
      </div>
    </div>
  );
};