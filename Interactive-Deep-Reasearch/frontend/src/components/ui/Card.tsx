import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../utils/cn';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'glass' | 'elevated';
  hoverable?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  variant = 'default',
  hoverable = false,
}) => {
  const baseClasses = "rounded-2xl border transition-all duration-300";
  
  const variants = {
    default: "bg-apple-card border-apple-gray-200/50 shadow-apple",
    glass: "bg-white/70 backdrop-blur-xl border-white/20 shadow-glass",
    elevated: "bg-apple-card border-apple-gray-200/50 shadow-apple-lg"
  };

  const hoverClasses = hoverable ? "hover:shadow-apple-lg hover:scale-[1.02] cursor-pointer" : "";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(
        baseClasses,
        variants[variant],
        hoverClasses,
        className
      )}
    >
      {children}
    </motion.div>
  );
};
