"""
AgriBot AI Routes - Gemini-powered farming assistant with offline fallback
Supports: Text chat (multi-language), Plant identification from images
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import json
import base64
import re

agribot_bp = Blueprint('agribot', __name__, url_prefix='/api/agribot')

GEMINI_API_KEY = 'AQ.Ab8RN6IEXR-bEe4Q3EmgD2eSYH65nSWdE9GFBA47GKNmOhKXBQ'

# Try to use google.generativeai SDK
genai = None
try:
    import google.generativeai as gai
    gai.configure(api_key=GEMINI_API_KEY)
    genai = gai
    print("[OK] Google Generative AI SDK loaded")
except Exception as e:
    print(f"[WARN] google-generativeai not available: {e}")

# Fallback: raw HTTP
import requests as http_requests

GEMINI_MODELS = ['gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-1.5-flash-latest']

def get_gemini_url(model):
    return f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}'

SYSTEM_PROMPT = {
    'en': """You are AgriBot, an expert AI farming assistant for Indian farmers. You help with:
- Plant/crop identification from photos
- Fertilizer recommendations
- Disease diagnosis
- Best farming practices
- Crop pricing and market trends
- Weather-based farming advice
Be concise, practical, and helpful. Use simple language. Include emojis for readability.""",
    'te': """మీరు AgriBot, భారతీయ రైతులకు నిపుణుడైన AI వ్యవసాయ సహాయకుడు. మీరు సహాయం చేస్తారు:
- ఫోటోల నుండి మొక్క/పంట గుర్తింపు
- ఎరువుల సిఫార్సులు
- వ్యాధి నిర్ధారణ
- ఉత్తమ వ్యవసాయ పద్ధతులు
తెలుగులో సమాధానం ఇవ్వండి. సరళమైన భాషను ఉపయోగించండి.""",
    'hi': """आप AgriBot हैं, भारतीय किसानों के लिए एक विशेषज्ञ AI कृषि सहायक। आप मदद करते हैं:
