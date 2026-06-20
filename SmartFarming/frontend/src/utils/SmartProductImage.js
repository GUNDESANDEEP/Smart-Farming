/**
 * SmartProductImage Component
 * Renders a product image that automatically fetches the correct image
 * from Wikipedia based on the product name.
 * 
 * Shows category placeholder first, then swaps to the real image
 * once Wikipedia returns it (cached for future renders).
 */
import React, { useState, useEffect, useRef } from 'react';
import { getProductImage, PLACEHOLDER_IMG } from './productImages';

const SmartProductImage = ({ product, alt, style, className }) => {
  const [imgSrc, setImgSrc] = useState(PLACEHOLDER_IMG);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;

    // Get initial image (may be cached or category fallback)
    const initialSrc = getProductImage(product, (newUrl) => {
      // This callback fires when Wikipedia returns the real image
      if (mountedRef.current) {
        setImgSrc(newUrl);
      }
    });
    setImgSrc(initialSrc);

    return () => {
      mountedRef.current = false;
    };
  // Only re-run when product name changes
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [product?.name, product?.id, product?.image_url]);

  const handleError = () => {
    setImgSrc(PLACEHOLDER_IMG);
  };

  return (
    <img
      src={imgSrc}
      alt={alt || product?.name || 'Product'}
      onError={handleError}
      style={style}
      className={className}
      loading="lazy"
    />
  );
};

export default SmartProductImage;
