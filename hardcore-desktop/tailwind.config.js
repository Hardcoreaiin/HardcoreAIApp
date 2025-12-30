/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'bg-dark': '#0a0a0f',
                'bg-surface': '#12121a',
                'bg-elevated': '#1a1a24',
                'bg-hover': '#222230',
                'border': '#2a2a3a',
                'text-primary': '#ffffff',
                'text-secondary': '#a0a0b0',
                'text-muted': '#606070',
                'accent-primary': '#6366f1',
                'accent-secondary': '#8b5cf6',
                'success': '#22c55e',
                'warning': '#f59e0b',
                'error': '#ef4444',
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
                mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
            },
        },
    },
    plugins: [],
}