- फोटो से पौधे/फसल की पहचान
- उर्वरक सिफारिशें
- रोग निदान
- सर्वोत्तम कृषि पद्धतियां
हिंदी में जवाब दें। सरल भाषा का उपयोग करें।"""
}

# ════════════════════════════════════════════════════════════════════════
# Offline Knowledge Base - comprehensive farming info
# ════════════════════════════════════════════════════════════════════════
FARMING_KB = {
    'en': {
        'hello': '🌿 **Hello! I am AgriBot!**\n\nI am your AI farming assistant. Ask me about:\n🌾 Crops & farming tips\n🧪 Fertilizers & soil\n💊 Plant diseases\n💧 Irrigation\n📅 Seasonal advice\n💰 Market prices\n\nWhat would you like to know?',
        'hi': '🌿 **Hello! I am AgriBot!**\n\nI am your AI farming assistant. Ask me about:\n🌾 Crops & farming tips\n🧪 Fertilizers & soil\n💊 Plant diseases\n💧 Irrigation\n📅 Seasonal advice\n💰 Market prices\n\nWhat would you like to know?',
        'rice': '🌾 **Rice (Paddy) - Complete Guide**\n\n**Season:** Kharif (June-Nov)\n**Soil:** Clay loam, pH 5.5-6.5\n**Water:** Requires standing water 5-7cm\n\n🧪 **Fertilizers:**\n- Urea: 130 kg/acre\n- DAP: 60 kg/acre\n- Potash: 30 kg/acre\n\n⚠️ **Common Diseases:**\n- Blast: Use Tricyclazole\n- BLB: Use Streptocycline\n\n💰 **MSP:** ₹2,300/quintal\n**Yield:** 20-25 quintals/acre',
        'wheat': '🌾 **Wheat - Complete Guide**\n\n**Season:** Rabi (Oct-March)\n**Soil:** Loamy soil, pH 6.0-7.5\n**Temp:** 15-25°C ideal\n\n🧪 **Fertilizers:**\n- Urea: 130 kg/acre\n- DAP: 50 kg/acre\n- MOP: 25 kg/acre\n\n⚠️ **Common Diseases:**\n- Rust: Use Propiconazole\n- Karnal Bunt: Seed treatment\n\n💰 **MSP:** ₹2,275/quintal\n**Yield:** 18-22 quintals/acre',
        'tomato': '🍅 **Tomato - Complete Guide**\n\n**Season:** Year-round (Oct-Feb best)\n**Soil:** Well-drained loamy, pH 6.0-7.0\n**Spacing:** 60x45 cm\n\n🧪 **Fertilizers:**\n- NPK 19:19:19 at transplanting\n- Calcium Nitrate for fruit quality\n- Boron spray during flowering\n\n⚠️ **Common Diseases:**\n- Early Blight: Mancozeb spray\n- Leaf Curl: Control whitefly\n\n💰 **Market Price:** ₹15-60/kg\n**Yield:** 25-40 tons/hectare',
        'mango': '🥭 **Mango - Complete Guide**\n\n**Varieties:** Alphonso, Dasheri, Langra, Totapuri\n**Season:** Flowers Jan-Feb, Fruits Apr-Jul\n**Soil:** Deep well-drained, pH 5.5-7.5\n\n🧪 **Fertilizers:**\n- Age-based NPK: 1kg Urea + 0.5kg SSP per year of age\n- Micronutrients: Zinc, Boron spray\n\n⚠️ **Diseases:**\n- Anthracnose: Copper fungicide\n- Powdery Mildew: Sulphur spray\n\n💰 **Price:** ₹30-200/kg depending on variety',
        'fertilizer': '🧪 **Fertilizer Guide for Indian Farming**\n\n**Major Fertilizers:**\n- **Urea (46% N):** ₹266/bag - Best for leafy growth\n- **DAP (18-46-0):** ₹1,350/bag - For root & flower\n- **MOP (0-0-60):** ₹1,700/bag - For fruit quality\n- **NPK 20:20:20:** Balanced growth\n\n**Organic Options:**\n- 🐄 Vermicompost: 2-3 tons/acre\n- 🌿 Neem cake: Pest repellent + nutrition\n- 🦴 Bone meal: Phosphorus rich\n\n📅 **Application:**\n- Basal dose at sowing\n- Top dressing at 30 & 60 days\n- Never apply urea during rain',
        'soil': '🌍 **Soil Health Guide**\n\n**Testing:** Get soil tested at your nearest KVK (₹50-100)\n\n**Soil Types in India:**\n- **Alluvial:** Best for wheat, rice, sugarcane\n- **Black (Regur):** Cotton, soybean, groundnut\n- **Red:** Millets, groundnut, potato\n- **Laterite:** Tea, coffee, cashew\n\n🧪 **Improving Soil:**\n- Add organic matter yearly\n- Green manuring with Dhaincha\n- Crop rotation\n- Lime for acidic soil\n- Gypsum for alkaline soil',
        'irrigation': '💧 **Irrigation Guide**\n\n**Methods:**\n1. **Drip:** 90% efficiency, best for fruits & vegetables\n   - Govt subsidy: 55-90%\n2. **Sprinkler:** Good for wheat, pulses\n   - Govt subsidy: 50-80%\n3. **Flood:** Traditional, 40% efficiency\n\n**Water Requirements:**\n- Rice: 1200-1400mm\n- Wheat: 400-500mm\n- Cotton: 700-900mm\n- Sugarcane: 1500-2000mm\n\n💡 **Tips:**\n- Irrigate early morning or evening\n- Mulching saves 30% water\n- Sensor-based irrigation saves 40%',
        'disease': '💊 **Common Plant Diseases & Solutions**\n\n**Fungal:**\n- Powdery Mildew: Sulphur/Karathane spray\n- Downy Mildew: Metalaxyl spray\n- Rust: Propiconazole spray\n- Blight: Mancozeb/Copper spray\n\n**Bacterial:**\n- Wilt: Trichoderma soil treatment\n- Soft Rot: Streptocycline spray\n\n**Viral:**\n- Leaf Curl: Control vectors (whitefly)\n- Mosaic: Remove infected plants\n\n🛡️ **Prevention:**\n- Seed treatment with Thiram\n- Crop rotation\n- Resistant varieties\n- Clean cultivation',
        'weather': '🌦️ **Weather-Based Farming Tips**\n\n**Monsoon (Jun-Sep):**\n- Plant kharif crops: Rice, Cotton, Maize\n- Prepare drainage channels\n- Watch for fungal diseases\n\n**Winter (Oct-Feb):**\n- Plant rabi crops: Wheat, Mustard, Gram\n- Protect from frost\n- Good for vegetables\n\n**Summer (Mar-May):**\n- Mulching is essential\n- Summer ploughing\n- Plant: Watermelon, Muskmelon, Cucumber\n\n💡 **App:** Check IMD weather at mausam.imd.gov.in',
        'price': '💰 **Current Market Price Ranges (2026)**\n\n**Cereals:**\n- Rice: ₹2,200-3,000/quintal\n- Wheat: ₹2,200-2,800/quintal\n- Maize: ₹1,800-2,200/quintal\n\n**Vegetables:**\n- Tomato: ₹15-60/kg\n- Onion: ₹20-50/kg\n- Potato: ₹15-35/kg\n\n**Fruits:**\n- Mango: ₹30-200/kg\n- Banana: ₹15-40/kg\n\n📱 **Check live prices:** enam.gov.in\n📞 **Kisan Call Center:** 1800-180-1551',
        'organic': '🌿 **Organic Farming Guide**\n\n**Key Inputs:**\n- Vermicompost: 5 tons/acre\n- Jeevamrutha: 200L/acre monthly\n- Panchagavya: Spray every 15 days\n- Neem oil: Pest control\n\n**Bio-pesticides:**\n- Trichoderma: Soil-borne diseases\n- Beauveria: Insect control\n- Pseudomonas: Bacterial diseases\n\n**Certification:**\n- PGS-India (free)\n- NPOP certification\n- 3-year conversion period\n\n💰 **Premium:** 20-30% higher prices for organic produce',
    }
}

# Telugu and Hindi responses
FARMING_KB['te'] = {
    'hello': '🌿 **నమస్కారం! నేను AgriBot!**\n\nనేను మీ AI వ్యవసాయ సహాయకుడు. నన్ను అడగండి:\n🌾 పంటలు & వ్యవసాయ చిట్కాలు\n🧪 ఎరువులు & నేల\n💊 మొక్క వ్యాధులు\n💧 నీటిపారుదల\n📅 సీజన్ సలహా\n💰 మార్కెట్ ధరలు\n\nమీకు ఏమి తెలుసుకోవాలి?',
    'rice': '🌾 **వరి (బియ్యం) - పూర్తి గైడ్**\n\n**సీజన్:** ఖరీఫ్ (జూన్-నవంబర్)\n**నేల:** బంకమట్టి, pH 5.5-6.5\n**నీరు:** 5-7 సెం.మీ నిలకడ నీరు అవసరం\n\n🧪 **ఎరువులు:**\n- యూరియా: 130 కేజీ/ఎకరం\n- DAP: 60 కేజీ/ఎకరం\n- పొటాష్: 30 కేజీ/ఎకరం\n\n⚠️ **సాధారణ వ్యాధులు:**\n- బ్లాస్ట్: ట్రైసైక్లాజోల్ వాడండి\n- BLB: స్ట్రెప్టోసైక్లిన్ వాడండి\n\n💰 **MSP:** ₹2,300/క్వింటాల్\n**దిగుబడి:** 20-25 క్వింటాళ్లు/ఎకరం',
    'wheat': '🌾 **గోధుమ - పూర్తి గైడ్**\n\n**సీజన్:** రబీ (అక్టోబర్-మార్చి)\n**నేల:** లోమీ నేల, pH 6.0-7.5\n**ఉష్ణోగ్రత:** 15-25°C అనువైనది\n\n🧪 **ఎరువులు:**\n- యూరియా: 130 కేజీ/ఎకరం\n- DAP: 50 కేజీ/ఎకరం\n- MOP: 25 కేజీ/ఎకరం\n\n💰 **MSP:** ₹2,275/క్వింటాల్',
    'tomato': '🍅 **టమాటో - పూర్తి గైడ్**\n\n**సీజన్:** ఏడాది పొడవునా (అక్టో-ఫిబ్ర ఉత్తమం)\n**నేల:** నీరు పోయే లోమీ, pH 6.0-7.0\n**దూరం:** 60x45 సెం.మీ\n\n🧪 **ఎరువులు:**\n- NPK 19:19:19 నాటేటప్పుడు\n- క్యాల్షియం నైట్రేట్ పండ్ల నాణ్యతకు\n\n💰 **మార్కెట్ ధర:** ₹15-60/కేజీ\n**దిగుబడి:** 25-40 టన్నులు/హెక్టార్',
    'mango': '🥭 **మామిడి - పూర్తి గైడ్**\n\n**రకాలు:** బంగినపల్లి, దశేరి, లంగ్ర, తోతాపురి\n**సీజన్:** పూలు జన-ఫిబ్ర, పండ్లు ఏప్రి-జులై\n\n🧪 **ఎరువులు:**\n- వయస్సు ఆధారంగా NPK\n- సూక్ష్మ పోషకాలు: జింక్, బోరాన్\n\n💰 **ధర:** ₹30-200/కేజీ రకాన్ని బట్టి',
    'fertilizer': '🧪 **ఎరువుల గైడ్**\n\n**ప్రధాన ఎరువులు:**\n- **యూరియా (46% N):** ₹266/బ్యాగ్ - ఆకు పెరుగుదలకు\n- **DAP (18-46-0):** ₹1,350/బ్యాగ్ - వేరు & పువ్వుకు\n- **MOP (0-0-60):** ₹1,700/బ్యాగ్ - పండ్ల నాణ్యతకు\n\n**సేంద్రీయ:**\n- 🐄 వర్మికంపోస్ట్: 2-3 టన్నులు/ఎకరం\n- 🌿 వేప పిండి: పురుగు నివారణ',
    'soil': '🌍 **నేల ఆరోగ్య గైడ్**\n\n**పరీక్ష:** మీ సమీపంలోని KVK లో నేల పరీక్ష చేయించండి (₹50-100)\n\n**భారతదేశంలో నేల రకాలు:**\n- **ఒండ్రు:** గోధుమ, వరి, చెరకుకు ఉత్తమం\n- **నల్ల (రేగుర్):** పత్తి, సోయాబీన్\n- **ఎరుపు:** చిరుధాన్యాలు, వేరుశెనగ',
    'disease': '💊 **సాధారణ మొక్క వ్యాధులు & పరిష్కారాలు**\n\n**శిలీంధ్ర:**\n- పొడి తెగులు: సల్ఫర్ పిచికారీ\n- తుప్పు: ప్రొపికొనాజోల్ పిచికారీ\n- బ్లైట్: మాంకోజెబ్ పిచికారీ\n\n**బ్యాక్టీరియా:**\n- వాడు: ట్రైకోడెర్మా నేల చికిత్స\n\n🛡️ **నివారణ:**\n- విత్తన చికిత్స\n- పంట మార్పు\n- నిరోధక రకాలు',
    'irrigation': '💧 **నీటిపారుదల గైడ్**\n\n**పద్ధతులు:**\n1. **డ్రిప్:** 90% సామర్థ్యం - పండ్లు & కూరగాయలకు\n   - ప్రభుత్వ సబ్సిడీ: 55-90%\n2. **స్ప్రింక్లర్:** గోధుమ, పప్పులకు\n3. **వరద:** సాంప్రదాయ, 40% సామర్థ్యం',
    'price': '💰 **ప్రస్తుత మార్కెట్ ధరలు (2026)**\n\n**ధాన్యాలు:**\n- బియ్యం: ₹2,200-3,000/క్వింటాల్\n- గోధుమ: ₹2,200-2,800/క్వింటాల్\n\n**కూరగాయలు:**\n- టమాటో: ₹15-60/కేజీ\n- ఉల్లిపాయ: ₹20-50/కేజీ\n\n📱 **లైవ్ ధరలు:** enam.gov.in\n📞 **కిసాన్ కాల్ సెంటర్:** 1800-180-1551',
    'weather': '🌦️ **వాతావరణ ఆధారిత వ్యవసాయ చిట్కాలు**\n\n**వర్షాకాలం (జూన్-సెప్):**\n- ఖరీఫ్ పంటలు: వరి, పత్తి, మొక్కజొన్న\n\n**శీతాకాలం (అక్టో-ఫిబ్ర):**\n- రబీ పంటలు: గోధుమ, ఆవాలు\n\n**వేసవి (మార్-మే):**\n- మల్చింగ్ అవసరం\n- పుచ్చకాయ, దోసకాయ',
    'organic': '🌿 **సేంద్రీయ వ్యవసాయ గైడ్**\n\n**ముఖ్య ఇన్‌పుట్లు:**\n- వర్మికంపోస్ట్: 5 టన్నులు/ఎకరం\n- జీవామృతం: 200L/ఎకరం నెలకు\n- పంచగవ్య: 15 రోజులకు ఒకసారి పిచికారీ\n- వేప నూనె: పురుగు నియంత్రణ\n\n💰 **ప్రీమియం:** సేంద్రీయ ఉత్పత్తులకు 20-30% ఎక్కువ ధరలు',
}
FARMING_KB['hi'] = {
    'hello': '🌿 **नमस्ते! मैं AgriBot हूं!**\n\nमैं आपका AI कृषि सहायक हूं। मुझसे पूछें:\n🌾 फसलें और खेती के टिप्स\n🧪 उर्वरक और मिट्टी\n💊 पौधों की बीमारियां\n💧 सिंचाई\n📅 मौसमी सलाह\n💰 बाजार भाव\n\nआप क्या जानना चाहते हैं?',
    'rice': '🌾 **चावल (धान) - पूरी गाइड**\n\n**सीजन:** खरीफ (जून-नवंबर)\n**मिट्टी:** चिकनी मिट्टी, pH 5.5-6.5\n**पानी:** 5-7 सेमी खड़ा पानी जरूरी\n\n🧪 **उर्वरक:**\n- यूरिया: 130 किग्रा/एकड़\n- DAP: 60 किग्रा/एकड़\n- पोटाश: 30 किग्रा/एकड़\n\n⚠️ **आम बीमारियां:**\n- ब्लास्ट: ट्राइसाइक्लाजोल\n- BLB: स्ट्रेप्टोसाइक्लिन\n\n💰 **MSP:** ₹2,300/क्विंटल\n**उपज:** 20-25 क्विंटल/एकड़',
    'wheat': '🌾 **गेहूं - पूरी गाइड**\n\n**सीजन:** रबी (अक्टूबर-मार्च)\n**मिट्टी:** दोमट मिट्टी, pH 6.0-7.5\n**तापमान:** 15-25°C आदर्श\n\n🧪 **उर्वरक:**\n- यूरिया: 130 किग्रा/एकड़\n- DAP: 50 किग्रा/एकड़\n- MOP: 25 किग्रा/एकड़\n\n💰 **MSP:** ₹2,275/क्विंटल',
    'tomato': '🍅 **टमाटर - पूरी गाइड**\n\n**सीजन:** साल भर (अक्टू-फरवरी सबसे अच्छा)\n**मिट्टी:** अच्छी जल निकासी वाली दोमट, pH 6.0-7.0\n**दूरी:** 60x45 सेमी\n\n🧪 **उर्वरक:**\n- NPK 19:19:19 रोपाई पर\n- कैल्शियम नाइट्रेट फलों की गुणवत्ता के लिए\n\n💰 **बाजार भाव:** ₹15-60/किग्रा\n**उपज:** 25-40 टन/हेक्टेयर',
    'mango': '🥭 **आम - पूरी गाइड**\n\n**किस्में:** अल्फोंसो, दशहरी, लंगड़ा, तोतापुरी\n**सीजन:** फूल जन-फरवरी, फल अप्रैल-जुलाई\n\n🧪 **उर्वरक:**\n- उम्र के हिसाब से NPK\n- सूक्ष्म पोषक: जिंक, बोरॉन\n\n💰 **भाव:** ₹30-200/किग्रा किस्म के अनुसार',
    'fertilizer': '🧪 **उर्वरक गाइड**\n\n**प्रमुख उर्वरक:**\n- **यूरिया (46% N):** ₹266/बैग - पत्तों की बढ़त\n- **DAP (18-46-0):** ₹1,350/बैग - जड़ और फूल\n- **MOP (0-0-60):** ₹1,700/बैग - फल की गुणवत्ता\n\n**जैविक विकल्प:**\n- 🐄 वर्मीकम्पोस्ट: 2-3 टन/एकड़\n- 🌿 नीम खली: कीट निवारक + पोषण',
    'soil': '🌍 **मिट्टी स्वास्थ्य गाइड**\n\n**परीक्षण:** नजदीकी KVK में मिट्टी परीक्षण करवाएं (₹50-100)\n\n**भारत में मिट्टी के प्रकार:**\n- **जलोढ़:** गेहूं, चावल, गन्ना\n- **काली (रेगुर):** कपास, सोयाबीन\n- **लाल:** बाजरा, मूंगफली',
    'disease': '💊 **आम पौधों की बीमारियां और उपचार**\n\n**फफूंद:**\n- चूर्णिल आसिता: सल्फर छिड़काव\n- रस्ट: प्रोपिकोनाजोल छिड़काव\n- ब्लाइट: मैन्कोजेब छिड़काव\n\n**बैक्टीरिया:**\n- विल्ट: ट्राइकोडर्मा मिट्टी उपचार\n\n🛡️ **रोकथाम:**\n- बीज उपचार\n- फसल चक्र\n- प्रतिरोधी किस्में',
    'irrigation': '💧 **सिंचाई गाइड**\n\n**तरीके:**\n1. **ड्रिप:** 90% दक्षता - फल और सब्जियों के लिए\n   - सरकारी सब्सिडी: 55-90%\n2. **स्प्रिंकलर:** गेहूं, दालों के लिए\n3. **बाढ़:** पारंपरिक, 40% दक्षता',
    'price': '💰 **वर्तमान बाजार भाव (2026)**\n\n**अनाज:**\n- चावल: ₹2,200-3,000/क्विंटल\n- गेहूं: ₹2,200-2,800/क्विंटल\n\n**सब्जियां:**\n- टमाटर: ₹15-60/किग्रा\n- प्याज: ₹20-50/किग्रा\n\n📱 **लाइव भाव:** enam.gov.in\n📞 **किसान कॉल सेंटर:** 1800-180-1551',
    'weather': '🌦️ **मौसम आधारित खेती टिप्स**\n\n**बरसात (जून-सितंबर):**\n- खरीफ फसलें: धान, कपास, मक्का\n\n**सर्दी (अक्टू-फरवरी):**\n- रबी फसलें: गेहूं, सरसों\n\n**गर्मी (मार्च-मई):**\n- मल्चिंग जरूरी\n- तरबूज, खरबूजा, ककड़ी',
    'organic': '🌿 **जैविक खेती गाइड**\n\n**मुख्य सामग्री:**\n- वर्मीकम्पोस्ट: 5 टन/एकड़\n- जीवामृत: 200L/एकड़ मासिक\n- पंचगव्य: 15 दिन में छिड़काव\n- नीम तेल: कीट नियंत्रण\n\n💰 **प्रीमियम:** जैविक उपज के लिए 20-30% अधिक कीमत',
}

def get_offline_response(message, lang='en'):
    """Get response from offline knowledge base"""
    msg = message.lower().strip()
    kb = FARMING_KB.get(lang, FARMING_KB['en'])
    en_kb = FARMING_KB['en']
    
    # Keyword matching - returns response in requested language
    keywords = {
        'rice': ['rice', 'paddy', 'dhan', 'chawal', 'బియ్యం', 'వరి', 'चावल', 'धान'],
        'wheat': ['wheat', 'gehu', 'గోధుమ', 'गेहूं'],
        'tomato': ['tomato', 'tamatar', 'టమాటో', 'टमाटर'],
        'mango': ['mango', 'aam', 'mamidi', 'మామిడి', 'आम'],
        'fertilizer': ['fertilizer', 'urea', 'dap', 'npk', 'manure', 'ఎరువు', 'उर्वरक', 'खाद'],
        'soil': ['soil', 'mitti', 'నేల', 'मिट्टी'],
        'irrigation': ['water', 'irrigation', 'drip', 'sprinkler', 'నీరు', 'पानी', 'सिंचाई'],
        'disease': ['disease', 'pest', 'blight', 'fungus', 'wilt', 'వ్యాధి', 'रोग', 'कीट'],
        'weather': ['weather', 'rain', 'monsoon', 'season', 'వాతావరణం', 'मौसम', 'बारिश'],
        'price': ['price', 'market', 'msp', 'sell', 'ధర', 'दाम', 'बाजार', 'मंडी'],
        'organic': ['organic', 'jaivik', 'natural', 'సేంద్రియ', 'जैविक'],
        'hello': ['hello', 'hi', 'hey', 'hii', 'hiii', 'namaste', 'నమస్కారం', 'नमस्ते', 'help', 'start'],
    }
    
    for topic, words in keywords.items():
        for w in words:
            if w in msg:
                # Return in requested language, fallback to English
                return kb.get(topic, en_kb.get(topic, kb.get('hello', 'Ask me about crops!')))
    
    # Default response
    defaults = {
        'en': '🌿 I can help with:\n\n🌾 **Crops:** rice, wheat, tomato, mango, cotton...\n🧪 **Fertilizers:** urea, DAP, organic options\n💊 **Diseases:** blight, rust, wilt solutions\n💧 **Irrigation:** drip, sprinkler, water management\n💰 **Market prices:** current MSP and mandi rates\n🌦️ **Weather:** seasonal farming tips\n\nTry asking: *"How to grow rice?"* or *"Best fertilizer for tomato?"*',
        'te': '🌿 నేను సహాయం చేయగలను:\n\n🌾 **పంటలు:** బియ్యం, గోధుమ, టమాటో, మామిడి...\n🧪 **ఎరువులు:** యూరియా, DAP, సేంద్రీయ\n💊 **వ్యాధులు:** బ్లైట్, తుప్పు, వడలు\n💧 **నీటిపారుదల:** డ్రిప్, స్ప్రింక్లర్\n\n*"బియ్యం ఎలా పండించాలి?"* అని అడగండి',
        'hi': '🌿 मैं मदद कर सकता हूं:\n\n🌾 **फसलें:** चावल, गेहूं, टमाटर, आम...\n🧪 **उर्वरक:** यूरिया, DAP, जैविक\n💊 **रोग:** ब्लाइट, रस्ट, विल्ट\n💧 **सिंचाई:** ड्रिप, स्प्रिंकलर\n\n*"चावल कैसे उगाएं?"* पूछ कर देखें',
    }
    return defaults.get(lang, defaults['en'])


def call_gemini_sdk(prompt, lang='en'):
    """Try Gemini SDK first"""
    if not genai:
        return None
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text
    except Exception as e:
        print(f"Gemini SDK error: {e}")
    return None


def call_gemini_http(payload):
    """Fallback to HTTP API"""
    for model in GEMINI_MODELS:
        try:
            resp = http_requests.post(get_gemini_url(model), json=payload, timeout=30)
            data = resp.json()
            if 'candidates' in data:
                parts = data['candidates'][0].get('content', {}).get('parts', [])
                text = parts[0].get('text', '') if parts else ''
                if text:
                    return text
            elif resp.status_code == 429 or 'Quota exceeded' in str(data):
                continue
        except Exception:
            continue
    return None


@agribot_bp.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    """Text chat with AgriBot"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        lang = data.get('language', 'en')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        system = SYSTEM_PROMPT.get(lang, SYSTEM_PROMPT['en'])
        lang_instruction = ''
        if lang == 'te':
            lang_instruction = 'IMPORTANT: Reply ONLY in Telugu (తెలుగు). '
        elif lang == 'hi':
            lang_instruction = 'IMPORTANT: Reply ONLY in Hindi (हिंदी). '
        
        full_prompt = f"{system}\n\n{lang_instruction}User question: {message}"
        
        # Try Gemini SDK first
        reply = call_gemini_sdk(full_prompt, lang)
        
        # Try HTTP API
        if not reply:
            payload = {
                'contents': [{'parts': [{'text': full_prompt}]}],
                'generationConfig': {'temperature': 0.7, 'maxOutputTokens': 1024}
            }
            reply = call_gemini_http(payload)
        
        # Fallback to offline knowledge base
        if not reply:
            reply = get_offline_response(message, lang)
        
        return jsonify({'success': True, 'reply': reply}), 200
    except Exception as e:
        print(f'AgriBot chat error: {e}')
        # Even on error, return offline response
        reply = get_offline_response(message if 'message' in dir() else 'hello', 'en')
        return jsonify({'success': True, 'reply': reply}), 200


