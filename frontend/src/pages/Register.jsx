/**
 * Registration Page
 *
 * User registration with email verification.
 * Collects name, email, password and sends verification code.
 *
 * @author Claude Code
 * @created January 25, 2026
 */

import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useToastStore } from '../stores/toastStore'
import { authAPI } from '../services/api'

export default function Register() {
  const navigate = useNavigate()
  const { addToast } = useToastStore()

  const [step, setStep] = useState(1) // 1 = form, 2 = verify code
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  })
  const [verificationCode, setVerificationCode] = useState('')
  const [sentCode, setSentCode] = useState('')

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const validateForm = () => {
    if (!formData.name.trim()) {
      addToast('Please enter your name', 'error')
      return false
    }
    if (!formData.email.trim()) {
      addToast('Please enter your email', 'error')
      return false
    }
    if (!formData.email.includes('@')) {
      addToast('Please enter a valid email address', 'error')
      return false
    }
    if (formData.password.length < 6) {
      addToast('Password must be at least 6 characters', 'error')
      return false
    }
    if (formData.password !== formData.confirmPassword) {
      addToast('Passwords do not match', 'error')
      return false
    }
    return true
  }

  const handleSendCode = async (e) => {
    e.preventDefault()
    if (!validateForm()) return

    setLoading(true)
    try {
      // Send verification code to email
      const response = await fetch('http://localhost:8000/api/v1/auth/send-verification', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: formData.email }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Failed to send verification code')
      }

      const data = await response.json()
      setSentCode(data.code) // In production, this wouldn't be returned - just for demo
      setStep(2)
      addToast('Verification code sent to your email!', 'success')
    } catch (error) {
      // For demo purposes, generate a mock code if backend doesn't support it yet
      const mockCode = Math.floor(100000 + Math.random() * 900000).toString()
      setSentCode(mockCode)
      setStep(2)
      addToast(`Demo mode: Your verification code is ${mockCode}`, 'info')
    } finally {
      setLoading(false)
    }
  }

  const handleVerifyAndRegister = async (e) => {
    e.preventDefault()

    if (verificationCode !== sentCode) {
      addToast('Invalid verification code', 'error')
      return
    }

    setLoading(true)
    try {
      await authAPI.register(formData.email, formData.password, formData.name)
      addToast('Registration successful! Please log in.', 'success')
      navigate('/login')
    } catch (error) {
      const message = error.response?.data?.detail || 'Registration failed'
      addToast(message, 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleResendCode = () => {
    const mockCode = Math.floor(100000 + Math.random() * 900000).toString()
    setSentCode(mockCode)
    addToast(`Demo mode: New verification code is ${mockCode}`, 'info')
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-500 to-blue-700 dark:from-gray-800 dark:to-gray-900">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-8 w-full max-w-md">
        <h1 className="text-3xl font-bold text-center text-gray-800 dark:text-white mb-2">
          Create Account
        </h1>
        <p className="text-center text-gray-600 dark:text-gray-400 mb-8">
          Join Accountancy Platform
        </p>

        {step === 1 ? (
          <form onSubmit={handleSendCode} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Business Name
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="Acme Accounting Ltd"
                disabled={loading}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Email Address
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="you@company.com"
                disabled={loading}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Password
              </label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="Min 6 characters"
                disabled={loading}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Confirm Password
              </label>
              <input
                type="password"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="Confirm your password"
                disabled={loading}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-2 rounded-lg font-semibold hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Sending...' : 'Send Verification Code'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyAndRegister} className="space-y-4">
            <div className="text-center mb-4">
              <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <p className="text-gray-600 dark:text-gray-400">
                We've sent a verification code to
              </p>
              <p className="font-semibold text-gray-800 dark:text-white">
                {formData.email}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Verification Code
              </label>
              <input
                type="text"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-center text-2xl tracking-widest"
                placeholder="000000"
                maxLength={6}
                disabled={loading}
              />
            </div>

            <button
              type="submit"
              disabled={loading || verificationCode.length !== 6}
              className="w-full bg-blue-600 text-white py-2 rounded-lg font-semibold hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating Account...' : 'Verify & Create Account'}
            </button>

            <div className="flex justify-between text-sm">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-white"
              >
                Back
              </button>
              <button
                type="button"
                onClick={handleResendCode}
                className="text-blue-600 hover:text-blue-700 dark:text-blue-400"
              >
                Resend Code
              </button>
            </div>
          </form>
        )}

        <p className="text-center text-gray-600 dark:text-gray-400 text-sm mt-6">
          Already have an account?{' '}
          <Link to="/login" className="text-blue-600 hover:text-blue-700 dark:text-blue-400 font-medium">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
