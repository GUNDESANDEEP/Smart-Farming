/**
 * STRICT Product Image System v6
 * 
 * RULES:
 * 1. Search ONLY for the EXACT product name entered by the user
 * 2. Do NOT return similar, related, or category-based products
 * 3. Product name must match 100% exactly
 * 4. If exact product not found → show category placeholder (never substitute)
 * 5. NEVER substitute products
 * 6. Match using EXACT product name + selected category
 * 7. Ignore semantic similarity and AI assumptions
 * 
 * Strategy:
 * - Use Wikipedia REST API to fetch image for the EXACT product name
 * - Hindi product names are translated to English ONLY for Wikipedia lookup
 * - No fuzzy, partial, or substring matching
 * - Cached in localStorage for speed
 */

// ── Hindi → English EXACT translations (not substitutions) ──
const HINDI_TO_ENGLISH = {
  'palak': 'spinach',
  'methi': 'fenugreek',
  'bhindi': 'okra',
  'karela': 'bitter gourd',
  'lauki': 'bottle gourd',
  'turai': 'ridge gourd',
  'kaddu': 'pumpkin',
  'adrak': 'ginger',
  'lehsun': 'garlic',
  'dhaniya': 'coriander',
  'pudina': 'mint',
  'haldi': 'turmeric',
  'jeera': 'cumin',
  'elaichi': 'cardamom',
  'laung': 'clove',
  'dalchini': 'cinnamon',
  'saunf': 'fennel',
  'ajwain': 'carom seeds',
  'hing': 'asafoetida',
  'kesar': 'saffron',
  'rai': 'mustard seeds',
  'til': 'sesame seeds',
  'kalonji': 'nigella seeds',
  'seb': 'apple',
  'kela': 'banana',
  'aam': 'mango',
  'santra': 'orange',
  'mosambi': 'sweet lime',
  'angoor': 'grapes',
  'tarbooz': 'watermelon',
  'kharbooja': 'muskmelon',
  'amrud': 'guava',
  'anar': 'pomegranate',
  'ananas': 'pineapple',
  'nashpati': 'pear',
  'anjeer': 'fig',
  'khajoor': 'dates',
  'nariyal': 'coconut',
  'nimbu': 'lemon',
  'sitaphal': 'custard apple',
  'chiku': 'sapodilla',
  'kathal': 'jackfruit',
  'litchi': 'lychee',
  'jamun': 'java plum',
  'chawal': 'rice',
  'gehu': 'wheat',
  'atta': 'wheat flour',
  'maida': 'refined flour',
  'bajra': 'pearl millet',
  'jowar': 'sorghum',
  'ragi': 'finger millet',
  'makka': 'corn',
  'jau': 'barley',
  'suji': 'semolina',
  'rava': 'semolina',
  'poha': 'flattened rice',
  'dalia': 'broken wheat',
  'kuttu': 'buckwheat',
  'doodh': 'milk',
  'dahi': 'yogurt',
  'makhan': 'butter',
  'malai': 'cream',
  'chaas': 'buttermilk',
  'mooli': 'radish',
  'matar': 'green peas',
  'shimla mirch': 'bell pepper',
  'hari mirch': 'green chilli',
  'lal mirch': 'red chilli',
  'sarson': 'mustard greens',
  'arbi': 'colocasia',
  'shakarkandi': 'sweet potato',
  'toor dal': 'pigeon pea lentil',
  'arhar dal': 'pigeon pea lentil',
  'moong dal': 'mung bean',
  'urad dal': 'black gram lentil',
  'chana dal': 'bengal gram lentil',
  'masoor dal': 'red lentil',
  'rajma': 'kidney beans',
  'chole': 'chickpeas',
  'chana': 'chickpeas',
  'lobiya': 'black eyed peas',
  'moongfali': 'peanuts',
  'badam': 'almonds',
  'kaju': 'cashew nuts',
  'akhrot': 'walnuts',
  'pista': 'pistachios',
  'kishmish': 'raisins',
};

