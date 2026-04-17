import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
}

export const Card: React.FC<CardProps> = ({ children, className = '', hover = false }) => {
  return (
    <div
      className={`
        bg-[#171717] border border-[#262626] rounded-lg p-6
        ${hover ? 'transition-all duration-300 hover:border-[#404040] hover:shadow-lg hover:shadow-[#E82127]/10 hover:-translate-y-1' : ''}
        ${className}
      `}
    >
      {children}
    </div>
  );
};
