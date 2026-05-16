const DOMAIN = import.meta.env.VITE_COGNITO_DOMAIN
const REGION = import.meta.env.VITE_COGNITO_REGION
const CLIENT_ID = import.meta.env.VITE_COGNITO_CLIENT_ID
const REDIRECT_URI = import.meta.env.VITE_REDIRECT_URI

const CODE_VERIFIER_KEY = 'code_verifier'
const TOKEN_KEY = 'access_token'

const generateCodeVerifier = () => {
    const array = new Uint8Array(32)
    window.crypto.getRandomValues(array)
    return btoa(String.fromCharCode.apply(null, array)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

const generateCodeChallenge = async (verifier) => {
    const encoder = new TextEncoder()
    const data = encoder.encode(verifier)
    const digest = await window.crypto.subtle.digest('SHA-256', data)
    return btoa(String.fromCharCode.apply(null, new Uint8Array(digest))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

export const redirectToLogin = async () => {
    const codeVerifier = generateCodeVerifier()
    const codeChallenge = await generateCodeChallenge(codeVerifier)

    sessionStorage.setItem(CODE_VERIFIER_KEY, codeVerifier)

    const params = new URLSearchParams({
    response_type: 'code',
    client_id: CLIENT_ID,
    redirect_uri: REDIRECT_URI,
    prompt: 'login',
    scope: 'openid email profile aws.cognito.signin.user.admin',
    code_challenge_method: 'S256',
    code_challenge: codeChallenge,
    })

    const cognitoLoginUrl = `https://${DOMAIN}.auth.${REGION}.amazoncognito.com/oauth2/authorize?${params}`
    window.location.href = cognitoLoginUrl
}

export const redirectToLogout = () => {
    clearAuthState()

    const params = new URLSearchParams({
        client_id: CLIENT_ID,
        logout_uri: REDIRECT_URI,
    })

    const cognitoLogoutUrl = `https://${DOMAIN}.auth.${REGION}.amazoncognito.com/logout?${params}`
    window.location.href = cognitoLogoutUrl
}

export const exchangeCodeForToken = async (code) => {
    const codeVerifier = sessionStorage.getItem(CODE_VERIFIER_KEY)
    
    if (!codeVerifier) {
        throw new Error('Code verifier not found in session storage')
    }

    const params = new URLSearchParams({
        grant_type: 'authorization_code',
        client_id: CLIENT_ID,
        redirect_uri: REDIRECT_URI,
        code,
        code_verifier: codeVerifier,
    })

    const url = `https://${DOMAIN}.auth.${REGION}.amazoncognito.com/oauth2/token`

    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: params.toString(),
    })

    if (!response.ok) {
        const error_msg = await response.text()
        throw new Error(`Token exchange failed: ${error_msg}`)
    }

    const data = await response.json()
    const token = data.access_token
    sessionStorage.setItem(TOKEN_KEY, token)
    sessionStorage.removeItem(CODE_VERIFIER_KEY)
    return token
}

export const getAccessToken = () => {
    return sessionStorage.getItem(TOKEN_KEY)
}

export const clearAccessToken = () => {
    sessionStorage.removeItem(TOKEN_KEY)
}

export const clearAuthState = () => {
    sessionStorage.removeItem(TOKEN_KEY)
    sessionStorage.removeItem(CODE_VERIFIER_KEY)
}

export const isTokenExpired = (token) => {
    if (!token) {
        return true
    }

    try {
        const payload = JSON.parse(atob(token.split('.')[1]))
        if (!payload.exp) {
            return true
        }

        const nowInSeconds = Math.floor(Date.now() / 1000)
        return payload.exp <= nowInSeconds
    }
    catch {
        return true
    }
}