@agribot_bp.route('/identify-plant', methods=['POST'])
@jwt_required()
def identify_plant():
    """Identify plant from uploaded image"""
    try:
        lang = request.form.get('language', 'en')
        
        if 'image' not in request.files:
            return jsonify({'error': 'Image is required'}), 400
        
        image_file = request.files['image']
        image_bytes = image_file.read()
        image_data = base64.b64encode(image_bytes).decode('utf-8')
        mime_type = image_file.content_type or 'image/jpeg'
        
        system = SYSTEM_PROMPT.get(lang, SYSTEM_PROMPT['en'])
        lang_instruction = ''
        if lang == 'te':
            lang_instruction = 'IMPORTANT: Reply ONLY in Telugu (తెలుగు). '
        elif lang == 'hi':
            lang_instruction = 'IMPORTANT: Reply ONLY in Hindi (हिंदी). '
        
        prompt = f"""{system}

{lang_instruction}Identify this plant/crop from the image. Provide:
1. 🌱 Plant Name
2. ✅ Benefits & Advantages
3. ⚠️ Disadvantages/Challenges
4. 🧪 Recommended Fertilizers
5. 💧 Watering & Care Instructions
6. 📅 Best Season to Grow
7. 💰 Market Price Range

Be detailed and practical for Indian farmers."""
        
        # Try Gemini SDK with image
        reply = None
        if genai:
            try:
                import PIL.Image
                import io
                img = PIL.Image.open(io.BytesIO(image_bytes))
                model = genai.GenerativeModel('gemini-2.0-flash')
                response = model.generate_content([prompt, img])
                if response and response.text:
                    reply = response.text
            except Exception as e:
                print(f"Gemini SDK image error: {e}")
        
        # Try HTTP API
        if not reply:
            payload = {
                'contents': [{'parts': [
                    {'text': prompt},
                    {'inline_data': {'mime_type': mime_type, 'data': image_data}}
                ]}],
                'generationConfig': {'temperature': 0.4, 'maxOutputTokens': 2048}
            }
            reply = call_gemini_http(payload)
        
        # Fallback
        if not reply:
            reply = '📸 **Image Analysis**\n\nI received your image but the AI service is currently busy.\n\n💡 **Try these alternatives:**\n1. Describe the plant in text (leaf shape, color, size)\n2. Ask about a specific crop by name\n3. Try again in a few minutes\n\n🌿 Meanwhile, ask me about any crop: rice, wheat, tomato, mango, etc!'
        
        return jsonify({'success': True, 'reply': reply}), 200
    except Exception as e:
        print(f'Plant identify error: {e}')
        return jsonify({'success': True, 'reply': '📸 Could not process the image right now. Please describe your plant or try again later.'}), 200
