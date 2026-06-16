/**
 * Smart Product Image Resolver
 * Maps product names to accurate, high-quality Unsplash images.
 * Covers 80+ Indian agricultural products across all categories.
 */

// ── Exact product name → curated Unsplash photo ID mapping ──
const PRODUCT_IMAGES = {
  // 🥭 FRUITS
  'mango':        'https://images.unsplash.com/photo-1553279768-865429fa0078?w=400&h=300&fit=crop',
  'banana':       'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=400&h=300&fit=crop',
  'apple':        'https://images.unsplash.com/photo-1568702846914-96b305d2ead1?w=400&h=300&fit=crop',
  'orange':       'https://images.unsplash.com/photo-1547514701-42782101795e?w=400&h=300&fit=crop',
  'grapes':       'https://images.unsplash.com/photo-1537640538966-79f369143f8f?w=400&h=300&fit=crop',
  'grape':        'https://images.unsplash.com/photo-1537640538966-79f369143f8f?w=400&h=300&fit=crop',
  'watermelon':   'https://images.unsplash.com/photo-1589984662646-e7b2e4f907cd?w=400&h=300&fit=crop',
  'papaya':       'https://images.unsplash.com/photo-1517282009859-f000ec3b26fe?w=400&h=300&fit=crop',
  'guava':        'https://images.unsplash.com/photo-1536511132770-e5058c7e8c46?w=400&h=300&fit=crop',
  'gova':         'https://images.unsplash.com/photo-1536511132770-e5058c7e8c46?w=400&h=300&fit=crop',
  'pomegranate':  'https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=400&h=300&fit=crop',
  'pineapple':    'https://images.unsplash.com/photo-1550258987-190a2d41a8ba?w=400&h=300&fit=crop',
  'coconut':      'https://images.unsplash.com/photo-1560769629-975ec94e6a86?w=400&h=300&fit=crop',
  'lemon':        'https://images.unsplash.com/photo-1590502593747-42a996133562?w=400&h=300&fit=crop',
  'lime':         'https://images.unsplash.com/photo-1590502593747-42a996133562?w=400&h=300&fit=crop',
  'strawberry':   'https://images.unsplash.com/photo-1464965911861-746a04b4bca6?w=400&h=300&fit=crop',
  'cherry':       'https://images.unsplash.com/photo-1528821128474-27f963b062bf?w=400&h=300&fit=crop',
  'kiwi':         'https://images.unsplash.com/photo-1585059895524-72f83aca6510?w=400&h=300&fit=crop',
  'jackfruit':    'https://images.unsplash.com/photo-1528825871115-3581a5e31138?w=400&h=300&fit=crop',
  'custard apple':'https://images.unsplash.com/photo-1600577916048-804c9191e36c?w=400&h=300&fit=crop',
  'sapota':       'https://images.unsplash.com/photo-1600577916048-804c9191e36c?w=400&h=300&fit=crop',
  'chikoo':       'https://images.unsplash.com/photo-1600577916048-804c9191e36c?w=400&h=300&fit=crop',
  'fig':          'https://images.unsplash.com/photo-1601379760883-1bb497c558e0?w=400&h=300&fit=crop',
  'dates':        'https://images.unsplash.com/photo-1593882320784-e4e8b1c1d669?w=400&h=300&fit=crop',
  'litchi':       'https://images.unsplash.com/photo-1558818498-28c1e002b655?w=400&h=300&fit=crop',
  'lychee':       'https://images.unsplash.com/photo-1558818498-28c1e002b655?w=400&h=300&fit=crop',
  'peach':        'https://images.unsplash.com/photo-1629828874514-c1daa25e1b5c?w=400&h=300&fit=crop',
  'plum':         'https://images.unsplash.com/photo-1502666865024-e96fad581049?w=400&h=300&fit=crop',
  'pear':         'https://images.unsplash.com/photo-1514756331096-242fdeb70d4a?w=400&h=300&fit=crop',
  'dragon fruit': 'https://images.unsplash.com/photo-1527325678964-54921661f888?w=400&h=300&fit=crop',
  'avocado':      'https://images.unsplash.com/photo-1523049673857-eb18f1d7b578?w=400&h=300&fit=crop',

  // 🥬 VEGETABLES
  'tomato':       'https://images.unsplash.com/photo-1546470427-0d4db154ceb8?w=400&h=300&fit=crop',
  'potato':       'https://images.unsplash.com/photo-1518977676601-b53f82afe204?w=400&h=300&fit=crop',
  'onion':        'https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?w=400&h=300&fit=crop',
  'carrot':       'https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?w=400&h=300&fit=crop',
  'cabbage':      'https://images.unsplash.com/photo-1594282486552-05b4d80fbb9f?w=400&h=300&fit=crop',
  'cauliflower':  'https://images.unsplash.com/photo-1568702846914-96b305d2ead1?w=400&h=300&fit=crop',
  'brinjal':      'https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=400&h=300&fit=crop',
  'eggplant':     'https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=400&h=300&fit=crop',
  'capsicum':     'https://images.unsplash.com/photo-1563565375-f3fdfdbefa83?w=400&h=300&fit=crop',
  'bell pepper':  'https://images.unsplash.com/photo-1563565375-f3fdfdbefa83?w=400&h=300&fit=crop',
  'green pepper': 'https://images.unsplash.com/photo-1563565375-f3fdfdbefa83?w=400&h=300&fit=crop',
  'spinach':      'https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=400&h=300&fit=crop',
  'palak':        'https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=400&h=300&fit=crop',
  'methi':        'https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=400&h=300&fit=crop',
  'beans':        'https://images.unsplash.com/photo-1567375698348-5d9d5ae10c3c?w=400&h=300&fit=crop',
  'green beans':  'https://images.unsplash.com/photo-1567375698348-5d9d5ae10c3c?w=400&h=300&fit=crop',
  'peas':         'https://images.unsplash.com/photo-1587735243615-c03f25aaff15?w=400&h=300&fit=crop',
  'green peas':   'https://images.unsplash.com/photo-1587735243615-c03f25aaff15?w=400&h=300&fit=crop',
  'cucumber':     'https://images.unsplash.com/photo-1449300079323-02e209d9d3a6?w=400&h=300&fit=crop',
  'bitter gourd': 'https://images.unsplash.com/photo-1607305387299-a3d9611cd469?w=400&h=300&fit=crop',
  'karela':       'https://images.unsplash.com/photo-1607305387299-a3d9611cd469?w=400&h=300&fit=crop',
  'bottle gourd': 'https://images.unsplash.com/photo-1622921491193-345c3402b14c?w=400&h=300&fit=crop',
  'lauki':        'https://images.unsplash.com/photo-1622921491193-345c3402b14c?w=400&h=300&fit=crop',
  'ridge gourd':  'https://images.unsplash.com/photo-1622921491193-345c3402b14c?w=400&h=300&fit=crop',
  'pumpkin':      'https://images.unsplash.com/photo-1570586437263-ab629fccc818?w=400&h=300&fit=crop',
  'lady finger':  'https://images.unsplash.com/photo-1425543103986-22abb7d7e8d2?w=400&h=300&fit=crop',
  'okra':         'https://images.unsplash.com/photo-1425543103986-22abb7d7e8d2?w=400&h=300&fit=crop',
  'bhindi':       'https://images.unsplash.com/photo-1425543103986-22abb7d7e8d2?w=400&h=300&fit=crop',
  'radish':       'https://images.unsplash.com/photo-1447175008436-054170c2e979?w=400&h=300&fit=crop',
  'beetroot':     'https://images.unsplash.com/photo-1593105544559-ecb03bf76f82?w=400&h=300&fit=crop',
  'mushroom':     'https://images.unsplash.com/photo-1504545102780-26774c1bb073?w=400&h=300&fit=crop',
  'corn':         'https://images.unsplash.com/photo-1551754655-cd27e38d2076?w=400&h=300&fit=crop',
  'sweet corn':   'https://images.unsplash.com/photo-1551754655-cd27e38d2076?w=400&h=300&fit=crop',
  'sweet potato': 'https://images.unsplash.com/photo-1596097635092-6d8e3c9b6e2c?w=400&h=300&fit=crop',
  'broccoli':     'https://images.unsplash.com/photo-1459411552884-841db9b3cc2a?w=400&h=300&fit=crop',
  'lettuce':      'https://images.unsplash.com/photo-1622206151226-18ca2c9ab4a1?w=400&h=300&fit=crop',
  'ginger':       'https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=400&h=300&fit=crop',
  'garlic':       'https://images.unsplash.com/photo-1540148426945-6cf22a6b2571?w=400&h=300&fit=crop',
  'drumstick':    'https://images.unsplash.com/photo-1567375698348-5d9d5ae10c3c?w=400&h=300&fit=crop',

  // 🌾 GRAINS & CEREALS
  'rice':         'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=400&h=300&fit=crop',
  'wheat':        'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=400&h=300&fit=crop',
  'maize':        'https://images.unsplash.com/photo-1551754655-cd27e38d2076?w=400&h=300&fit=crop',
  'bajra':        'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=400&h=300&fit=crop',
  'jowar':        'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=400&h=300&fit=crop',
  'ragi':         'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=400&h=300&fit=crop',
  'oats':         'https://images.unsplash.com/photo-1614961233913-a5113a4a34ed?w=400&h=300&fit=crop',
  'barley':       'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=400&h=300&fit=crop',

  // 🫘 PULSES & LENTILS
  'dal':          'https://images.unsplash.com/photo-1515543904413-63b3b6a12977?w=400&h=300&fit=crop',
  'toor dal':     'https://images.unsplash.com/photo-1515543904413-63b3b6a12977?w=400&h=300&fit=crop',
  'moong dal':    'https://images.unsplash.com/photo-1515543904413-63b3b6a12977?w=400&h=300&fit=crop',
  'chana dal':    'https://images.unsplash.com/photo-1515543904413-63b3b6a12977?w=400&h=300&fit=crop',
  'urad dal':     'https://images.unsplash.com/photo-1515543904413-63b3b6a12977?w=400&h=300&fit=crop',
  'rajma':        'https://images.unsplash.com/photo-1515543904413-63b3b6a12977?w=400&h=300&fit=crop',
  'chickpea':     'https://images.unsplash.com/photo-1515543904413-63b3b6a12977?w=400&h=300&fit=crop',
  'chana':        'https://images.unsplash.com/photo-1515543904413-63b3b6a12977?w=400&h=300&fit=crop',
  'soybean':      'https://images.unsplash.com/photo-1515543904413-63b3b6a12977?w=400&h=300&fit=crop',
  'groundnut':    'https://images.unsplash.com/photo-1567892320421-1c657571ea4e?w=400&h=300&fit=crop',
  'peanut':       'https://images.unsplash.com/photo-1567892320421-1c657571ea4e?w=400&h=300&fit=crop',

  // 🥛 DAIRY
  'milk':         'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=400&h=300&fit=crop',
  'curd':         'https://images.unsplash.com/photo-1488477181946-6428a0291777?w=400&h=300&fit=crop',
  'yogurt':       'https://images.unsplash.com/photo-1488477181946-6428a0291777?w=400&h=300&fit=crop',
  'butter':       'https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?w=400&h=300&fit=crop',
  'ghee':         'https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?w=400&h=300&fit=crop',
  'paneer':       'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=400&h=300&fit=crop',
  'cheese':       'https://images.unsplash.com/photo-1486297678162-eb2a19b0a32d?w=400&h=300&fit=crop',
  'cream':        'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=400&h=300&fit=crop',
  'egg':          'https://images.unsplash.com/photo-1518569656558-1f25e69d93d7?w=400&h=300&fit=crop',
  'eggs':         'https://images.unsplash.com/photo-1518569656558-1f25e69d93d7?w=400&h=300&fit=crop',
  'honey':        'https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=400&h=300&fit=crop',

  // 🌶️ SPICES
  'chili':        'https://images.unsplash.com/photo-1588252303782-cb80119abd6c?w=400&h=300&fit=crop',
  'chilli':       'https://images.unsplash.com/photo-1588252303782-cb80119abd6c?w=400&h=300&fit=crop',
  'red chili':    'https://images.unsplash.com/photo-1588252303782-cb80119abd6c?w=400&h=300&fit=crop',
  'green chili':  'https://images.unsplash.com/photo-1526346698789-22fd84314424?w=400&h=300&fit=crop',
  'turmeric':     'https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=400&h=300&fit=crop',
  'haldi':        'https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=400&h=300&fit=crop',
  'cumin':        'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop',
  'jeera':        'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop',
  'coriander':    'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop',
  'dhaniya':      'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop',
  'cardamom':     'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop',
  'elaichi':      'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop',
  'clove':        'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop',
  'pepper':       'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop',
  'black pepper': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop',
  'mustard':      'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop',
  'cinnamon':     'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop',
  'saffron':      'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop',

  // 🌿 OTHERS
  'sugarcane':    'https://images.unsplash.com/photo-1558642452-9d2a7deb7f62?w=400&h=300&fit=crop',
  'jaggery':      'https://images.unsplash.com/photo-1558642452-9d2a7deb7f62?w=400&h=300&fit=crop',
  'tea':          'https://images.unsplash.com/photo-1556881286-fc6915169721?w=400&h=300&fit=crop',
  'coffee':       'https://images.unsplash.com/photo-1447933601403-56dc2973e209?w=400&h=300&fit=crop',
  'cotton':       'https://images.unsplash.com/photo-1594897030264-ab7d87efc473?w=400&h=300&fit=crop',
  'flower':       'https://images.unsplash.com/photo-1490750967868-88aa4f44baee?w=400&h=300&fit=crop',
  'rose':         'https://images.unsplash.com/photo-1490750967868-88aa4f44baee?w=400&h=300&fit=crop',
  'marigold':     'https://images.unsplash.com/photo-1490750967868-88aa4f44baee?w=400&h=300&fit=crop',
  'tulsi':        'https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=400&h=300&fit=crop',
  'aloe vera':    'https://images.unsplash.com/photo-1596547609652-9cf5d8c76921?w=400&h=300&fit=crop',
  'neem':         'https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=400&h=300&fit=crop',
};

