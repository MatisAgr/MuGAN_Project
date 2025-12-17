"use client";
import React from "react";
import { motion } from "motion/react";
import { Link } from "react-router-dom";



const transition = {
  type: "spring" as const,
  mass: 0.5,
  damping: 11.5,
  stiffness: 100,
  restDelta: 0.001,
  restSpeed: 0.001,
};

export const MenuItem = ({
  setActive,
  active,
  item,
  icon,
  children,
}: {
  setActive: (item: string) => void;
  active: string | null;
  item: string;
  icon?: React.ReactNode;
  children?: React.ReactNode;
}) => {
  return (
    <div onMouseEnter={() => setActive(item)} className="relative">
      <motion.div
        transition={{ duration: 0.3 }}
        className="cursor-pointer text-sm font-medium text-white hover:text-purple-300 transition-colors flex items-center gap-2"
      >
        {icon}
        {item}
      </motion.div>
      {active !== null && (
        <motion.div
          initial={{ opacity: 0, scale: 0.85, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={transition}
          onMouseEnter={() => setActive(item)}
        >
          {active === item && (
            <div className="absolute top-[calc(100%_+_0.5rem)] left-1/2 transform -translate-x-1/2">
              <div className="h-4 w-full" />
              <motion.div
                transition={transition}
                layoutId="active"
                className="bg-slate-900/95 backdrop-blur-xl rounded-2xl overflow-hidden border border-purple-500/30 shadow-2xl"
              >
                <motion.div
                  layout
                  className="w-max h-full p-4"
                >
                  {children}
                </motion.div>
              </motion.div>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
};

export const Menu = ({
  setActive,
  children,
}: {
  setActive: (item: string | null) => void;
  children: React.ReactNode;
}) => {
  return (
    <nav
      onMouseLeave={() => setActive(null)}
      className="relative rounded-full border border-purple-500/30 bg-gradient-to-r from-slate-900/95 via-indigo-950/95 to-purple-950/95 backdrop-blur-xl shadow-2xl flex justify-center space-x-6 px-10 py-4"
    >
      {children}
    </nav>
  );
};

export const ProductItem = ({
  title,
  description,
  href,
  src,
  icon,
}: {
  title: string;
  description: string;
  href: string;
  src: string;
  icon?: React.ReactNode;
}) => {
  return (
    <Link to={href} className="flex space-x-3 group cursor-pointer hover:bg-slate-800/50 p-3 rounded-lg transition-all">
      <img
        src={src}
        width={140}
        height={70}
        alt={title}
        className="shrink-0 rounded-lg shadow-xl object-cover border border-purple-500/20 group-hover:border-purple-500/40 transition-all"
      />
      <div>
        <h4 className="text-base font-bold mb-2 text-white group-hover:text-purple-300 transition-colors flex items-center gap-2">
          {icon}
          {title}
        </h4>
        <p className="text-neutral-400 text-sm max-w-[12rem] leading-relaxed">
          {description}
        </p>
      </div>
    </Link>
  );
};

export const HoveredLink = ({ children, href, ...rest }: any) => {
  return (
    <Link
      to={href}
      {...rest}
      className="text-white hover:text-purple-300 transition-colors font-medium"
    >
      {children}
    </Link>
  );
};
