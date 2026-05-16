import { useState } from 'react'
import { Alert, Button, Form, Row, Col, Card } from 'react-bootstrap'

function TradePanel({ portfolio, holdings, onBuy, onSell }) {
    const [ticker, setTicker] = useState('')
    const [quantity, setQuantity] = useState('')
    const [error, setError] = useState('')
    const [success, setSuccess] = useState('')

    if (!portfolio) {
        return <Alert variant="info">Please select a portfolio from the <strong>Portfolios</strong> tab to trade.</Alert>
    }

    async function handleTrade(type){
        setError('')
        setSuccess('')
        
        const trimmedTicker = ticker.trim().toUpperCase()
        const qty = parseInt(quantity, 10)

        if (!trimmedTicker) {
            setError('Ticker symbol cannot be empty')
            return
        }
        if (!qty || isNaN(qty) || qty <= 0) {
            setError('Quantity must be a positive number')
            return
        }

        const fn = type === 'buy' ? onBuy : onSell
        let result
        try {
            result = await fn(portfolio.id, trimmedTicker, qty)
        } catch (err) {
            setError(err.message || 'Trade failed')
            return
        }

        if (!result?.ok) {
            setError(result?.error || 'Trade failed')
        } else {
            setSuccess(result?.message || `${type === 'buy' ? 'Bought' : 'Sold'} ${qty} share(s) of ${trimmedTicker} successfully!`)
            setTicker('')
            setQuantity('')
        }
    }

    return (
        <div>
            <h5 align="left" className="mb-2">Trading for Portfolio: <strong>{portfolio.name}</strong></h5>
            {error && <Alert variant="danger" dismissible onClose={() => setError('')}>{error}</Alert>}
            {success && <Alert variant="success" dismissible onClose={() => setSuccess('')}>{success}</Alert>}

            <Card style ={{ maxWidth: '430px' }}>
                <Card.Body>
                    <Form>
                        <Row className="mb-3">
                            <Col>
                                <Form.Label align="left" className="d-block">Ticker Symbol</Form.Label>
                                <Form.Control 
                                    type="text"
                                    placeholder="e.g. AAPL"
                                    value={ticker}
                                    onChange={(e) => setTicker(e.target.value)}
                                />
                            </Col>
                            <Col>
                                <Form.Label align="left" className="d-block">Quantity</Form.Label>
                                <Form.Control 
                                    type="number"
                                    min="1"
                                    placeholder="e.g. 10"
                                    value={quantity}
                                    onChange={(e) => setQuantity(e.target.value)}
                                />
                            </Col>
                        </Row>

                        <div className="d-flex gap-2">
                            <Button variant="success" onClick={() => handleTrade('buy')}>Buy</Button>
                            <Button variant="danger" onClick={() => handleTrade('sell')}>Sell</Button>
                        </div>
                    </Form>
                </Card.Body>
            </Card>

            {holdings.length > 0 && (
                <div className="mt-4">
                    <h6 align="left">Current Holdings:</h6>
                    <ul className="list-unstyled">
                        {holdings.map((holding) => (
                            <li align="left" key={holding.ticker}>
                                <span className="fw-bold">{holding.ticker}</span>
                                <span className="text-muted ms-2">{holding.quantity} share(s)</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    )
}

    export default TradePanel