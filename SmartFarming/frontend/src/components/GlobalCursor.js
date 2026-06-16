import { useEffect, useRef } from 'react';

const GlobalCursor = () => {
  const cursorRef = useRef(null);

  useEffect(() => {
    // Create cursor element
    const cursor = document.createElement('div');
    cursor.className = 'global-cursor';
    document.body.appendChild(cursor);
    cursorRef.current = cursor;

    let lastTime = 0;

    const createTrail = (x, y) => {
      const trail = document.createElement('div');
      trail.className = 'global-trail';
      trail.style.left = x + 'px';
      trail.style.top = y + 'px';
      document.body.appendChild(trail);

      requestAnimationFrame(() => {
        trail.style.opacity = '0';
        trail.style.transform = 'translate(-50%, -50%) scale(0) rotate(180deg)';
      });

      setTimeout(() => {
        if (trail.parentNode) trail.parentNode.removeChild(trail);
      }, 700);
    };

    const handleMouseMove = (e) => {
      cursor.style.left = e.clientX + 'px';
      cursor.style.top = e.clientY + 'px';

      const now = Date.now();
      if (now - lastTime > 50) {
        createTrail(e.clientX, e.clientY);
        lastTime = now;
      }
    };

    const handleMouseDown = () => {
      cursor.classList.add('clicking');
    };

    const handleMouseUp = () => {
      cursor.classList.remove('clicking');
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mouseup', handleMouseUp);
      if (cursor.parentNode) cursor.parentNode.removeChild(cursor);
      document.querySelectorAll('.global-trail').forEach(t => t.remove());
    };
  }, []);

  return null;
};

export default GlobalCursor;
