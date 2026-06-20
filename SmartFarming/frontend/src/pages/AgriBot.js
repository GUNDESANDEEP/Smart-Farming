import React, { useState, useRef, useEffect, useCallback } from 'react';
import { FiSend, FiCamera, FiGlobe, FiX, FiPaperclip, FiVolume2, FiVolumeX, FiPlus, FiTrash2, FiMessageSquare, FiMenu } from 'react-icons/fi';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
const getToken = () => localStorage.getItem('access_token');
const STORAGE_KEY = 'agribot_chats';

const LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇬🇧', ttsLang: 'en-US' },
  { code: 'te', name: 'తెలుగు', flag: '🇮🇳', ttsLang: 'te-IN' },
  { code: 'hi', name: 'हिंदी', flag: '🇮🇳', ttsLang: 'hi-IN' },
];

const WELCOME_MSG = {
  en: '🌿 Hello! I am AgriBot, your AI farming assistant.\n\nI can help you with:\n📸 **Plant identification** - Take a photo!\n🧪 **Fertilizer advice**\n🌾 **Crop recommendations**\n💊 **Disease diagnosis**\n📁 **Upload files** for analysis\n\nAsk me anything or take a photo of your crop!',
  te: '🌿 నమస్కారం! నేను AgriBot, మీ AI వ్యవసాయ సహాయకుడు.\n\nనేను మీకు సహాయం చేయగలను:\n📸 **మొక్క గుర్తింపు** - ఫోటో తీయండి!\n🧪 **ఎరువుల సలహా**\n🌾 **పంట సిఫార్సులు**\n💊 **వ్యాధి నిర్ధారణ**\n📁 **ఫైళ్లు అప్‌లోడ్** విశ్లేషణ కోసం\n\nఏదైనా అడగండి లేదా మీ పంట ఫోటో తీయండి!',
  hi: '🌿 नमस्ते! मैं AgriBot हूं, आपका AI कृषि सहायक.\n\nमैं इसमें मदद कर सकता हूं:\n📸 **पौधे की पहचान** - फोटो लें!\n🧪 **उर्वरक सलाह**\n🌾 **फसल सिफारिशें**\n💊 **रोग निदान**\n📁 **फाइल अपलोड** विश्लेषण के लिए\n\nकुछ भी पूछें या अपनी फसल की फोटो लें!',
};

/* ── keyframes ── */
const KEYFRAMES_ID = 'agribot-keyframes';
const injectKeyframes = () => {
  if (document.getElementById(KEYFRAMES_ID)) return;
  const style = document.createElement('style');
  style.id = KEYFRAMES_ID;
  style.textContent = `
    @keyframes agriPulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.5;transform:scale(1.15)} }
    @keyframes agriFadeSlideUp { from{opacity:0;transform:translateY(14px)} to{opacity:1;transform:translateY(0)} }
    @keyframes agriBounce { 0%,80%,100%{transform:translateY(0)} 40%{transform:translateY(-5px)} }
  `;
  document.head.appendChild(style);
};

/* ── markdown formatter ── */
const formatBotText = (text) => {
  if (!text) return null;
  return text.split('\n').map((line, i) => {
    const formatted = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    return <p key={i} style={{ margin: '2px 0' }} dangerouslySetInnerHTML={{ __html: formatted }} />;
  });
};

/* ── localStorage helpers ── */
const loadChats = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
};

const saveChats = (chats) => {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(chats)); } catch {}
};

const generateId = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 6);

const getChatTitle = (msgs) => {
  const userMsg = msgs.find(m => m.role === 'user');
  if (userMsg) return userMsg.text.slice(0, 30) + (userMsg.text.length > 30 ? '...' : '');
  return 'New Chat';
};

const formatDate = (ts) => {
  const d = new Date(ts);
  const now = new Date();
  const diff = now - d;
  if (diff < 86400000) return 'Today';
  if (diff < 172800000) return 'Yesterday';
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
};

/* ════════════════════════════════════════════════
   AgriBot Component
   ════════════════════════════════════════════════ */
