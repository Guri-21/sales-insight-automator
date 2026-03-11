import { useState, useRef, useCallback } from 'react'
import axios from 'axios'
import FileUploader from './components/FileUploader'
import StatusDisplay from './components/StatusDisplay'

const API_URL = import.meta.env.VITE_API_URL || ''

function App() {
    const [file, setFile] = useState(null)
    const [email, setEmail] = useState('')
    const [status, setStatus] = useState('idle') // idle | loading | success | error
    const [result, setResult] = useState(null)
    const [error, setError] = useState('')
    const [progress, setProgress] = useState(0) // 0-3: upload, parse, ai, email

    const handleSubmit = useCallback(async (e) => {
        e.preventDefault()
        if (!file || !email) return

        setStatus('loading')
        setProgress(0)
        setError('')
        setResult(null)

        const formData = new FormData()
        formData.append('file', file)
        formData.append('email', email)

        // Simulate progress stages
        setProgress(1) // Uploading

        try {
            const response = await axios.post(`${API_URL}/api/upload`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
                timeout: 120000, // 2 min timeout for AI processing
                onUploadProgress: (progressEvent) => {
                    if (progressEvent.loaded === progressEvent.total) {
                        setProgress(2) // Processing
                    }
                },
            })

            if (response.data.status === 'error') {
                setStatus('error')
                setError(response.data.detail || 'An error occurred')
                return
            }

            setProgress(3)
            setResult(response.data)
            setStatus('success')
        } catch (err) {
            setStatus('error')
            if (err.response?.status === 429) {
                setError('Rate limit exceeded. Please wait a moment before trying again.')
            } else if (err.response?.data?.detail) {
                setError(err.response.data.detail)
            } else if (err.code === 'ECONNABORTED') {
                setError('Request timed out. The file may be too large or the service is busy.')
            } else {
                setError('Failed to connect to the server. Please check your connection.')
            }
        }
    }, [file, email])

    const handleReset = useCallback(() => {
        setFile(null)
        setEmail('')
        setStatus('idle')
        setResult(null)
        setError('')
        setProgress(0)
    }, [])

    return (
        <div className="app">
            {/* Header */}
            <header className="header">
                <div className="header__badge">
                    Rabbitt AI • Sales Intelligence
                </div>
                <h1 className="header__title">Sales Insight Automator</h1>
                <p className="header__subtitle">
                    Upload your sales data and receive an AI-generated executive brief
                    delivered straight to your inbox
                </p>
            </header>

            {/* Main Card */}
            <main className="card">
                <form onSubmit={handleSubmit}>
                    {/* File Upload */}
                    <FileUploader
                        file={file}
                        onFileSelect={setFile}
                        disabled={status === 'loading'}
                    />

                    {/* Email Input */}
                    <div className="input-group">
                        <label className="input-group__label" htmlFor="email-input">
                            Recipient Email
                        </label>
                        <input
                            id="email-input"
                            type="email"
                            className="input-group__field"
                            placeholder="executive@company.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            disabled={status === 'loading'}
                            autoComplete="email"
                        />
                    </div>

                    {/* Submit */}
                    <button
                        type="submit"
                        className={`btn-submit ${status === 'loading' ? 'btn-submit--loading' : ''}`}
                        disabled={!file || !email || status === 'loading'}
                    >
                        {status === 'loading' ? '⚡ Processing...' : '🚀 Generate & Send Insight Brief'}
                    </button>
                </form>

                {/* Status */}
                {status !== 'idle' && (
                    <StatusDisplay
                        status={status}
                        result={result}
                        error={error}
                        progress={progress}
                        onReset={handleReset}
                    />
                )}
            </main>

            {/* Footer */}
            <footer className="footer">
                <p>
                    Powered by <strong>Groq AI (Llama 3)</strong> •{' '}
                    <a href={`${API_URL}/docs`} target="_blank" rel="noopener noreferrer">
                        API Documentation
                    </a>
                </p>
            </footer>
        </div>
    )
}

export default App
