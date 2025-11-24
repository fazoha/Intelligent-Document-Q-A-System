"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactNode;
  side?: "top" | "bottom" | "left" | "right";
  className?: string;
}

export function Tooltip({ content, children, side = "top", className }: TooltipProps) {
  const [isVisible, setIsVisible] = React.useState(false);

  const positionClasses = {
    top: "-top-2 left-1/2 -translate-x-1/2 -translate-y-full mb-2",
    bottom: "-bottom-2 left-1/2 -translate-x-1/2 translate-y-full mt-2",
    left: "-left-2 top-1/2 -translate-y-1/2 -translate-x-full mr-2",
    right: "-right-2 top-1/2 -translate-y-1/2 translate-x-full ml-2",
  };

  return (
    <div 
      className="relative flex items-center justify-center group"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      <div
        className={cn(
          "absolute z-50 px-2 py-1 text-xs font-medium text-white bg-slate-900 rounded shadow-md whitespace-nowrap transition-all duration-200 pointer-events-none",
          positionClasses[side],
          isVisible ? "opacity-100 scale-100" : "opacity-0 scale-95",
          className
        )}
      >
        {content}
        {/* Arrow */}
        <div 
          className={cn(
            "absolute w-2 h-2 bg-slate-900 rotate-45",
            side === "top" && "bottom-[-4px] left-1/2 -translate-x-1/2",
            side === "bottom" && "top-[-4px] left-1/2 -translate-x-1/2",
            side === "left" && "right-[-4px] top-1/2 -translate-y-1/2",
            side === "right" && "left-[-4px] top-1/2 -translate-y-1/2",
          )}
        />
      </div>
    </div>
  );
}

