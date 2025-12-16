import React from 'react';

export const Spinner: React.FC = () => (
  <div className="flex justify-center items-center space-x-2 animate-pulse">
    <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
    <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
    <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
  </div>
);