// ── Category fallback images ──
const CATEGORY_IMAGES = {
  'vegetables':   'https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400&h=300&fit=crop',
  'Vegetables':   'https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400&h=300&fit=crop',
  'fruits':       'https://images.unsplash.com/photo-1619566636858-adf3ef46400b?w=400&h=300&fit=crop',
  'Fruits':       'https://images.unsplash.com/photo-1619566636858-adf3ef46400b?w=400&h=300&fit=crop',
  'grains':       'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=400&h=300&fit=crop',
  'Grains':       'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=400&h=300&fit=crop',
  'dairy':        'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=400&h=300&fit=crop',
  'Dairy':        'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=400&h=300&fit=crop',
  'spices':       'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop',
  'Spices':       'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop',
  'pulses':       'https://images.unsplash.com/photo-1515543904413-63b3b6a12977?w=400&h=300&fit=crop',
  'Pulses':       'https://images.unsplash.com/photo-1515543904413-63b3b6a12977?w=400&h=300&fit=crop',
  'Others':       'https://images.unsplash.com/photo-1542838132-92c53300491e?w=400&h=300&fit=crop',
};

const PLACEHOLDER_IMG = 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=400&h=300&fit=crop';

/**
 * Get the best matching image for a product.
 * Priority: uploaded image > exact name match > partial name match > category > fallback
 */
