import React from 'react';
import { useLocation } from 'react-router-dom';
import { Link } from 'react-router-dom';

const Breadcrumbs: React.FC = () => {
  const location = useLocation();
  const pathnames = location.pathname.split('/').filter(x => x);

  return (
    <nav className="flex items-center space-x-2 text-gray-600 dark:text-gray-300">
      <Link to="/" className="text-blue-600 hover:underline dark:text-blue-400">Dashboard</Link>
      {pathnames.map((name, index) => {
        const routeTo = `/${pathnames.slice(0, index + 1).join('/')}`;
        const isLast = index === pathnames.length - 1;
        return isLast ? (
          <span key={index} className="text-gray-600 dark:text-gray-300">{name}</span>
        ) : (
          <Link key={index} to={routeTo} className="text-blue-600 hover:underline dark:text-blue-400">{name}</Link>
        );
      })}
    </nav>
  );
};

export { Breadcrumbs };