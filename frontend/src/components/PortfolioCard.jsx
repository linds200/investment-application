import { Card, Button } from 'react-bootstrap'

function PortfolioCard({ portfolio, isSelected, onSelect }) {
  return (
    <Card
      className="h-100"
      border={isSelected ? 'success' : undefined}
      style={{ cursor: 'pointer' }}
      onClick={() => onSelect(portfolio.id)}
    >
      <Card.Body>
        <Card.Title>{portfolio.name}</Card.Title>
        {portfolio.description && (
          <Card.Text className="text-muted">{portfolio.description}</Card.Text>
        )}
      </Card.Body>
      <Card.Footer className="text-end">
        <Button
          variant="outline-success"
          size="sm"
          onClick={e => { e.stopPropagation(); onSelect(portfolio.id) }}
        >
          View Holdings
        </Button>
      </Card.Footer>
    </Card>
  )
}

export default PortfolioCard