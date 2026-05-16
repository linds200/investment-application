import { Row, Col, Card, Button } from 'react-bootstrap'
import { BsTrash } from 'react-icons/bs'

function PortfolioList({ portfolios, selectedPortfolioId, onSelect, onOpenCreate, onDelete }) {
  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h5 className="mb-0">Your Portfolios</h5>
        <Button variant="success" size="sm" onClick={onOpenCreate}>
          + New Portfolio
        </Button>
      </div>

      {portfolios.length === 0 && (
        <p className="text-muted">No portfolios yet. Create one to get started.</p>
      )}

      <Row xs={1} md={2} lg={3} className="g-3">
        {portfolios.map(portfolio => (
          <Col key={portfolio.id}>
            <Card
              className="h-100"
              border={portfolio.id === selectedPortfolioId ? 'success' : undefined}
              style={{ cursor: 'pointer' }}
              onClick={() => onSelect(portfolio.id)}
            >
              <Card.Body>
                <Card.Title className="text-start">{portfolio.name}</Card.Title>
                <Card.Text className="text-start">{portfolio.description || 'No description.'}</Card.Text>
              </Card.Body>
              <Card.Footer className="d-flex justify-content-end gap-2">
                <Button variant="outline-danger" size="sm" onClick={(e) => {e.stopPropagation(); onDelete(portfolio)}}>
                  <BsTrash />
                </Button>
                <Button variant="outline-success" size="sm" onClick={(e) => {e.stopPropagation(); onSelect(portfolio.id)}}>
                  View Holdings
                </Button>
              </Card.Footer>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  )
}

export default PortfolioList