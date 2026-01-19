
import React, { createContext, useContext, useState, useEffect } from 'react';
import { 
  signInWithPopup, 
  signOut as firebaseSignOut,
  onAuthStateChanged,
  User as FirebaseUser
} from 'firebase/auth';
import { auth, googleProvider } from '../lib/firebase';
import { AuthUser, AuthContextType } from '../types';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Convert Firebase user to our AuthUser type
const mapFirebaseUser = (firebaseUser: FirebaseUser | null): AuthUser | null => {
  if (!firebaseUser) return null;
  
  return {
    id: firebaseUser.uid,
    email: firebaseUser.email || '',
    name: firebaseUser.displayName || firebaseUser.email?.split('@')[0] || 'User'
  };
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!auth) {
      // Firebase not configured, use mock auth
      const timer = setTimeout(() => {
        const stored = localStorage.getItem('clip_user');
        if (stored) setUser(JSON.parse(stored));
        setIsLoading(false);
      }, 800);
      return () => clearTimeout(timer);
    }

    // Listen for auth state changes
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      const mappedUser = mapFirebaseUser(firebaseUser);
      setUser(mappedUser);
      setIsLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const login = async () => {
    if (!auth || !googleProvider) {
      // Fallback to mock login if Firebase not configured
      setIsLoading(true);
      await new Promise(r => setTimeout(r, 1000));
      const mockUser = { id: '1', email: 'guest@cliplink.com', name: 'Guest User' };
      setUser(mockUser);
      localStorage.setItem('clip_user', JSON.stringify(mockUser));
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      const result = await signInWithPopup(auth, googleProvider);
      const mappedUser = mapFirebaseUser(result.user);
      setUser(mappedUser);
    } catch (error: any) {
      console.error('Login error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    if (!auth) {
      // Fallback for mock auth
      setUser(null);
      localStorage.removeItem('clip_user');
      return;
    }

    try {
      await firebaseSignOut(auth);
      setUser(null);
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
