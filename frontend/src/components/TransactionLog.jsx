import { useEffect, useMemo, useState } from 'react'
import { Alert, Badge, Form, Spinner, Table } from 'react-bootstrap'
import { getAccessToken } from '../cognito'

function formatTransactionDate(value) {
  if (!value) {
    return '—'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return '—'
  }

  return new Intl.DateTimeFormat('en-CA').format(date)
}

function normalizeTransaction(transaction) {
  return {
    id: transaction.transaction_id ?? transaction.id,
    portfolioId: transaction.portfolio_id ?? transaction.portfolioId,
    ticker: transaction.ticker ?? transaction.symbol ?? '',
    type: (transaction.transaction_type ?? transaction.type ?? '').toString().toUpperCase(),
    quantity: transaction.quantity ?? 0,
    price: transaction.price ?? null,
    dateTime: transaction.date_time ?? transaction.timestamp ?? null,
  }
}

function TransactionLog({ portfolios }) {
  const [transactions, setTransactions] = useState([])
  const [selectedPortfolioId, setSelectedPortfolioId] = useState('all')
  const [tickerFilter, setTickerFilter] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let isActive = true

    async function loadTransactions() {
      const token = getAccessToken()

      if (!token) {
        setTransactions([])
        setError('Please log in again to view transaction history.')
        return
      }

      if (!portfolios.length) {
        setTransactions([])
        setError('')
        return
      }

      setLoading(true)
      setError('')

      try {
        const portfolioIds =
          selectedPortfolioId === 'all'
            ? portfolios.map((portfolio) => portfolio.id)
            : [Number(selectedPortfolioId)]

        const responses = await Promise.all(
          portfolioIds.map(async (portfolioId) => {
            const response = await fetch(`/api/portfolios/${portfolioId}/transactions`, {
              headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
              },
            })

            if (!response.ok) {
              throw new Error(`Failed to load transactions for portfolio ${portfolioId}`)
            }

            return response.json()
          })
        )

        if (!isActive) {
          return
        }

        const combinedTransactions = responses
          .flat()
          .map(normalizeTransaction)
          .sort((left, right) => new Date(left.dateTime) - new Date(right.dateTime))

        setTransactions(combinedTransactions)
      } catch (requestError) {
        if (isActive) {
          setTransactions([])
          setError(requestError.message || 'Failed to load transactions.')
        }
      } finally {
        if (isActive) {
          setLoading(false)
        }
      }
    }

    loadTransactions()

    return () => {
      isActive = false
    }
  }, [portfolios, selectedPortfolioId])

  const filteredTransactions = useMemo(() => {
    const normalizedFilter = tickerFilter.trim().toUpperCase()

    return transactions.filter((transaction) => {
      if (!normalizedFilter) {
        return true
      }

      return transaction.ticker.toUpperCase().includes(normalizedFilter)
    })
  }, [tickerFilter, transactions])

  const portfolioLookup = useMemo(
    () => new Map(portfolios.map((portfolio) => [String(portfolio.id), portfolio.name])),
    [portfolios]
  )

  return (
    <div>
          <h5 className="text-start">Transaction History</h5>

      <div>
        <Form.Group className="d-flex justify-content-between align-items-center mb-3">
          <Form.Select value={selectedPortfolioId} onChange={(event) => setSelectedPortfolioId(event.target.value)}>
            <option value="all">All Portfolios</option>
            {portfolios.map((portfolio) => (
              <option key={portfolio.id} value={portfolio.id}>
                {portfolio.name}
              </option>
            ))}
          </Form.Select>
          <Form.Control
            type="text"
            value={tickerFilter}
            onChange={(event) => setTickerFilter(event.target.value)}
            placeholder="Filter by ticker"
          />
        </Form.Group>
      </div>

      {error ? <Alert variant="danger" className="mb-0">{error}</Alert> : null}

      <div className="transaction-log-panel">
        {loading ? (
          <div className="transaction-log-empty">
            <Spinner animation="border" variant="dark" />
          </div>
        ) : filteredTransactions.length === 0 ? (
          <div className="transaction-log-empty">
            No transactions found.
          </div>
        ) : (
          <Table responsive hover className="transaction-log-table mb-0">
            <thead className="table-dark">
              <tr>
                <th>Date</th>
                <th>Portfolio</th>
                <th>Ticker</th>
                <th>Type</th>
                <th>Quantity</th>
              </tr>
            </thead>
            <tbody>
              {filteredTransactions.map((transaction) => (
                <tr key={transaction.id}>
                  <td>{formatTransactionDate(transaction.dateTime)}</td>
                  <td>{portfolioLookup.get(String(transaction.portfolioId)) ?? 'Unknown'}</td>
                  <td className="fw-semibold">{transaction.ticker || '—'}</td>
                  <td>
                    <Badge bg={transaction.type === 'BUY' ? 'success' : 'danger'} pill className="transaction-log-pill">
                      {transaction.type || '—'}
                    </Badge>
                  </td>
                  <td>{transaction.quantity}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </div>
    </div>
  )
}

export default TransactionLog