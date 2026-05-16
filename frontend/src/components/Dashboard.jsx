import { useState, useEffect } from 'react'
import { Container, Tabs, Tab, Spinner, Alert } from 'react-bootstrap'
import { getAccessToken } from '../cognito'
import PortfolioList from './PortfolioList'
import CreatePortfolioModal from './CreatePortfolioModal'
import DeletePortfolioModal from './DeletePortfolioModal'
import HoldingsPanel from './HoldingsPanel'
import TradePanel from './TradePanel'
import TransactionLog from './TransactionLog'

function Dashboard({ onSessionExpired }) {

  const [isLoading, setIsLoading] = useState(false)
  const [showErrorAlert, setShowErrorAlert] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [portfolios, setPortfolios] = useState([])
  const [refreshPortfolioList, setRefreshPortfolioList] = useState(0)
  const [portfolioToDelete, setPortfolioToDelete] = useState(null)
  const [nextPortfolioId, setNextPortfolioId] = useState(1)
  const [holdings, setHoldings] = useState([])
  const [selectedPortfolioId, setSelectedPortfolioId] = useState(null)
  const [activeTab, setActiveTab] = useState('portfolios')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)

  useEffect(() => {
    const showFullPageLoader = refreshPortfolioList === 0
    if (showFullPageLoader) {
      setIsLoading(true)
    }

    const token = getAccessToken()

    if (!token) {
      onSessionExpired?.()
      return
    }

    const handleUnauthorized = (message) => {
      setErrorMessage(message)
      setShowErrorAlert(true)
      onSessionExpired?.()
    }

    fetch('/api/portfolios/', {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }).then(res => {
      if (res.status === 401 || res.status === 403) {
        handleUnauthorized('Your session has expired. Please log in again.')
        return
      }

      if (!res.ok) {
        return res.json().then(errorData => {
          setErrorMessage(errorData.error)
          setShowErrorAlert(true)
        })
      } else {
        res.json().then(data => {
          setPortfolios(data)
        })
      }
    }).catch(error => {
      setErrorMessage(error.message)
      setShowErrorAlert(true)
    }).finally(() => {
      if (showFullPageLoader) {
        setIsLoading(false)
      }
    })
  }, [refreshPortfolioList])

  function handleSelectPortfolio(id) {
    setSelectedPortfolioId(id)
    setActiveTab('holdings')
  }

  async function handleCreatePortfolio(name, description) {
    const token = getAccessToken()
    const res = await fetch('/api/portfolios/', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ name, description })
    })

    if (res.status === 401 || res.status === 403) {
      onSessionExpired?.()
      return
    }
    
    if (!res.ok) {
      const errorData = await res.json()
      throw new Error(errorData.error || `Request failed with status ${res.status}`)
    }

    setRefreshPortfolioList(i => i + 1)
    setShowCreateModal(false)
  }

  async function handleDeletePortfolio() {
    const token = getAccessToken()
    const res = await fetch(`/api/portfolios/${portfolioToDelete.id}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (res.status === 401 || res.status === 403) {
      onSessionExpired?.()
      return
    }
    
    if (!res.ok) {
      const errorData = await res.json()
      throw new Error(errorData.error || `Request failed with status ${res.status}`)
    }

    setShowDeleteModal(false)
    setPortfolioToDelete(null)
    setRefreshPortfolioList(i => i + 1)

  }

  async function handleBuy(portfolioId, ticker, quantity) {
    try {
      const token = getAccessToken()

      const res = await fetch(`/api/trades/buy`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ portfolio_id: portfolioId, ticker, quantity })
      })

      if (res.status === 401 || res.status === 403) {
        onSessionExpired?.()
        return { ok: false, error: 'Your session has expired. Please log in again.' }
      }

      if (!res.ok) {
        const errorData = await res.json()
        return { ok: false, error: errorData.error || `Request failed with status ${res.status}` }
      }

      const data = await res.json()
      setRefreshPortfolioList(i => i + 1)
      return { ok: true, message: data?.message || 'Purchase order executed successfully' }
    } catch (error) {
      return { ok: false, error: error.message || 'Trade failed' }
    }
  }

  async function handleSell(portfolioId, ticker, quantity) {
    try {
      const token = getAccessToken()

      const res = await fetch(`/api/trades/sell`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ portfolio_id: portfolioId, ticker, quantity})
      })

      if (res.status === 401 || res.status === 403) {
        onSessionExpired?.()
        return { ok: false, error: 'Your session has expired. Please log in again.' }
      }

      if (!res.ok) {
        const errorData = await res.json()
        return { ok: false, error: errorData.error || `Request failed with status ${res.status}` }
      }

      const data = await res.json()
      setRefreshPortfolioList(i => i + 1)
      return { ok: true, message: data?.message || 'Investment liquidated successfully' }
    } catch (error) {
      return { ok: false, error: error.message || 'Trade failed' }
    }
  }

  const selectedPortfolio = portfolios.find(p => p.id === selectedPortfolioId) || null
  const selectedHoldings  = selectedPortfolio?.investments ?? []

  return (
    <>
      {
        isLoading && (
          <div style = {{position: 'fixed', inset: 0, backgroundColor: 'rgba(255, 255, 255, 0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999}}>
            <Spinner animation="border" variant="dark" />
          </div>
        )
      }
      {
        !isLoading &&(
          <Container className="mt-4">
            {
              showErrorAlert && (
                <Alert variant="danger" onClose={() => setShowErrorAlert(false)} dismissible>
                  <Alert.Heading>Error</Alert.Heading>
                  <p>{errorMessage}</p>
                </Alert>
              )
            }
            <Tabs activeKey={activeTab} onSelect={setActiveTab} className="mb-3">

              <Tab eventKey="portfolios" title="Portfolios">
                <PortfolioList
                  portfolios={portfolios}
                  selectedPortfolioId={selectedPortfolioId}
                  onSelect={handleSelectPortfolio}
                  onOpenCreate={() => {setShowCreateModal(true)}}
                  onDelete={(portfolio) => {setPortfolioToDelete(portfolio); setShowDeleteModal(true)}}
                />
                <CreatePortfolioModal
                  show={showCreateModal}
                  onClose={() => setShowCreateModal(false)}
                  onCreate={handleCreatePortfolio}
                  portfolios={portfolios}
                />
                <DeletePortfolioModal
                  show={showDeleteModal}
                  portfolio={portfolioToDelete}
                  onClose={() => {setShowDeleteModal(false); setPortfolioToDelete(null)}}
                  onDelete = {handleDeletePortfolio}
                />
              </Tab>

              <Tab eventKey="holdings" title="Holdings">
                <HoldingsPanel
                  portfolio={selectedPortfolio}
                  holdings={selectedHoldings}
                  onGoTrade={() => setActiveTab('trade')}
                />
              </Tab>

              <Tab eventKey="trade" title="Trade">
                <TradePanel 
                portfolio={selectedPortfolio} 
                holdings={selectedHoldings}
                onBuy = {handleBuy}
                onSell = {handleSell}
                />
              </Tab>

              <Tab eventKey="transactions" title="Transactions">
                <TransactionLog 
                portfolios={portfolios}
                />
              </Tab>

            </Tabs>
          </Container>
        )
      }
    </>
  )
}

export default Dashboard