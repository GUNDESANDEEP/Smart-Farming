"""
Frontend Testing Configuration and Utilities
Setup for Jest and React Testing Library
"""

// jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  transform: {
    '^.+\\.(js|jsx)$': 'babel-jest',
  },
  testMatch: ['**/__tests__/**/*.test.js', '**/*.test.js'],
  collectCoverageFrom: [
    'src/**/*.{js,jsx}',
    '!src/index.js',
    '!src/serviceWorker.js',
  ],
};

// setupTests.js
import '@testing-library/jest-dom';
import { server } from './mocks/server';

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// mocks/handlers.js
import { http, HttpResponse } from 'msw';

export const handlers = [
  // Auth endpoints
  http.post('/api/auth/register', () => {
    return HttpResponse.json({
      status: 'success',
      data: {
        access_token: 'test-token',
        refresh_token: 'test-refresh',
        user: { id: '1', email: 'test@test.com', role: 'buyer' },
      },
    }, { status: 201 });
  }),

  http.post('/api/auth/login', () => {
    return HttpResponse.json({
      status: 'success',
      data: {
        access_token: 'test-token',
        refresh_token: 'test-refresh',
        user: { id: '1', email: 'test@test.com', role: 'buyer' },
      },
    });
  }),

  // Buyer endpoints
  http.get('/api/buyer/products', () => {
    return HttpResponse.json({
      status: 'success',
      data: [
        {
          id: '1',
          name: 'Test Product',
          price: 100,
          farmer_name: 'Test Farmer',
          stock: 10,
        },
      ],
      pagination: { page: 1, limit: 20, total: 1 },
    });
  }),

  http.get('/api/buyer/cart', () => {
    return HttpResponse.json({
      status: 'success',
      data: { items: [], total_amount: 0 },
    });
  }),
];

// mocks/server.js
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);

// __tests__/components/Login.test.js
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Login from '../../pages/auth/Login';

const renderWithRouter = (component) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('Login Component', () => {
  test('renders login form', () => {
    renderWithRouter(<Login />);
    expect(screen.getByPlaceholderText(/email address/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/password/i)).toBeInTheDocument();
  });

  test('submits form with email and password', async () => {
    renderWithRouter(<Login />);

    const emailInput = screen.getByPlaceholderText(/email address/i);
    const passwordInput = screen.getByPlaceholderText(/password/i);
    const submitButton = screen.getByRole('button', { name: /login/i });

    fireEvent.change(emailInput, { target: { value: 'test@test.com' } });
    fireEvent.change(passwordInput, { target: { value: 'TestPass123!' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/login successful/i)).toBeInTheDocument();
    });
  });

  test('displays error on login failure', async () => {
    renderWithRouter(<Login />);

    const emailInput = screen.getByPlaceholderText(/email address/i);
    const passwordInput = screen.getByPlaceholderText(/password/i);
    const submitButton = screen.getByRole('button', { name: /login/i });

    fireEvent.change(emailInput, { target: { value: 'wrong@test.com' } });
    fireEvent.change(passwordInput, { target: { value: 'WrongPass123!' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/login failed/i)).toBeInTheDocument();
    });
  });
});

// __tests__/hooks/useAuthStore.test.js
import { renderHook, act } from '@testing-library/react';
import { useAuthStore } from '../../store/authStore';

describe('useAuthStore', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
  });

  test('initializes with null user', () => {
    const { result } = renderHook(() => useAuthStore());
    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  test('sets user after login', async () => {
    const { result } = renderHook(() => useAuthStore());

    await act(async () => {
      await result.current.login('test@test.com', 'TestPass123!');
    });

    expect(result.current.user).toBeDefined();
    expect(result.current.isAuthenticated).toBe(true);
  });

  test('clears user after logout', async () => {
    const { result } = renderHook(() => useAuthStore());

    // Login first
    await act(async () => {
      await result.current.login('test@test.com', 'TestPass123!');
    });

    // Then logout
    await act(async () => {
      await result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });
});