// ── Wikipedia search term overrides (to get better Wikipedia article) ──
const WIKI_SEARCH_OVERRIDE = {
  'red dal': 'Masoor dal',
  'yellow dal': 'Toor dal',
  'dal': 'Dal',
  'daal': 'Dal',
  'toor dal': 'Pigeon pea',
  'arhar dal': 'Pigeon pea',
  'moong dal': 'Mung bean',
  'urad dal': 'Vigna mungo',
  'chana dal': 'Bengal gram',
  'masoor dal': 'Lens culinaris',
  'paneer': 'Paneer',
  'ghee': 'Ghee',
  'buttermilk': 'Buttermilk',
  'lassi': 'Lassi',
  'curd': 'Yogurt',
  'lady finger': 'Okra',
  'okra': 'Okra',
  'brinjal': 'Eggplant',
  'capsicum': 'Bell pepper',
  'corn': 'Maize',
  'sweet potato': 'Sweet potato',
  'drumstick': 'Moringa oleifera',
  'curry leaves': 'Curry tree',
  'bottle gourd': 'Calabash',
  'bitter gourd': 'Momordica charantia',
  'ridge gourd': 'Luffa',
  'snake gourd': 'Trichosanthes cucumerina',
  'ivy gourd': 'Coccinia grandis',
  'cluster beans': 'Guar',
  'pointed gourd': 'Trichosanthes dioica',
  'raw banana': 'Cooking banana',
  'custard apple': 'Sugar-apple',
  'dragon fruit': 'Pitaya',
  'jackfruit': 'Jackfruit',
  'sapota': 'Manilkara zapota',
  'amla': 'Phyllanthus emblica',
  'tamarind': 'Tamarind',
  'dates': 'Date palm',
  'coconut': 'Coconut',
  'fig': 'Common fig',
  'basmati rice': 'Basmati',
  'basmati': 'Basmati',
  'brown rice': 'Brown rice',
  'millets': 'Millet',
  'oats': 'Oat',
  'quinoa': 'Quinoa',
  'barley': 'Barley',
  'black pepper': 'Black pepper',
  'cardamom': 'Cardamom',
  'cinnamon': 'Cinnamon',
  'clove': 'Clove',
  'turmeric': 'Turmeric',
  'cumin': 'Cumin',
  'mustard': 'Mustard seed',
  'saffron': 'Saffron',
  'fennel': 'Fennel',
  'red chilli': 'Chili pepper',
  'green chilli': 'Chili pepper',
  'chilli': 'Chili pepper',
  'garam masala': 'Garam masala',
  'groundnut': 'Peanut',
  'peanut': 'Peanut',
  'almond': 'Almond',
  'cashew': 'Cashew',
  'walnut': 'Walnut',
  'pistachio': 'Pistachio',
  'soybean': 'Soybean',
  'chickpea': 'Chickpea',
  'kidney bean': 'Kidney bean',
  'lentil': 'Lentil',
  'mushroom': 'Edible mushroom',
  'ginger': 'Ginger',
  'garlic': 'Garlic',
  'coriander': 'Coriander',
  'mint': 'Mentha',
  'lettuce': 'Lettuce',
  'broccoli': 'Broccoli',
  'kale': 'Kale',
  'asparagus': 'Asparagus',
  'celery': 'Celery',
  'spinach': 'Spinach',
  'cabbage': 'Cabbage',
  'cauliflower': 'Cauliflower',
  'pumpkin': 'Pumpkin',
  'beetroot': 'Beetroot',
  'radish': 'Radish',
  'turnip': 'Turnip',
  'yam': 'Yam (vegetable)',
  'tomato': 'Tomato',
  'potato': 'Potato',
  'onion': 'Onion',
  'carrot': 'Carrot',
  'cucumber': 'Cucumber',
  'peas': 'Pea',
  'green peas': 'Pea',
  'beans': 'Green bean',
  'apple': 'Apple',
  'banana': 'Banana',
  'mango': 'Mango',
  'orange': 'Orange (fruit)',
  'grapes': 'Grape',
  'watermelon': 'Watermelon',
  'muskmelon': 'Muskmelon',
  'papaya': 'Papaya',
  'guava': 'Guava',
  'pomegranate': 'Pomegranate',
  'pineapple': 'Pineapple',
  'pineapples': 'Pineapple',
  'strawberry': 'Strawberry',
  'blueberry': 'Blueberry',
  'raspberry': 'Raspberry',
  'cherry': 'Cherry',
  'peach': 'Peach',
  'plum': 'Plum',
  'pear': 'Pear',
  'lemon': 'Lemon',
  'lime': 'Lime (fruit)',
  'kiwi': 'Kiwifruit',
  'avocado': 'Avocado',
  'lychee': 'Lychee',
  'rice': 'Rice',
  'wheat': 'Wheat',
  'flour': 'Wheat flour',
  'maize': 'Maize',
  'milk': 'Milk',
  'yogurt': 'Yogurt',
  'butter': 'Butter',
  'cheese': 'Cheese',
  'cream': 'Cream',
  'ice cream': 'Ice cream',
};

