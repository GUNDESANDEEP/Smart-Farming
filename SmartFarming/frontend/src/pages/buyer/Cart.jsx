import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { buyerAPI } from '../../services/api';
import toast from 'react-hot-toast';
import { FiTrash2, FiArrowLeft } from 'react-icons/fi';

export default function ShoppingCart() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user || user.role !== 'buyer') {
      navigate('/login');
      return;
    }
    fetchCart();
  }, [user, navigate]);

  const fetchCart = async () => {
    try {
      setLoading(true);
      const response = await buyerAPI.getCart();
      setCart(response.data.data);
    } catch (error) {
      toast.error('Failed to load cart');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateQuantity = async (itemId, quantity) => {
    if (quantity <= 0) {
      handleRemoveItem(itemId);
      return;
    }

    try {
      await buyerAPI.updateCartItem(itemId, quantity);
      fetchCart();
      toast.success('Cart updated');
    } catch (error) {
      toast.error('Failed to update cart');
    }
  };

  const handleRemoveItem = async (itemId) => {
    try {
      await buyerAPI.removeFromCart(itemId);
      fetchCart();
      toast.success('Item removed from cart');
    } catch (error) {
      toast.error('Failed to remove item');
    }
  };

  const handleClearCart = async () => {
    if (window.confirm('Are you sure you want to clear your cart?')) {
      try {
        await buyerAPI.clearCart();
        setCart({ items: [], total_amount: 0 });
        toast.success('Cart cleared');
      } catch (error) {
        toast.error('Failed to clear cart');
      }
    }
  };

  const handleCheckout = () => {
    if (!cart || cart.items.length === 0) {
      toast.error('Your cart is empty');
      return;
    }
    navigate('/buyer/checkout', { state: { cart } });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading cart...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <button
            onClick={() => navigate('/buyer/marketplace')}
            className="flex items-center text-green-600 hover:text-green-700 font-semibold"
          >
            <FiArrowLeft className="mr-2" /> Continue Shopping
          </button>
          <h1 className="text-2xl font-bold text-green-600">Shopping Cart</h1>
          <div className="w-32" /> {/* Spacer for alignment */}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {!cart || cart.items.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <p className="text-gray-600 text-xl mb-4">Your cart is empty</p>
            <button
              onClick={() => navigate('/buyer/marketplace')}
              className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 font-semibold"
            >
              Continue Shopping
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Cart Items */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className="px-6 py-4 border-b flex justify-between items-center">
                  <h2 className="text-lg font-bold text-gray-800">
                    Cart Items ({cart.items.length})
                  </h2>
                  {cart.items.length > 0 && (
                    <button
                      onClick={handleClearCart}
                      className="text-red-600 hover:text-red-700 text-sm font-semibold"
                    >
                      Clear Cart
                    </button>
                  )}
                </div>

                <div className="divide-y">
                  {cart.items.map((item) => (
                    <div key={item.id} className="px-6 py-4">
                      <div className="flex gap-4">
                        {/* Product Image */}
                        {item.product.image_url && (
                          <img
                            src={item.product.image_url}
                            alt={item.product.name}
                            className="w-24 h-24 object-cover rounded"
                          />
                        )}

                        {/* Product Info */}
                        <div className="flex-1">
                          <h3 className="font-semibold text-gray-800 mb-1">
                            {item.product.name}
                          </h3>
                          <p className="text-sm text-gray-600 mb-2">
                            By {item.product.farmer_name}
                          </p>
                          <p className="text-sm text-gray-600">
                            {item.product.description.substring(0, 100)}...
                          </p>
                        </div>

                        {/* Price and Actions */}
                        <div className="text-right">
                          <p className="text-lg font-bold text-green-600 mb-4">
                            ₹{item.product.price}
                          </p>

                          {/* Quantity Control */}
                          <div className="flex items-center gap-2 mb-4">
                            <button
                              onClick={() =>
                                handleUpdateQuantity(item.id, item.quantity - 1)
                              }
                              className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-100"
                            >
                              −
                            </button>
                            <input
                              type="number"
                              value={item.quantity}
                              onChange={(e) =>
                                handleUpdateQuantity(
                                  item.id,
                                  parseInt(e.target.value) || 1
                                )
                              }
                              min="1"
                              className="w-12 border border-gray-300 rounded text-center"
                            />
                            <button
                              onClick={() =>
                                handleUpdateQuantity(item.id, item.quantity + 1)
                              }
                              className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-100"
                            >
                              +
                            </button>
                          </div>

                          {/* Remove Button */}
                          <button
                            onClick={() => handleRemoveItem(item.id)}
                            className="flex items-center justify-center gap-2 text-red-600 hover:text-red-700 font-semibold text-sm"
                          >
                            <FiTrash2 /> Remove
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Order Summary */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow p-6 sticky top-4">
                <h2 className="text-lg font-bold text-gray-800 mb-4">Order Summary</h2>

                <div className="space-y-3 mb-6 border-b pb-6">
                  <div className="flex justify-between text-gray-700">
                    <span>Subtotal</span>
                    <span>₹{cart.total_amount || 0}</span>
                  </div>
                  <div className="flex justify-between text-gray-700">
                    <span>Shipping</span>
                    <span>₹0 (Free)</span>
                  </div>
                  <div className="flex justify-between text-gray-700">
                    <span>Tax (5%)</span>
                    <span>₹{Math.round(cart.total_amount * 0.05 || 0)}</span>
                  </div>
                </div>

                <div className="flex justify-between text-lg font-bold text-gray-800 mb-6">
                  <span>Total</span>
                  <span className="text-green-600">
                    ₹{Math.round(cart.total_amount * 1.05 || 0)}
                  </span>
                </div>

                <button
                  onClick={handleCheckout}
                  className="w-full bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 font-semibold mb-3"
                >
                  Proceed to Checkout
                </button>

                <button
                  onClick={() => navigate('/buyer/marketplace')}
                  className="w-full border border-gray-300 text-gray-700 py-3 rounded-lg hover:bg-gray-50 font-semibold"
                >
                  Continue Shopping
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
