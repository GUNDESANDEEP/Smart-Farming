import { useEffect, useRef, useCallback } from 'react';
import { io } from 'socket.io-client';

const SOCKET_URL = process.env.REACT_APP_SOCKET_URL || 'http://localhost:5000';

export const useSocket = (userId) => {
  const socketRef = useRef(null);

  useEffect(() => {
    if (!userId) return;

    // Initialize socket connection
    socketRef.current = io(SOCKET_URL, {
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5,
    });

    // Authenticate socket
    socketRef.current.on('connect', () => {
      console.log('Socket connected');
      socketRef.current.emit('authenticate', { user_id: userId });
    });

    socketRef.current.on('authenticated', (data) => {
      console.log('Socket authenticated:', data);
    });

    socketRef.current.on('error', (error) => {
      console.error('Socket error:', error);
    });

    socketRef.current.on('disconnect', () => {
      console.log('Socket disconnected');
    });

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, [userId]);

  return socketRef.current;
};

export const useConversationSocket = (userId, conversationId) => {
  const socket = useSocket(userId);
  const messageHandlerRef = useRef(null);

  useEffect(() => {
    if (!socket || !conversationId) return;

    // Join conversation room
    socket.emit('join_conversation', { conversation_id: conversationId });

    return () => {
      socket.emit('leave_conversation', { conversation_id: conversationId });
    };
  }, [socket, conversationId]);

  const sendMessage = useCallback(
    (message) => {
      if (socket && conversationId) {
        socket.emit('send_message', {
          conversation_id: conversationId,
          message,
        });
      }
    },
    [socket, conversationId]
  );

  const onMessageReceived = useCallback(
    (handler) => {
      if (socket) {
        socket.off('new_message');
        socket.on('new_message', handler);
        messageHandlerRef.current = handler;
      }
    },
    [socket]
  );

  const onUserTyping = useCallback(
    (handler) => {
      if (socket) {
        socket.off('user_typing');
        socket.on('user_typing', handler);
      }
    },
    [socket]
  );

  const setTyping = useCallback(() => {
    if (socket && conversationId) {
      socket.emit('typing', { conversation_id: conversationId });
    }
  }, [socket, conversationId]);

  return { sendMessage, onMessageReceived, onUserTyping, setTyping };
};

export const useOrderSocket = (userId, orderId) => {
  const socket = useSocket(userId);

  useEffect(() => {
    if (!socket || !orderId) return;

    // Join order room
    socket.emit('join_order', { order_id: orderId });

    return () => {
      // Leave order room
    };
  }, [socket, orderId]);

  const onOrderUpdate = useCallback(
    (handler) => {
      if (socket) {
        socket.off('order_updated');
        socket.on('order_updated', handler);
      }
    },
    [socket]
  );

  const updateOrderStatus = useCallback(
    (status) => {
      if (socket && orderId) {
        socket.emit('order_status_update', {
          order_id: orderId,
          status,
        });
      }
    },
    [socket, orderId]
  );

  return { onOrderUpdate, updateOrderStatus };
};

export const useNotificationSocket = (userId) => {
  const socket = useSocket(userId);

  useEffect(() => {
    if (!socket) return;

    socket.emit('subscribe_notifications');
  }, [socket]);

  const onNotification = useCallback(
    (handler) => {
      if (socket) {
        socket.off('notification');
        socket.on('notification', handler);
      }
    },
    [socket]
  );

  return { onNotification };
};

export const useProductSocket = (productId) => {
  const socketRef = useRef(null);

  useEffect(() => {
    if (!productId) return;

    socketRef.current = io(SOCKET_URL);

    socketRef.current.on('connect', () => {
      socketRef.current.emit('subscribe_product', { product_id: productId });
    });

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, [productId]);

  const onStockUpdate = useCallback(
    (handler) => {
      if (socketRef.current) {
        socketRef.current.off('stock_updated');
        socketRef.current.on('stock_updated', handler);
      }
    },
    []
  );

  return { onStockUpdate };
};

export const usePresenceSocket = (userId) => {
  const socket = useSocket(userId);

  const setPresence = useCallback(
    (status) => {
      if (socket) {
        socket.emit('set_presence', { status });
      }
    },
    [socket]
  );

  const onPresenceUpdate = useCallback(
    (handler) => {
      if (socket) {
        socket.off('presence_updated');
        socket.on('presence_updated', handler);
      }
    },
    [socket]
  );

  return { setPresence, onPresenceUpdate };
};

export const useDirectMessageSocket = (userId) => {
  const socket = useSocket(userId);

  const sendDirectMessage = useCallback(
    (recipientId, message) => {
      if (socket) {
        socket.emit('send_direct_message', {
          recipient_id: recipientId,
          message,
        });
      }
    },
    [socket]
  );

  const onDirectMessage = useCallback(
    (handler) => {
      if (socket) {
        socket.off('direct_message');
        socket.on('direct_message', handler);
      }
    },
    [socket]
  );

  return { sendDirectMessage, onDirectMessage };
};
