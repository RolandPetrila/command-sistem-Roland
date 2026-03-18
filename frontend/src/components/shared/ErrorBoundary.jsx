import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary a prins o eroare:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center h-64 p-8">
          <div className="text-center space-y-4 max-w-md">
            <h2 className="text-xl font-semibold text-red-400">
              Ceva nu a funcționat corect
            </h2>
            <p className="text-sm text-slate-400">
              A apărut o eroare neașteptată. Vă rugăm să reîncărcați pagina sau să încercați din nou.
            </p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="btn-primary px-4 py-2 text-sm"
            >
              Încearcă din nou
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