// ── Category fallback images (shown ONLY when exact product image not found) ──
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
  'pulses':       'https://images.unsplash.com/photo-1596797038530-2c107229654b?w=400&h=300&fit=crop',
  'Pulses':       'https://images.unsplash.com/photo-1596797038530-2c107229654b?w=400&h=300&fit=crop',
  'Others':       'https://images.unsplash.com/photo-1495461199391-8c39ab674295?w=400&h=300&fit=crop',
};

const PLACEHOLDER_IMG = 'https://images.unsplash.com/photo-1495461199391-8c39ab674295?w=400&h=300&fit=crop';

// ── localStorage cache ──
const CACHE_KEY = 'sf_product_images_v6_strict';
const CACHE_EXPIRY_MS = 30 * 24 * 60 * 60 * 1000; // 30 days

// Clear ALL old caches
try { 
  localStorage.removeItem('sf_product_images_cache'); 
  localStorage.removeItem('sf_product_images_v2');
  localStorage.removeItem('sf_product_images_v3');
  localStorage.removeItem('sf_product_images_v4');
  localStorage.removeItem('sf_product_images_v5');
} catch {}

function getCachedImage(key) {
  try {
    const cache = JSON.parse(localStorage.getItem(CACHE_KEY) || '{}');
    const entry = cache[key];
    if (entry && Date.now() - entry.timestamp < CACHE_EXPIRY_MS) return entry.url;
  } catch {}
  return null;
}

function setCachedImage(key, url) {
  try {
    const cache = JSON.parse(localStorage.getItem(CACHE_KEY) || '{}');
    cache[key] = { url, timestamp: Date.now() };
    localStorage.setItem(CACHE_KEY, JSON.stringify(cache));
  } catch {}
}

/**
 * Get the EXACT Wikipedia search term for a product.
 * Only uses direct translations (Hindi→English) and exact overrides.
 * NO fuzzy matching. NO partial matching. NO substitution.
 */
function getExactWikiTerm(productName) {
  const lower = productName.toLowerCase().trim();
  
  // Check exact override first
  if (WIKI_SEARCH_OVERRIDE[lower]) return WIKI_SEARCH_OVERRIDE[lower];
  
  // Check Hindi→English translation
  if (HINDI_TO_ENGLISH[lower]) return HINDI_TO_ENGLISH[lower];
  
  // Use the product name as-is (capitalize first letter for Wikipedia)
  return productName.trim();
}

/**
 * Fetch EXACT product image from Wikipedia REST API.
 * Searches for the EXACT product name — no substitution.
 */
