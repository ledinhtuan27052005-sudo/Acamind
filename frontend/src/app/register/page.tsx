'use client';

import { useState, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Eye, EyeOff, Mail, Lock, User, Phone, BookOpen, ArrowLeft, RefreshCw } from 'lucide-react';
import { GoogleOAuthProvider, GoogleLogin, CredentialResponse } from '@react-oauth/google';
import { sendOtp, authRegister, authLogin, authGoogleLogin } from '@/lib/api';
import { useAppStore } from '@/store/useAppStore';

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || '';

// ── Password strength ──────────────────────────────────────────────────────────
function PasswordStrength({ password }: { password: string }) {
  if (!password) return null;
  const hasNum = /[0-9]/.test(password);
  const hasSpecial = /[!@#$%^&*]/.test(password);
  const score = password.length >= 12 && hasNum && hasSpecial ? 3
    : password.length >= 8 && (hasNum || hasSpecial) ? 2
      : password.length >= 6 ? 1 : 0;
  const levels = [
    { label: 'Weak', color: 'bg-red-500', text: 'text-red-500' },
    { label: 'Weak', color: 'bg-red-500', text: 'text-red-500' },
    { label: 'Medium', color: 'bg-yellow-500', text: 'text-yellow-600' },
    { label: 'Strong', color: 'bg-green-500', text: 'text-green-600' },
  ];
  const { label, color, text } = levels[score];
  return (
    <div className="mt-2 space-y-1">
      <div className="flex gap-1">
        {[1, 2, 3].map(i => (
          <div key={i} className={`h-1 flex-1 rounded-full transition-all ${i <= score ? color : 'bg-slate-200 dark:bg-slate-700 dark:bg-gray-600'}`} />
        ))}
      </div>
      <p className={`text-xs ${text}`}>Strength: {label}</p>
    </div>
  );
}

// ── OTP Input (6 digits) ───────────────────────────────────────────────────────
function OTPInput({ value, onChange, disabled }: { value: string; onChange: (v: string) => void; disabled?: boolean }) {
  const refs = useRef<(HTMLInputElement | null)[]>([]);

  const handleChange = (i: number, char: string) => {
    if (!/^\d?$/.test(char)) return;
    const arr = value.padEnd(6, ' ').split('');
    arr[i] = char || ' ';
    const next = arr.join('').replace(/ /g, '').slice(0, 6);
    // Build without trailing spaces
    const newVal = arr.join('').trimEnd().slice(0, 6);
    onChange(char ? newVal : value.slice(0, i));
    if (char && i < 5) refs.current[i + 1]?.focus();
  };

  const handleKeyDown = (i: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace') {
      if (!value[i]) {
        if (i > 0) {
          onChange(value.slice(0, i - 1));
          refs.current[i - 1]?.focus();
        }
      } else {
        onChange(value.slice(0, i));
      }
    } else if (e.key === 'ArrowLeft' && i > 0) {
      refs.current[i - 1]?.focus();
    } else if (e.key === 'ArrowRight' && i < 5) {
      refs.current[i + 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    onChange(pasted);
    refs.current[Math.min(pasted.length, 5)]?.focus();
    e.preventDefault();
  };

  return (
    <div className="flex gap-2.5 justify-center">
      {Array.from({ length: 6 }).map((_, i) => (
        <input
          key={i}
          ref={el => { refs.current[i] = el; }}
          type="text"
          inputMode="numeric"
          maxLength={1}
          value={value[i] || ''}
          disabled={disabled}
          onChange={e => handleChange(i, e.target.value)}
          onKeyDown={e => handleKeyDown(i, e)}
          onPaste={i === 0 ? handlePaste : undefined}
          onFocus={e => e.target.select()}
          className={`w-12 h-14 text-center text-2xl font-bold rounded-xl border-2 transition-all focus:outline-none disabled:opacity-50 ${value[i]
              ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300'
              : 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-800 dark:text-slate-100 focus:border-indigo-400 dark:focus:border-indigo-500'
            }`}
        />
      ))}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function RegisterPage() {
  const [step, setStep] = useState<1 | 2>(1);
  const [form, setForm] = useState({ full_name: '', email: '', phone: '', password: '', confirm: '' });
  const [showPw, setShowPw] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [agreed, setAgreed] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // OTP step state
  const [otp, setOtp] = useState('');
  const [otpError, setOtpError] = useState('');
  const [cooldown, setCooldown] = useState(0);
  const [debugOtp, setDebugOtp] = useState<string | null>(null);

  const { setAuth } = useAppStore();
  const router = useRouter();
  const cooldownRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }));

  const startCooldown = () => {
    setCooldown(60);
    if (cooldownRef.current) clearInterval(cooldownRef.current);
    cooldownRef.current = setInterval(() => {
      setCooldown(c => {
        if (c <= 1) { clearInterval(cooldownRef.current!); return 0; }
        return c - 1;
      });
    }, 1000);
  };

  const validate = () => {
    if (!form.full_name.trim()) return 'Please enter your full name';
    if (!form.email) return 'Please enter your email';
    if (form.password.length < 6) return 'Password must be at least 6 characters';
    if (form.password !== form.confirm) return 'Password confirmation does not match';
    if (!agreed) return 'Please agree to the terms of service';
    return null;
  };

  // Step 1: send OTP
  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    const err = validate();
    if (err) { setError(err); return; }
    setLoading(true); setError('');
    try {
      const res = await sendOtp(form.email);
      setDebugOtp(res.debug_otp ?? null);
      startCooldown();
      setStep(2);
      setOtp('');
    } catch (err: unknown) {
      const errWithResponse = err as { response?: { data?: { detail?: string } } };
      const msg = errWithResponse?.response?.data?.detail;
      setError(msg || 'Unable to send OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Resend OTP
  const handleResend = async () => {
    if (cooldown > 0) return;
    setLoading(true); setOtpError(''); setDebugOtp(null);
    try {
      const res = await sendOtp(form.email);
      setDebugOtp(res.debug_otp ?? null);
      startCooldown();
      setOtp('');
    } catch (err: unknown) {
      const errWithResponse = err as { response?: { data?: { detail?: string } } };
      const msg = errWithResponse?.response?.data?.detail;
      setOtpError(msg || 'Error resending OTP');
    } finally {
      setLoading(false);
    }
  };

  // Step 2: verify OTP & register
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (otp.length < 6) { setOtpError('Please enter all 6 digits'); return; }
    setLoading(true); setOtpError('');
    try {
      await authRegister(form.email, form.password, form.full_name, otp);
      const res = await authLogin(form.email, form.password);
      setAuth(res.user, res.access_token);
      if (form.phone && typeof window !== 'undefined') localStorage.setItem('user_phone', form.phone);
      router.push('/');
    } catch (err: unknown) {
      const errWithResponse = err as { response?: { data?: { detail?: string } } };
      const msg = errWithResponse?.response?.data?.detail;
      setOtpError(msg || 'Incorrect OTP. Please check and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSuccess = async (response: CredentialResponse) => {
    if (!response.credential) return;
    setLoading(true); setError('');
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

          {/* Logo */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-[#002D72] shadow-lg shadow-[#1E88E5]/20 dark:shadow-[#002D72]/30 mb-4">
              <BookOpen className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">Create account</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Join Acamind today</p>
          </div>

          {/* Step indicator */}
          <div className="flex items-center justify-center gap-3 mb-6">
            {[
              { n: 1, label: 'Information' },
              { n: 2, label: 'Verify Email' },
            ].map(({ n, label }, idx) => (
              <div key={n} className="flex items-center gap-3">
                {idx > 0 && <div className={`w-10 h-px ${step > 1 ? 'bg-indigo-400' : 'bg-slate-200 dark:bg-slate-700 dark:bg-gray-700'}`} />}
                <div className="flex items-center gap-2">
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all ${step === n ? 'bg-indigo-500 text-white shadow-md shadow-indigo-200 dark:shadow-indigo-900'
                      : step > n ? 'bg-emerald-500 text-white'
                        : 'bg-slate-100 dark:bg-slate-800/60 text-slate-400 dark:text-slate-500'
                    }`}>
                    {step > n ? '✓' : n}
                  </div>
                  <span className={`text-xs font-medium hidden sm:block ${step === n ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-400 dark:text-slate-500'}`}>
                    {label}
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div className="bg-white dark:bg-slate-800/60 rounded-2xl shadow-xl shadow-gray-200/60 dark:shadow-black/40 border border-slate-100 dark:border-slate-800 overflow-hidden">

            {/* ── STEP 1: Registration form ── */}
            {step === 1 && (
              <div className="p-8">
                {/* Google */}
                {GOOGLE_CLIENT_ID && (
                  <>
                    <div className="flex justify-center mb-5">
                      <GoogleLogin
                        onSuccess={handleGoogleSuccess}
                        onError={() => setError('Google sign up failed')}
                        width="100%"
                        text="signup_with"
                        shape="rectangular"
                        theme="outline"
                        size="large"
                      />
                    </div>
                    <div className="relative mb-5">
                      <div className="absolute inset-0 flex items-center">
                        <div className="w-full border-t border-slate-100 dark:border-slate-800" />
                      </div>
                      <div className="relative flex justify-center text-xs text-slate-400 dark:text-slate-500 bg-white dark:bg-slate-800/60 px-3">
                        or sign up with email
                      </div>
                    </div>
                  </>
                )}

                <form onSubmit={handleSendOtp} className="space-y-4">
                  {/* Full name */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-1.5">
                      Full Name <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-slate-500" />
                      <input type="text" value={form.full_name} onChange={set('full_name')} placeholder="John Doe"
                        className="w-full pl-10 pr-4 py-2.5 border border-slate-200 dark:border-slate-700 dark:border-gray-600 dark:bg-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#1E88E5] focus:border-transparent transition-all placeholder:text-gray-300 dark:placeholder:text-gray-500" />
                    </div>
                  </div>

                  {/* Email */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-1.5">
                      Email <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-slate-500" />
                      <input type="email" value={form.email} onChange={set('email')} placeholder="email@example.com" autoComplete="email"
                        className="w-full pl-10 pr-4 py-2.5 border border-slate-200 dark:border-slate-700 dark:border-gray-600 dark:bg-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#1E88E5] focus:border-transparent transition-all placeholder:text-gray-300 dark:placeholder:text-gray-500" />
                    </div>
                  </div>

                  {/* Phone */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-1.5">
                      Phone Number <span className="text-slate-400 dark:text-slate-500 font-normal text-xs">(optional)</span>
                    </label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-slate-500" />
                      <input type="tel" value={form.phone} onChange={set('phone')} placeholder="0912 345 678"
                        className="w-full pl-10 pr-4 py-2.5 border border-slate-200 dark:border-slate-700 dark:border-gray-600 dark:bg-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#1E88E5] focus:border-transparent transition-all placeholder:text-gray-300 dark:placeholder:text-gray-500" />
                    </div>
                  </div>

                  {/* Password */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-1.5">
                      Password <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-slate-500" />
                      <input type={showPw ? 'text' : 'password'} value={form.password} onChange={set('password')}
                        placeholder="At least 6 characters" autoComplete="new-password"
                        className="w-full pl-10 pr-11 py-2.5 border border-slate-200 dark:border-slate-700 dark:border-gray-600 dark:bg-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#1E88E5] focus:border-transparent transition-all placeholder:text-gray-300 dark:placeholder:text-gray-500" />
                      <button type="button" onClick={() => setShowPw(!showPw)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500 dark:hover:text-gray-300">
                        {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    <PasswordStrength password={form.password} />
                  </div>

                  {/* Confirm */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-1.5">
                      Confirm Password <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-slate-500" />
                      <input type={showConfirm ? 'text' : 'password'} value={form.confirm} onChange={set('confirm')}
                        placeholder="Re-enter password" autoComplete="new-password"
                        className={`w-full pl-10 pr-11 py-2.5 border rounded-xl text-sm focus:outline-none focus:ring-2 focus:border-transparent transition-all placeholder:text-gray-300 dark:placeholder:text-gray-500 dark:bg-gray-700 ${form.confirm && form.confirm !== form.password ? 'border-red-400 focus:ring-red-400'
                            : form.confirm && form.confirm === form.password ? 'border-green-400 focus:ring-green-400'
                              : 'border-slate-200 dark:border-slate-700 dark:border-gray-600 focus:ring-[#1E88E5]'
                          }`} />
                      <button type="button" onClick={() => setShowConfirm(!showConfirm)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500 dark:hover:text-gray-300">
                        {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                      {form.confirm && form.confirm === form.password && (
                        <span className="absolute right-9 top-1/2 -translate-y-1/2 text-green-500 text-xs">✓</span>
                      )}
                    </div>
                  </div>

                  {/* Terms */}
                  <label className="flex items-start gap-2.5 cursor-pointer select-none">
                    <input type="checkbox" checked={agreed} onChange={e => setAgreed(e.target.checked)}
                      className="w-4 h-4 mt-0.5 rounded border-slate-300 dark:border-slate-600 text-blue-600 focus:ring-[#1E88E5] shrink-0" />
                    <span className="text-sm text-slate-600 dark:text-slate-300">
                      I agree to the <span className="text-blue-600 hover:underline cursor-pointer">terms of service</span>{' '}
                      and <span className="text-blue-600 hover:underline cursor-pointer">privacy policy</span>
                    </span>
                  </label>

                  {error && (
                    <div className="flex items-start gap-2.5 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 text-red-700 dark:text-red-300 text-sm rounded-xl px-4 py-3">
                      <span className="shrink-0 mt-0.5">⚠️</span>
                      <span>{error}</span>
                    </div>
                  )}

                  <button type="submit" disabled={loading}
                    className="w-full bg-[#002D72] hover:bg-[#1E88E5] active:bg-[#1565C0] text-white py-3 rounded-xl font-semibold text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm shadow-[#1E88E5]/20 dark:shadow-[#002D72]/30 flex items-center justify-center gap-2">
                    {loading ? (
                      <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Sending OTP...</>
                    ) : 'Continue →'}
                  </button>
                </form>

                <div className="relative my-6">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-slate-100 dark:border-slate-800" />
                  </div>
                  <div className="relative flex justify-center text-xs text-slate-400 dark:text-slate-500 bg-white dark:bg-slate-800/60 px-3">
                    Already have an account?
                  </div>
                </div>
                <Link href="/login"
                  className="w-full block text-center border border-slate-200 dark:border-slate-700 dark:border-gray-600 hover:border-[#1E88E5] dark:hover:border-[#1565C0] text-slate-700 dark:text-slate-200 hover:text-[#1565C0] dark:hover:text-[#64B5F6] py-2.5 rounded-xl font-medium text-sm transition-all">
                  Log in
                </Link>
              </div>
            )}

            {/* ── STEP 2: OTP verification ── */}
            {step === 2 && (
              <div className="p-8">
                <button onClick={() => { setStep(1); setOtp(''); setOtpError(''); }}
                  className="flex items-center gap-1.5 text-xs text-slate-400 dark:text-slate-500 dark:hover:text-gray-300 mb-6 transition-colors">
                  <ArrowLeft className="w-3.5 h-3.5" /> Back
                </button>

                <div className="text-center mb-8">
                  <div className="w-14 h-14 bg-indigo-50 dark:bg-indigo-900/30 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <Mail className="w-7 h-7 text-indigo-500" />
                  </div>
                  <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-1">Check your email</h2>
                  <p className="text-sm text-slate-400 dark:text-slate-500">
                    OTP sent to <span className="font-medium text-slate-600 dark:text-slate-300">{form.email}</span>
                  </p>
                </div>

                {/* Dev fallback: show OTP when SMTP not configured */}
                {debugOtp && (
                  <div className="mb-6 p-3.5 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-xl">
                    <p className="text-xs font-semibold text-amber-700 dark:text-amber-400 mb-0.5">Development Mode</p>
                    <p className="text-xs text-amber-600 dark:text-amber-400">
                      SMTP not configured. Your OTP code:{' '}
                      <span className="font-mono font-bold text-base tracking-widest">{debugOtp}</span>
                    </p>
                  </div>
                )}

                <form onSubmit={handleRegister} className="space-y-6">
                  <OTPInput value={otp} onChange={setOtp} disabled={loading} />

                  {otpError && (
                    <div className="flex items-start gap-2.5 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 text-red-700 dark:text-red-300 text-sm rounded-xl px-4 py-3">
                      <span className="shrink-0 mt-0.5">⚠️</span>
                      <span>{otpError}</span>
                    </div>
                  )}

                  <button type="submit" disabled={loading || otp.length < 6}
                    className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-3 rounded-xl font-semibold text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm shadow-indigo-200 dark:shadow-indigo-900 flex items-center justify-center gap-2">
                    {loading ? (
                      <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Verifying...</>
                    ) : 'Create account'}
                  </button>
                </form>

                {/* Resend */}
                <div className="mt-5 text-center">
                  <p className="text-xs text-slate-400 dark:text-slate-500 mb-2">Didn't receive the code?</p>
                  <button onClick={handleResend} disabled={cooldown > 0 || loading}
                    className="inline-flex items-center gap-1.5 text-sm font-medium text-indigo-500 hover:text-indigo-600 disabled:text-gray-300 dark:disabled:text-gray-600 transition-colors">
                    <RefreshCw className="w-3.5 h-3.5" />
                    {cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend OTP'}
                  </button>
                </div>

                <p className="text-center text-[11px] text-slate-300 dark:text-slate-600 mt-4">
                  Code valid for 10 minutes
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </GoogleOAuthProvider>
  );
}