const AgriBot = () => {
  const [chatList, setChatList] = useState(() => loadChats());
  const [activeChatId, setActiveChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [language, setLanguage] = useState('en');
  const [loading, setLoading] = useState(false);
  const [showLangMenu, setShowLangMenu] = useState(false);
  const [imagePreview, setImagePreview] = useState(null);
  const [speakingIdx, setSpeakingIdx] = useState(-1);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth >= 768);
  const [voices, setVoices] = useState([]);

  const chatEndRef = useRef(null);
  const cameraInputRef = useRef(null);
  const fileInputRef = useRef(null);
  const prevLangRef = useRef(language);
  const audioRef = useRef(null);

  useEffect(() => { injectKeyframes(); }, []);
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  /* ── Detect mobile resize ── */
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (!mobile && !sidebarOpen) setSidebarOpen(true);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [sidebarOpen]);

  /* ── Preload TTS voices ── */
  useEffect(() => {
    const loadVoices = () => {
      const v = window.speechSynthesis?.getVoices() || [];
      setVoices(v);
    };
    loadVoices();
    if (window.speechSynthesis) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }
    return () => { if (window.speechSynthesis) window.speechSynthesis.onvoiceschanged = null; };
  }, []);

  /* ── create new chat ── */
  const startNewChat = useCallback((lang) => {
    const id = generateId();
    const welcome = { role: 'bot', text: WELCOME_MSG[lang || language] || WELCOME_MSG.en, time: new Date().toISOString() };
    const newChat = { id, messages: [welcome], language: lang || language, createdAt: Date.now(), updatedAt: Date.now() };
    setChatList(prev => {
      const updated = [newChat, ...prev];
      saveChats(updated);
      return updated;
    });
    setActiveChatId(id);
    setMessages([welcome]);
  }, [language]);

  /* ── load initial chat ── */
  useEffect(() => {
    if (chatList.length > 0 && !activeChatId) {
      const latest = chatList[0];
      setActiveChatId(latest.id);
      setMessages(latest.messages || []);
      setLanguage(latest.language || 'en');
      prevLangRef.current = latest.language || 'en';
    } else if (chatList.length === 0) {
      startNewChat('en');
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* ── AUTO-TRANSLATE: when language changes, re-translate all bot messages ── */
  useEffect(() => {
    if (prevLangRef.current === language) return;
    prevLangRef.current = language;

    const translateAll = async () => {
      setLoading(true);
      const newMessages = [];

      for (const msg of messages) {
        if (msg.role === 'user') {
          newMessages.push(msg);
        } else if (msg.role === 'bot') {
          // Check if this is the welcome message
          const isWelcome = Object.values(WELCOME_MSG).some(w => msg.text === w);
          if (isWelcome) {
            newMessages.push({ ...msg, text: WELCOME_MSG[language] || WELCOME_MSG.en, time: new Date().toISOString() });
          } else {
            // Find the user message before this bot message to re-ask
            const idx = messages.indexOf(msg);
            const prevUserMsg = messages.slice(0, idx).reverse().find(m => m.role === 'user');
            if (prevUserMsg && prevUserMsg.text && !prevUserMsg.text.startsWith('📸') && !prevUserMsg.text.startsWith('📁')) {
              try {
                const res = await axios.post(`${API_URL}/agribot/chat`,
                  { message: prevUserMsg.text, language },
                  { headers: { Authorization: `Bearer ${getToken()}` } }
                );
                newMessages.push({ ...msg, text: res.data.reply, time: new Date().toISOString() });
              } catch {
                newMessages.push(msg); // Keep original if translation fails
              }
            } else {
              newMessages.push(msg); // Keep image responses as-is
            }
          }
        }
      }

      setMessages(newMessages);
      setLoading(false);
    };

    translateAll();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [language]);

  /* ── save messages to chatList when they change ── */
  useEffect(() => {
    if (!activeChatId || messages.length === 0) return;
    setChatList(prev => {
      const updated = prev.map(c =>
        c.id === activeChatId ? { ...c, messages, language, updatedAt: Date.now() } : c
      );
      saveChats(updated);
      return updated;
    });
  }, [messages, activeChatId, language]);

  /* ── switch chat ── */
  const switchChat = (chatId) => {
    window.speechSynthesis?.cancel();
    setSpeakingIdx(-1);
    const chat = chatList.find(c => c.id === chatId);
    if (chat) {
      setActiveChatId(chatId);
      setMessages(chat.messages || []);
      setLanguage(chat.language || 'en');
    }
  };

  /* ── delete chat ── */
  const deleteChat = (e, chatId) => {
    e.stopPropagation();
    setChatList(prev => {
      const updated = prev.filter(c => c.id !== chatId);
      saveChats(updated);
      if (chatId === activeChatId) {
        if (updated.length > 0) {
          setActiveChatId(updated[0].id);
          setMessages(updated[0].messages || []);
          setLanguage(updated[0].language || 'en');
        } else {
          startNewChat('en');
        }
      }
      return updated;
    });
  };

  /* ── TTS: speak in the selected language ── */
  const speakText = (text, idx) => {
    // If already speaking this, stop
    if (speakingIdx === idx) {
      window.speechSynthesis?.cancel();
      if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
      setSpeakingIdx(-1);
      return;
    }
    window.speechSynthesis?.cancel();
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }

    // Clean text: remove markdown and emoji, keep ALL language characters
    const clean = text
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/[#•]/g, '')
      .replace(/₹/g, ' rupees ')
      .replace(/\n+/g, '. ')
      .replace(/[-]{2,}/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();

    const langObj = LANGUAGES.find(l => l.code === language);
    const targetLang = langObj?.ttsLang || 'en-US';
    const langPrefix = targetLang.split('-')[0];

    // Check if a local voice exists for this language
    const hasLocalVoice = voices.some(v =>
      v.lang === targetLang ||
      v.lang.startsWith(langPrefix + '-') ||
      v.lang.startsWith(langPrefix)
    );

    if (hasLocalVoice) {
      // Use browser SpeechSynthesis with matched voice
      const utterance = new SpeechSynthesisUtterance(clean);
      utterance.lang = targetLang;
      utterance.rate = 0.85;

      let bestVoice = voices.find(v => v.lang === targetLang);
      if (!bestVoice) bestVoice = voices.find(v => v.lang.startsWith(langPrefix));
      if (bestVoice) {
        utterance.voice = bestVoice;
        utterance.lang = bestVoice.lang;
      }

      utterance.onend = () => setSpeakingIdx(-1);
      utterance.onerror = () => setSpeakingIdx(-1);
      setSpeakingIdx(idx);
      window.speechSynthesis.speak(utterance);
    } else {
      // Fallback: Use Google Translate TTS (supports Telugu, Hindi, etc.)
      setSpeakingIdx(idx);
      const langCode = langPrefix; // 'te', 'hi', 'en'

      // Google TTS has a ~200 char limit, split into chunks
      const chunks = [];
      let remaining = clean;
      while (remaining.length > 0) {
        if (remaining.length <= 200) {
          chunks.push(remaining);
          break;
        }
        // Find a good break point
        let breakAt = remaining.lastIndexOf('. ', 200);
        if (breakAt < 50) breakAt = remaining.lastIndexOf(' ', 200);
        if (breakAt < 50) breakAt = 200;
        chunks.push(remaining.slice(0, breakAt));
        remaining = remaining.slice(breakAt).trim();
      }

      const playChunks = async (index) => {
        if (index >= chunks.length) { setSpeakingIdx(-1); return; }
        const encoded = encodeURIComponent(chunks[index]);
        const url = `https://translate.google.com/translate_tts?ie=UTF-8&q=${encoded}&tl=${langCode}&client=tw-ob`;
        const audio = new Audio(url);
        audioRef.current = audio;
        audio.onended = () => playChunks(index + 1);
        audio.onerror = () => {
          // If Google TTS fails, try browser synthesis anyway
          const utter = new SpeechSynthesisUtterance(chunks[index]);
          utter.lang = targetLang;
          utter.rate = 0.85;
          utter.onend = () => playChunks(index + 1);
          utter.onerror = () => setSpeakingIdx(-1);
          window.speechSynthesis?.speak(utter);
        };
        try { await audio.play(); } catch { playChunks(index + 1); }
      };

      playChunks(0);
    }
  };

  /* ── send text ── */
  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMsg = { role: 'user', text: input, time: new Date().toISOString() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    try {
      const res = await axios.post(`${API_URL}/agribot/chat`, { message: input, language },
        { headers: { Authorization: `Bearer ${getToken()}` } });
      setMessages(prev => [...prev, { role: 'bot', text: res.data.reply, time: new Date().toISOString() }]);
    } catch (err) {
      const errMsg = err.response?.data?.error || 'Something went wrong. Please try again.';
      setMessages(prev => [...prev, { role: 'bot', text: `❌ ${errMsg}`, time: new Date().toISOString() }]);
    } finally { setLoading(false); }
  };

  /* ── upload image ── */
  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => setImagePreview(ev.target.result);
    reader.readAsDataURL(file);
    const isImage = file.type.startsWith('image/');
    setMessages(prev => [...prev, {
      role: 'user', text: isImage ? '📸 Identifying this plant...' : `📁 Uploaded: ${file.name}`,
      image: isImage ? URL.createObjectURL(file) : null, time: new Date().toISOString(),
    }]);
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('image', file);
      formData.append('language', language);
      const res = await axios.post(`${API_URL}/agribot/identify-plant`, formData,
        { headers: { Authorization: `Bearer ${getToken()}`, 'Content-Type': 'multipart/form-data' } });
      setMessages(prev => [...prev, { role: 'bot', text: res.data.reply, time: new Date().toISOString() }]);
    } catch (err) {
      const errMsg = err.response?.data?.error || 'Could not analyze. Please try again.';
      setMessages(prev => [...prev, { role: 'bot', text: `❌ ${errMsg}`, time: new Date().toISOString() }]);
    } finally {
      setLoading(false); setImagePreview(null);
      if (cameraInputRef.current) cameraInputRef.current.value = '';
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleKeyDown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } };
  const currentLang = LANGUAGES.find(l => l.code === language) || LANGUAGES[0];

  /* ═══════════════════════════════════════
     Styles
     ═══════════════════════════════════════ */
  const S = {
    wrapper: {
      display: 'flex', height: 'calc(100vh - 80px)', borderRadius: isMobile ? '0' : '16px', overflow: 'hidden',
      fontFamily: "'Poppins', sans-serif", background: '#f0fdf4', position: 'relative',
    },
    /* ── sidebar ── */
    sidebar: {
      width: sidebarOpen ? (isMobile ? '85vw' : '280px') : '0px',
      minWidth: sidebarOpen ? (isMobile ? '85vw' : '280px') : '0px',
      background: 'linear-gradient(180deg, #14532d, #166534)',
      display: 'flex', flexDirection: 'column', transition: 'all 0.3s ease',
      overflow: 'hidden', borderRight: '1px solid rgba(255,255,255,0.1)',
      ...(isMobile && sidebarOpen ? {
        position: 'absolute', top: 0, left: 0, bottom: 0, zIndex: 60,
        boxShadow: '4px 0 24px rgba(0,0,0,0.3)',
      } : {}),
    },
    sidebarOverlay: {
      display: isMobile && sidebarOpen ? 'block' : 'none',
      position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.4)', zIndex: 55,
    },
    sidebarHeader: {
      padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      borderBottom: '1px solid rgba(255,255,255,0.1)',
    },
    newChatBtn: {
      display: 'flex', alignItems: 'center', gap: '8px', width: '100%',
      padding: '10px 14px', borderRadius: '10px', border: '1px dashed rgba(255,255,255,0.3)',
      background: 'rgba(255,255,255,0.08)', color: '#a7f3d0', cursor: 'pointer',
      fontSize: '0.88rem', fontFamily: "'Poppins', sans-serif", transition: 'all 0.2s',
    },
    chatList: { flex: 1, overflowY: 'auto', padding: '8px' },
    chatItem: (isActive) => ({
      display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 12px',
      borderRadius: '10px', cursor: 'pointer', marginBottom: '4px', transition: 'all 0.2s',
      background: isActive ? 'rgba(34,197,94,0.2)' : 'transparent',
      border: isActive ? '1px solid rgba(34,197,94,0.3)' : '1px solid transparent',
    }),
    chatItemText: { flex: 1, overflow: 'hidden' },
    chatItemTitle: { color: '#e2e8f0', fontSize: '0.82rem', fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
    chatItemDate: { color: '#94a3b8', fontSize: '0.7rem', marginTop: '2px' },
    deleteBtn: {
      background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer',
      padding: '4px', borderRadius: '6px', display: 'flex', alignItems: 'center',
      transition: 'color 0.2s', flexShrink: 0,
    },
    /* ── main chat ── */
    main: { flex: 1, display: 'flex', flexDirection: 'column', background: 'linear-gradient(135deg, #f0fdf4, #dcfce7)' },
    topBar: {
      background: 'linear-gradient(135deg, #166534, #14532d)', padding: '12px 16px',
      display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#fff',
    },
    topLeft: { display: 'flex', alignItems: 'center', gap: '10px' },
    menuBtn: {
      background: 'rgba(255,255,255,0.12)', border: 'none', color: '#fff',
      borderRadius: '8px', padding: '6px 8px', cursor: 'pointer', display: 'flex',
      alignItems: 'center', justifyContent: 'center',
    },
    langBtn: {
      display: 'flex', alignItems: 'center', gap: '6px',
      background: 'rgba(255,255,255,0.15)', border: '1px solid rgba(255,255,255,0.25)',
      borderRadius: '20px', padding: '6px 14px', color: '#fff',
      cursor: 'pointer', fontSize: '0.85rem', position: 'relative',
      fontFamily: "'Poppins', sans-serif",
    },
    langMenu: {
      position: 'absolute', top: '110%', right: 0, background: '#fff', borderRadius: '12px',
      boxShadow: '0 8px 24px rgba(0,0,0,0.15)', overflow: 'hidden', zIndex: 50,
      minWidth: '150px', animation: 'agriFadeSlideUp 0.2s ease',
    },
    langOpt: (a) => ({
      padding: '10px 16px', cursor: 'pointer', display: 'flex',
      alignItems: 'center', gap: '8px', color: '#14532d', fontSize: '0.9rem',
      background: a ? '#f0fdf4' : '#fff', fontWeight: a ? 600 : 400,
    }),
    chatArea: { flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' },
    userBubble: {
      alignSelf: 'flex-end', background: 'linear-gradient(135deg, #22c55e, #16a34a)',
      color: '#fff', padding: isMobile ? '10px 14px' : '12px 16px', borderRadius: '16px 16px 4px 16px',
      maxWidth: isMobile ? '88%' : '75%', boxShadow: '0 2px 8px rgba(34,197,94,0.2)',
      animation: 'agriFadeSlideUp 0.3s ease', whiteSpace: 'pre-wrap', lineHeight: 1.6, wordBreak: 'break-word',
      fontSize: isMobile ? '0.88rem' : '0.95rem',
    },
    botBubble: {
      alignSelf: 'flex-start', background: 'rgba(255,255,255,0.95)', color: '#14532d',
      padding: isMobile ? '10px 14px' : '12px 16px', borderRadius: '16px 16px 16px 4px',
      maxWidth: isMobile ? '92%' : '80%', boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
      border: '1px solid rgba(22,163,74,0.1)', whiteSpace: 'pre-wrap',
      lineHeight: 1.6, animation: 'agriFadeSlideUp 0.3s ease', wordBreak: 'break-word',
      fontSize: isMobile ? '0.85rem' : '0.95rem',
    },
    msgTime: { fontSize: '0.7rem', opacity: 0.6, marginTop: '6px', textAlign: 'right' },
    msgImage: { maxWidth: '200px', borderRadius: '12px', marginBottom: '8px', display: 'block' },
    inputBar: {
      display: 'flex', gap: '8px', padding: '12px 16px',
      background: 'rgba(255,255,255,0.95)', borderTop: '1px solid rgba(22,163,74,0.1)',
      alignItems: 'center', position: 'relative',
    },
    inputField: {
      flex: 1, padding: '12px 16px', borderRadius: '25px',
      border: '2px solid rgba(22,163,74,0.15)', outline: 'none',
      fontSize: '0.95rem', fontFamily: "'Poppins', sans-serif",
    },
    iconBtn: (d) => ({
      width: '42px', height: '42px', borderRadius: '50%', border: 'none',
      background: d ? '#a7f3d0' : 'linear-gradient(135deg, #22c55e, #16a34a)',
      color: '#fff', cursor: d ? 'not-allowed' : 'pointer',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: '1.1rem', transition: 'transform 0.15s', flexShrink: 0,
    }),
    speakBtn: (active) => ({
      background: 'none', border: 'none', cursor: 'pointer',
      color: active ? '#22c55e' : '#94a3b8', fontSize: '0.9rem',
      display: 'flex', alignItems: 'center', gap: '3px',
      marginTop: '4px', padding: '2px 6px', borderRadius: '8px',
    }),
    dot: (d) => ({
      width: '8px', height: '8px', borderRadius: '50%', background: '#22c55e',
      animation: `agriBounce 1.2s ${d}s infinite ease`,
    }),
    previewOverlay: {
      position: 'absolute', bottom: '70px', left: '16px', right: '16px',
      background: 'rgba(255,255,255,0.97)', borderRadius: '14px', padding: '12px',
      boxShadow: '0 4px 20px rgba(0,0,0,0.12)', display: 'flex',
      alignItems: 'center', gap: '12px', zIndex: 10,
    },
  };

  return (
    <div style={S.wrapper}>
      {/* ═══ Left Sidebar ═══ */}
      <div style={S.sidebar}>
        <div style={S.sidebarHeader}>
          <button style={S.newChatBtn} onClick={() => { startNewChat(language); if (isMobile) setSidebarOpen(false); }}
            onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.15)'; }}
            onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.08)'; }}>
            <FiPlus size={16} /> New Chat
          </button>
        </div>

        <div style={S.chatList}>
          {chatList.map(chat => (
            <div key={chat.id} style={S.chatItem(chat.id === activeChatId)}
              onClick={() => { switchChat(chat.id); if (isMobile) setSidebarOpen(false); }}
              onMouseEnter={e => { if (chat.id !== activeChatId) e.currentTarget.style.background = 'rgba(255,255,255,0.06)'; }}
              onMouseLeave={e => { if (chat.id !== activeChatId) e.currentTarget.style.background = 'transparent'; }}>
              <FiMessageSquare size={14} style={{ color: '#86efac', flexShrink: 0 }} />
              <div style={S.chatItemText}>
                <div style={S.chatItemTitle}>{getChatTitle(chat.messages || [])}</div>
                <div style={S.chatItemDate}>{formatDate(chat.updatedAt || chat.createdAt)}</div>
              </div>
              <button style={S.deleteBtn} onClick={(e) => deleteChat(e, chat.id)}
                onMouseEnter={e => { e.currentTarget.style.color = '#f87171'; }}
                onMouseLeave={e => { e.currentTarget.style.color = '#94a3b8'; }}
                title="Delete chat">
                <FiTrash2 size={14} />
              </button>
            </div>
          ))}
        </div>

        <div style={{ padding: '12px', borderTop: '1px solid rgba(255,255,255,0.1)', color: '#86efac', fontSize: '0.72rem', textAlign: 'center', opacity: 0.7 }}>
          💬 {chatList.length} chat{chatList.length !== 1 ? 's' : ''} saved
        </div>
      </div>

      {/* Mobile overlay */}
      <div style={S.sidebarOverlay} onClick={() => setSidebarOpen(false)} />

      {/* ═══ Main Chat ═══ */}
      <div style={S.main}>
        {/* Top Bar */}
        <div style={S.topBar}>
          <div style={S.topLeft}>
            <button style={S.menuBtn} onClick={() => setSidebarOpen(v => !v)} title="Toggle sidebar">
              <FiMenu size={18} />
            </button>
            <span style={{ fontSize: '1.05rem', fontWeight: 600 }}>🤖 AgriBot</span>
          </div>
          <button style={S.langBtn} onClick={() => setShowLangMenu(v => !v)}>
            <FiGlobe size={16} />
            <span>{currentLang.flag} {currentLang.name}</span>
            {showLangMenu && (
              <div style={S.langMenu} onClick={e => e.stopPropagation()}>
                {LANGUAGES.map(lang => (
                  <div key={lang.code} style={S.langOpt(lang.code === language)}
                    onMouseEnter={e => { e.currentTarget.style.background = '#f0fdf4'; }}
                    onMouseLeave={e => { e.currentTarget.style.background = lang.code === language ? '#f0fdf4' : '#fff'; }}
                    onClick={() => { setLanguage(lang.code); setShowLangMenu(false); }}>
                    <span>{lang.flag}</span> <span>{lang.name}</span>
                  </div>
                ))}
              </div>
            )}
          </button>
        </div>

        {/* Chat Area */}
        <div style={S.chatArea}>
          {messages.map((msg, idx) => (
            <div key={idx} style={msg.role === 'user' ? S.userBubble : S.botBubble}>
              {msg.image && <img src={msg.image} alt="uploaded" style={S.msgImage} />}
              {msg.role === 'bot' ? formatBotText(msg.text) : msg.text}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                {msg.role === 'bot' && (
                  <button style={S.speakBtn(speakingIdx === idx)} onClick={() => speakText(msg.text, idx)}
                    title={speakingIdx === idx ? 'Stop' : 'Listen'}>
                    {speakingIdx === idx ? <FiVolumeX size={14} /> : <FiVolume2 size={14} />}
                    <span style={{ fontSize: '0.72rem' }}>{speakingIdx === idx ? 'Stop' : '🔊'}</span>
                  </button>
                )}
                <div style={S.msgTime}>
                  {new Date(msg.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          ))}

          {loading && (
            <div style={S.botBubble}>
              <div style={{ display: 'flex', gap: '6px', alignItems: 'center', padding: '4px 0' }}>
                <span style={{ animation: 'agriPulse 1s infinite' }}>🤖</span>
                <div style={S.dot(0)} /> <div style={S.dot(0.15)} /> <div style={S.dot(0.3)} />
                <span style={{ marginLeft: '6px', fontSize: '0.88rem', color: '#16a34a', fontWeight: 500 }}>Thinking…</span>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Image Preview */}
        {imagePreview && (
          <div style={S.previewOverlay}>
            <img src={imagePreview} alt="preview" style={{ width: 64, height: 64, borderRadius: 10, objectFit: 'cover' }} />
            <span style={{ fontSize: '0.9rem', color: '#14532d', fontWeight: 500 }}>Analyzing image…</span>
            <button style={{ marginLeft: 'auto', background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}
              onClick={() => setImagePreview(null)}><FiX size={20} /></button>
          </div>
        )}

        {/* Input Bar */}
        <div style={S.inputBar}>
          <input type="file" accept="image/*" capture="environment" ref={cameraInputRef}
            style={{ display: 'none' }} onChange={handleImageUpload} />
          <input type="file" accept="image/*,.pdf,.doc,.docx,.txt" ref={fileInputRef}
            style={{ display: 'none' }} onChange={handleImageUpload} />
          <button style={S.iconBtn(loading)} disabled={loading} title="Take a photo"
            onClick={() => cameraInputRef.current?.click()}><FiCamera size={18} /></button>
          <button style={S.iconBtn(loading)} disabled={loading} title="Upload file"
            onClick={() => fileInputRef.current?.click()}><FiPaperclip size={18} /></button>
          <input style={S.inputField} placeholder="Ask about crops, soil, fertilizers..."
            value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKeyDown}
            onFocus={e => { e.target.style.borderColor = '#22c55e'; }}
            onBlur={e => { e.target.style.borderColor = 'rgba(22,163,74,0.15)'; }}
            disabled={loading} />
          <button style={S.iconBtn(loading || !input.trim())} disabled={loading || !input.trim()}
            title="Send" onClick={handleSend}><FiSend size={17} /></button>
        </div>
      </div>
    </div>
  );
};

export default AgriBot;
