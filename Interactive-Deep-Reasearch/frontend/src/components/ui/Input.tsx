import React from 'react';
import { cn } from '../../utils/cn';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  leftIcon,
  rightIcon,
  className,
  ...props
}) => {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-apple-text mb-2">
          {label}
        </label>
      )}
      <div className="relative">
        {leftIcon && (
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-apple-secondary">
            {leftIcon}
          </div>
        )}
        <input
          className={cn(
            "w-full px-4 py-3 rounded-xl border border-apple-gray-300 bg-apple-card",
            "focus:outline-none focus:ring-2 focus:ring-apple-blue/20 focus:border-apple-blue",
            "transition-all duration-200 placeholder-apple-secondary",
            leftIcon && "pl-10",
            rightIcon && "pr-10",
            error && "border-apple-red focus:ring-apple-red/20 focus:border-apple-red",
            className
          )}
          {...props}
        />
        {rightIcon && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-apple-secondary">
            {rightIcon}
          </div>
        )}
      </div>
      {error && (
        <p className="mt-1 text-sm text-apple-red">{error}</p>
      )}
    </div>
  );
};
