import { useRef, useCallback, useState } from 'react'

function FileUploader({ file, onFileSelect, disabled }) {
    const fileInputRef = useRef(null)
    const [isDragActive, setIsDragActive] = useState(false)

    const handleDragOver = useCallback((e) => {
        e.preventDefault()
        e.stopPropagation()
        if (!disabled) setIsDragActive(true)
    }, [disabled])

    const handleDragLeave = useCallback((e) => {
        e.preventDefault()
        e.stopPropagation()
        setIsDragActive(false)
    }, [])

    const handleDrop = useCallback((e) => {
        e.preventDefault()
        e.stopPropagation()
        setIsDragActive(false)

        if (disabled) return

        const droppedFile = e.dataTransfer.files[0]
        if (droppedFile && isValidFile(droppedFile)) {
            onFileSelect(droppedFile)
        }
    }, [disabled, onFileSelect])

    const handleFileInput = useCallback((e) => {
        const selected = e.target.files[0]
        if (selected && isValidFile(selected)) {
            onFileSelect(selected)
        }
    }, [onFileSelect])

    const isValidFile = (f) => {
        const ext = f.name.split('.').pop()?.toLowerCase()
        return ['csv', 'xlsx'].includes(ext)
    }

    const formatSize = (bytes) => {
        if (bytes < 1024) return `${bytes} B`
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    }

    const getFileIcon = (filename) => {
        if (filename.endsWith('.xlsx')) return '📗'
        return '📄'
    }

    // If file is selected, show the chip
    if (file) {
        return (
            <div className="file-chip">
                <span className="file-chip__icon">{getFileIcon(file.name)}</span>
                <div className="file-chip__info">
                    <div className="file-chip__name">{file.name}</div>
                    <div className="file-chip__size">{formatSize(file.size)}</div>
                </div>
                {!disabled && (
                    <button
                        type="button"
                        className="file-chip__remove"
                        onClick={() => onFileSelect(null)}
                        aria-label="Remove file"
                    >
                        ✕
                    </button>
                )}
            </div>
        )
    }

    // Drop zone
    return (
        <>
            <div
                className={`dropzone ${isDragActive ? 'dropzone--active' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => !disabled && fileInputRef.current?.click()}
                role="button"
                tabIndex={0}
                aria-label="Upload file"
                id="file-dropzone"
            >
                <span className="dropzone__icon">📊</span>
                <p className="dropzone__text">
                    <strong>Drop your sales data here</strong>
                    <br />
                    or click to browse files
                </p>
                <p className="dropzone__hint">
                    Supports .csv and .xlsx • Max 10MB
                </p>
            </div>
            <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xlsx"
                onChange={handleFileInput}
                style={{ display: 'none' }}
                aria-hidden="true"
            />
        </>
    )
}

export default FileUploader