export const getProductImage = (product) => {
  // 1. Use uploaded/stored image if available
  if (product.image_url) return product.image_url;
  if (product.image) return product.image;
  if (product.images && typeof product.images === 'string' && product.images.length > 5) {
    return product.images.split(',')[0].trim();
  }
  if (Array.isArray(product.images) && product.images.length > 0) return product.images[0];

  // 2. Match by product name
  const name = (product.name || '').toLowerCase().trim();

  // Exact match
  if (PRODUCT_IMAGES[name]) return PRODUCT_IMAGES[name];

  // Partial match — check if any key is contained in the product name
  for (const [key, url] of Object.entries(PRODUCT_IMAGES)) {
    if (name.includes(key) || key.includes(name)) return url;
  }

  // Word-level match — check each word in the product name
  const words = name.split(/[\s\-_,]+/);
  for (const word of words) {
    if (word.length >= 3 && PRODUCT_IMAGES[word]) return PRODUCT_IMAGES[word];
  }

  // 3. Category fallback
  const category = (product.category || '').toLowerCase();
  if (CATEGORY_IMAGES[product.category]) return CATEGORY_IMAGES[product.category];
  if (CATEGORY_IMAGES[category]) return CATEGORY_IMAGES[category];

  // 4. Default placeholder
  return PLACEHOLDER_IMG;
};

export { PLACEHOLDER_IMG, PRODUCT_IMAGES, CATEGORY_IMAGES };
export default getProductImage;
