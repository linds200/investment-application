import { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import LoginPage from './components/LoginPage'
import { Navbar, Container, Nav, Button} from 'react-bootstrap'
import { clearAuthState, exchangeCodeForToken, getAccessToken, isTokenExpired, redirectToLogout } from './cognito'

const PROCESSED_AUTH_CODE_KEY = 'processed_auth_code'

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [authError, setAuthError] = useState('')

  const resetToLogin = () => {
    clearAuthState()
    sessionStorage.removeItem(PROCESSED_AUTH_CODE_KEY)
    setAuthError('')
    setIsLoggedIn(false)
  }

  const handleLogout = () => {
    resetToLogin()
    redirectToLogout()
  }

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const code = params.get('code')

    if (code) {
      const alreadyProcessedCode = sessionStorage.getItem(PROCESSED_AUTH_CODE_KEY)
      if (alreadyProcessedCode === code) {
        return
      }

      // Prevent duplicate token exchange on StrictMode remount by marking this code as handled.
      sessionStorage.setItem(PROCESSED_AUTH_CODE_KEY, code)
      window.history.replaceState({}, document.title, window.location.pathname)

      exchangeCodeForToken(code)
        .then(() => {setIsLoggedIn(true)})
        .catch((error) => {
          setIsLoggedIn(false)
          setAuthError(error.message || 'Failed to authenticate')
        })
    }
    else {
      const token = getAccessToken()

      if (token && !isTokenExpired(token)) {
        setIsLoggedIn(true)
      } else {
        resetToLogin()
      }
    }
  }, [])

  const handleLogin = (username, password) => {
  }

  if (!isLoggedIn) {
    return <LoginPage handleLogin={handleLogin} authError={authError} />
  }

  return (
    <>
      <div className="App">
        <Navbar bg="dark" variant="dark" expand="lg">
          <Container>
            <Navbar.Brand href="#home">Finance Portal</Navbar.Brand>
            <Navbar.Toggle aria-controls="main-nav" />
            <Navbar.Collapse id="main-nav">
              <Nav className="ms-auto">
                <Button variant="outline-light" onClick={handleLogout}>
                  Logout
                </Button>
              </Nav>
            </Navbar.Collapse>
          </Container>
        </Navbar>

        <Dashboard onSessionExpired={resetToLogin} />
      </div>
    </>
  )
}

export default App