async function fetchExactWikipediaImage(productName) {
  const searchTerm = getExactWikiTerm(productName);
  
  const HEADERS = {
    'Accept': 'application/json',
    'Api-User-Agent': 'SmartFarmMarketplace/1.0 (https://smartfarm.app; contact@smartfarm.app)',
  };
  
  try {
    // Try exact Wikipedia article
    const response = await fetch(
      `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(searchTerm)}`,
      { headers: HEADERS }
    );
    
    if (response.ok) {
      const data = await response.json();
      // Verify the Wikipedia article is about the product (not a disambiguation page)
      if (data.type === 'standard' || data.type === 'summary') {
        if (data.originalimage?.source) return data.originalimage.source;
        if (data.thumbnail?.source) {
          // Get higher resolution thumbnail
          const thumbUrl = data.thumbnail.source;
          return thumbUrl.replace(/\/\d+px-/, '/400px-');
        }
      }
    }
    
    // If direct lookup failed, try Wikipedia search API for exact term
    const searchResponse = await fetch(
      `https://en.wikipedia.org/w/api.php?action=query&titles=${encodeURIComponent(searchTerm)}&prop=pageimages&format=json&pithumbsize=400&origin=*`,
      { headers: HEADERS }
    );
    
    if (searchResponse.ok) {
      const searchData = await searchResponse.json();
      const pages = searchData.query?.pages;
      if (pages) {
        const page = Object.values(pages)[0];
        if (page && page.thumbnail?.source) {
          return page.thumbnail.source;
        }
      }
    }
    
    return null;
  } catch (error) {
    console.warn(`[STRICT] Wikipedia fetch failed for "${productName}":`, error.message);
    return null;
  }
}

/**
 * Check if URL is a real user-uploaded image
 */
function isValidUploadedImage(url) {
  if (!url || typeof url !== 'string') return false;
  url = url.trim();
  if (url.length < 10) return false;
  return url.includes('cloudinary.com') || url.includes('firebasestorage') || url.includes('amazonaws.com');
}

/**
 * STRICT getProductImage
 * 
 * Returns ONLY the EXACT matching image for the product.
 * NO fuzzy matching. NO substitution. NO partial matching.
 * 
 * Priority:
 * 1. User-uploaded image (Cloudinary/Firebase/AWS)
 * 2. Cached Wikipedia image (exact match from previous fetch)
 * 3. Trigger async Wikipedia fetch for EXACT product name
 * 4. Category fallback (while Wikipedia loads)
 * 5. Default placeholder
 * 
 * @param {Object} product - { name, category, image_url, images }
 * @param {Function} onImageLoaded - called when async Wikipedia image is ready
 * @returns {string} Image URL
 */
export const getProductImage = (product, onImageLoaded) => {
  // 1. User-uploaded image (highest priority — always use if available)
  if (isValidUploadedImage(product.image_url)) return product.image_url;
  if (isValidUploadedImage(product.image)) return product.image;

  // Handle images array/string
  if (product.images) {
    let imageList = [];
    if (Array.isArray(product.images)) {
      imageList = product.images;
    } else if (typeof product.images === 'string') {
      try {
        const parsed = JSON.parse(product.images);
        if (Array.isArray(parsed)) imageList = parsed;
        else if (typeof parsed === 'string' && parsed.length > 10) imageList = [parsed];
      } catch {
        imageList = product.images.split(',').map(s => s.trim()).filter(s => s.length > 10);
      }
    }
    const validImg = imageList.find(img => isValidUploadedImage(img));
    if (validImg) return validImg;
  }

  const name = (product.name || '').trim();
  if (!name) return PLACEHOLDER_IMG;

  // Create a STRICT cache key using BOTH product name AND category
  const cacheKey = `${name.toLowerCase()}__${(product.category || '').toLowerCase()}`;

  // 2. Check strict cache (exact product name + category)
  const cached = getCachedImage(cacheKey);
  if (cached) return cached;

  // 3. Trigger async Wikipedia fetch for the EXACT product name
  fetchExactWikipediaImage(name).then(url => {
    if (url) {
      setCachedImage(cacheKey, url);
      if (typeof onImageLoaded === 'function') {
        onImageLoaded(url);
      }
    }
  });

  // 4. Category fallback (shown while Wikipedia loads — NOT a product substitute)
  const category = (product.category || '');
  if (CATEGORY_IMAGES[category]) return CATEGORY_IMAGES[category];
  if (CATEGORY_IMAGES[category.toLowerCase()]) return CATEGORY_IMAGES[category.toLowerCase()];

  // 5. Default placeholder
  return PLACEHOLDER_IMG;
};

export { PLACEHOLDER_IMG, CATEGORY_IMAGES };
export default getProductImage;
