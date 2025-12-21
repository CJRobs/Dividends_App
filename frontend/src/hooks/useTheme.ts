'use client';

import { useState, useEffect } from 'react';

/**
 * Hook to detect if dark mode is active
 * Listens for class changes on the document element
 */
export function useIsDark(): boolean {
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    // Initial check
    const checkDark = () => {
      setIsDark(document.documentElement.classList.contains('dark'));
    };

    checkDark();

    // Listen for class changes on html element
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === 'class') {
          checkDark();
        }
      });
    });

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class'],
    });

    return () => observer.disconnect();
  }, []);

  return isDark;
}
