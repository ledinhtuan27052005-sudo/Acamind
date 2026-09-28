'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Eye, EyeOff, Mail, Lock, BookOpen } from 'lucide-react';
import { GoogleOAuthProvider, GoogleLogin, CredentialResponse } from '@react-oauth/google';
import { authLogin, authGoogleLogin } from '@/lib/api';
import { useAppStore } from '@/store/useAppStore';

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || '';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [remember, setRemember] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { setAuth } = useAppStore();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) { setError('Please fill in all fields'); return; }
    setLoading(true);
    setError('');
    try {
      const res = await authLogin(email, password);
      setAuth(res.user, res.access_token);
      router.push('/');
    } catch (err: unknown) {
      const errWithResponse = err as { response?: { data?: { detail?: string } } };
      const msg = errWithResponse?.response?.data?.detail;
      setError(msg || 'Incorrect email or password');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSuccess = async (response: CredentialResponse) => {
    if (!response.credential) return;
    setLoading(true);
    setError('');
    try {
      const res = await authGoogleLogin(response.credential);
      setAuth(res.user, res.access_token);
      router.push('/');
    } catch (err: unknown) {
      const errWithResponse = err as { response?: { data?: { detail?: string } } };
      const msg = errWithResponse?.response?.data?.detail;
      setError(msg || 'Google login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <div className="min-h-[calc(100vh-56px)] flex items-center justify-center bg-gradient-to-br from-[#FAF9F6] via-[#FAF9F6] to-[#FAF9F6] dark:from-[#070A13] dark:via-[#070A13] dark:to-[#070A13] px-4 py-10 transition-colors duration-500">
        <div className="w-full max-w-md">

          {/* Logo + brand */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-[#002D72] shadow-lg shadow-[#1E88E5]/20 dark:shadow-[#002D72]/30 mb-4">
              <BookOpen className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">Welcome Back</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Log in to Acamind</p>
          </div>

          <div className="bg-white dark:bg-slate-800/60 rounded-2xl shadow-xl shadow-gray-200/60 dark:shadow-black/40 border border-slate-100 dark:border-slate-800 p-8">

            {/* Google Login */}
            {GOOGLE_CLIENT_ID && (
              <>
                <div className="flex justify-center">
                  <GoogleLogin
                    onSuccess={handleGoogleSuccess}
                    onError={() => setError('Google login failed')}
                    width="100%"
                    text="signin_with"
                    shape="rectangular"
                    theme="outline"
                    size="large"
                  />
                </div>

                {/* Divider */}
                <div className="relative my-6">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-slate-100 dark:border-slate-800" />
                  </div>
                  <div className="relative flex justify-center text-xs text-slate-400 dark:text-slate-500 bg-white dark:bg-slate-800/60 px-3">
                    or log in with email
                  </div>
                </div>
              </>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">

              {/* Email */}
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-1.5">
                  Email
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-slate-500" />
                  <input
                    type="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    placeholder="email@example.com"
                    autoComplete="email"
                    className="w-full pl-10 pr-4 py-2.5 border border-slate-200 dark:border-slate-700 dark:border-gray-600 dark:bg-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#1E88E5] focus:border-transparent transition-all placeholder:text-gray-300 dark:placeholder:text-gray-500"
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="text-sm font-medium text-slate-700 dark:text-slate-200">Password</label>
                  <span className="text-xs text-[#1E88E5] hover:text-[#1565C0] cursor-pointer">Forgot password?</span>
                </div>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-slate-500" />
                  <input
                    type={showPw ? 'text' : 'password'}
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="••••••••"
                    autoComplete="current-password"
                    className="w-full pl-10 pr-11 py-2.5 border border-slate-200 dark:border-slate-700 dark:border-gray-600 dark:bg-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#1E88E5] focus:border-transparent transition-all placeholder:text-gray-300 dark:placeholder:text-gray-500"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPw(!showPw)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500 dark:hover:text-gray-300"
                  >
                    {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Remember me */}
              <label className="flex items-center gap-2.5 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={remember}
                  onChange={e => setRemember(e.target.checked)}
                  className="w-4 h-4 rounded border-slate-300 dark:border-slate-600 text-blue-600 focus:ring-[#1E88E5]"
                />
                <span className="text-sm text-slate-600 dark:text-slate-300">Remember me</span>
              </label>

              {/* Error */}
              {error && (
                <div className="flex items-start gap-2.5 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 text-red-700 dark:text-red-300 text-sm rounded-xl px-4 py-3">
                  <span className="shrink-0 mt-0.5">⚠️</span>
                  <span>{error}</span>
                </div>
              )}

              {/* Submit */}
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-[#002D72] hover:bg-[#1E88E5] active:bg-[#1565C0] text-white py-3 rounded-xl font-semibold text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm shadow-[#1E88E5]/20 dark:shadow-[#002D72]/30 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Logging in...
                  </>
                ) : 'Log In'}
              </button>
            </form>

            {/* Divider */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-100 dark:border-slate-800" />
              </div>
              <div className="relative flex justify-center text-xs text-slate-400 dark:text-slate-500 bg-white dark:bg-slate-800/60 px-3">
                Don't have an account?
              </div>
            </div>

            <Link
              href="/register"
              className="w-full block text-center border border-slate-200 dark:border-slate-700 dark:border-gray-600 hover:border-[#1E88E5] dark:hover:border-[#1565C0] text-slate-700 dark:text-slate-200 hover:text-[#1565C0] dark:hover:text-[#64B5F6] py-2.5 rounded-xl font-medium text-sm transition-all"
            >
              Create new account
            </Link>
          </div>
        </div>
      </div>
    </GoogleOAuthProvider>
  );
}
