import React from 'react';
import { Utensils } from 'lucide-react';

export const Header: React.FC = () => {
  return (
    <header className="bg-orange-500 text-white p-6 shadow-md rounded-b-3xl mb-6">
      <div className="flex items-center justify-center gap-3">
        <Utensils className="w-8 h-8" />
        <h1 className="text-2xl font-bold tracking-wide">Mumbai Meal Planner</h1>
      </div>
      <p className="text-center text-orange-100 text-sm mt-2">Vegetarian • Home-cooked • Fresh</p>
    </header>
  );
};
