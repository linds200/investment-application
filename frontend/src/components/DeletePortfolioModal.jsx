import { useState } from 'react'
import { Alert, Button, Form, Modal, Spinner } from 'react-bootstrap'

function DeletePortfolioModal({ show, portfolio, onDelete, onClose }) {
    
    const [error, setError] = useState('')
    const [deleting, setDeleting] = useState(false)

    async function handleConfirm() {
        try{
            await onDelete()
            setError('')
        } catch (err) {
            setError(err.message || 'Failed to delete portfolio.')
        } finally {
            setDeleting(false)
        }
    }

    function handleClose() {
        setError('')
        onClose()
    }

    return (
        <Modal show={show} onHide={handleClose}>
            <Modal.Header closeButton = {!deleting}>
                <Modal.Title>Delete Portfolio</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                {error && <Alert variant="danger">{error}</Alert>}
                {portfolio && (
                    <p>Are you sure you want to delete the portfolio <strong>{portfolio.name}</strong>? This action cannot be undone.</p>
                )}
            </Modal.Body>
            <Modal.Footer>
                <Button variant="secondary" onClick={handleClose} disabled={deleting}>No</Button>
                <Button variant="danger" onClick={handleConfirm} disabled={deleting}>
                    {deleting ? <><Spinner as="span" animation="border" className = "me-2"  />Deleting...</> : 'Yes, Delete'}
                </Button>
            </Modal.Footer>
        </Modal>
    )
}

export default DeletePortfolioModal