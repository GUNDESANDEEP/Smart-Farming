import { useEffect, useRef } from 'react';

const GlobalCursor = () => {
  const cursorRef = useRef(null);
  const poolRef = useRef([]);
  const poolIndex = useRef(0);

  useEffect(() => {
    // Create cursor element
    const cursor = document.createElement('div');
    cursor.className = 'global-cursor';
    document.body.appendChild(cursor);
    cursorRef.current = cursor;

    // Pre-create a pool of trail elements instead of creating/destroying on every move
    const POOL_SIZE = 8;
    for (let i = 0; i < POOL_SIZE; i++) {
      const trail = document.createElement('div');
      trail.className = 'global-trail';
      trail.style.opacity = '0';
      document.body.appendChild(trail);
      poolRef.current.push(trail);
    }

    let lastTime = 0;

    const handleMouseMove = (e) => {
      cursor.style.left = e.clientX + 'px';
      cursor.style.top = e.clientY + 'px';

      const now = Date.now();
      if (now - lastTime > 80) {
        // Reuse trail from pool instead of creating new DOM elements
        const trail = poolRef.current[poolIndex.current % POOL_SIZE];
        poolIndex.current++;
        
        trail.style.left = e.clientX + 'px';
        trail.style.top = e.clientY + 'px';
        trail.style.opacity = '1';
        trail.style.transform = 'translate(-50%, -50%) scale(1) rotate(0deg)';

        requestAnimationFrame(() => {
          trail.style.opacity = '0';
          trail.style.transform = 'translate(-50%, -50%) scale(0) rotate(180deg)';
        });

        lastTime = now;
      }
    };

    const handleMouseDown = () => {
      cursor.classList.add('clicking');
    };

    const handleMouseUp = () => {
      cursor.classList.remove('clicking');
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    window.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mouseup', handleMouseUp);
      if (cursor.parentNode) cursor.parentNode.removeChild(cursor);
      poolRef.current.forEach(t => { if (t.parentNode) t.parentNode.removeChild(t); });
      poolRef.current = [];
    };
  }, []);

  return null;
};

export default GlobalCursor;
