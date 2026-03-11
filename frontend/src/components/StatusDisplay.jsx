function StatusDisplay({ status, result, error, progress, onReset }) {
    if (status === 'loading') {
        const steps = [
            { label: 'Uploading file...', done: progress >= 2 },
            { label: 'Analyzing data with AI...', done: progress >= 3 },
            { label: 'Sending executive brief...', done: false },
        ]

        const activeIdx = progress <= 1 ? 0 : progress === 2 ? 1 : 2

        return (
            <div className="status status--loading">
                <div className="spinner" role="status" aria-label="Processing" />
                <div className="status__title">Generating your insight brief...</div>
                <p className="status__message">
                    This typically takes 15–30 seconds depending on file size
                </p>
                <div className="progress-steps">
                    {steps.map((step, i) => (
                        <div
                            key={i}
                            className={`progress-step ${step.done ? 'progress-step--done' :
                                    i === activeIdx ? 'progress-step--active' : ''
                                }`}
                        >
                            <span className="progress-step__dot" />
                            <span>{step.done ? '✓' : ''} {step.label}</span>
                        </div>
                    ))}
                </div>
            </div>
        )
    }

    if (status === 'success') {
        return (
            <div className="status status--success">
                <span className="status__icon" style={{ animation: 'checkmark 0.5s ease-out' }}>
                    ✅
                </span>
                <div className="status__title">Insight Brief Sent!</div>
                <p className="status__message">
                    {result?.message || 'Your executive brief has been delivered.'}
                </p>
                {result?.data_shape && (
                    <p className="status__message" style={{ marginTop: '8px', fontSize: '12px' }}>
                        📊 Analyzed {result.data_shape.rows} rows × {result.data_shape.columns} columns
                    </p>
                )}
                <button className="status__retry" onClick={onReset} id="reset-button">
                    ↻ Process Another File
                </button>
            </div>
        )
    }

    if (status === 'error') {
        return (
            <div className="status status--error">
                <span className="status__icon">⚠️</span>
                <div className="status__title">Something went wrong</div>
                <p className="status__message">{error}</p>
                <button className="status__retry" onClick={onReset} id="retry-button">
                    ↻ Try Again
                </button>
            </div>
        )
    }

    return null
}

export default StatusDisplay
