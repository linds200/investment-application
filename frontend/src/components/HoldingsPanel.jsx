import { Alert, Button, Table } from 'react-bootstrap'

function HoldingsPanel({ portfolio, holdings, onGoTrade }) {
  if (!portfolio) {
    return (
      <Alert variant="info">
        Select a portfolio from the <strong>Portfolios</strong> tab to view its holdings.
      </Alert>
    )
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h5 className="mb-0 text-start">{portfolio.name}</h5>
          <p className="mb-0">{portfolio.description}</p>
        </div>
        <Button variant="success" size="sm" onClick={onGoTrade}>
          Trade
        </Button>
      </div>

      {holdings.length === 0 ? (
        <p className="text-muted">No holdings yet. Use the Trade tab to buy securities.</p>
      ) : (
        <Table striped bordered hover responsive>
          <thead className="table-dark">
            <tr>
              <th>Ticker</th>
              <th>Quantity</th>
            </tr>
          </thead>
          <tbody>
            {holdings.map((h, idx) => (
              <tr key={`${h.ticker}-${idx}`}>
                <td className="fw-bold">{h.ticker}</td>
                <td>{h.quantity}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
    </div>
  )
}

export default HoldingsPanel