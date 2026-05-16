import { Alert } from 'react-bootstrap'
import './LoginPage.css'
import { redirectToLogin } from '../cognito'

const LoginPage = ({ authError }) => {
    return (
        <div className="lp-root">
            <section className="lp-hero">
                <div className="lp-hero-overlay" />

                <div className="lp-hero-content">
                    <div className="lp-brand-row">
                        <span className="lp-brand-mark">FP</span>
                        <span className="lp-brand-name">Finance Portal</span>
                    </div>

                    <h1 className="lp-headline">Your portfolio, in one place.</h1>
                    <p className="lp-subline">Track your holdings, execute trades, and review every transaction seamlessly.</p>
                </div>
            </section>

            <aside className="lp-panel">
                <div className="lp-card">
                    <h2 className="lp-card-title">Welcome back</h2>
                    <p className="lp-card-sub">Sign in to access your portfolio dashboard.</p>

                    {authError ? <Alert variant="danger" className="lp-alert">{authError}</Alert> : null}

                    <button className="lp-signin-btn" onClick={redirectToLogin}>
                        Sign in
                    </button>

                    <p className="lp-card-footer">Don't have an account? Click the sign in button to create one.</p>
                </div>
            </aside>
        </div>
    )
}

export default LoginPage