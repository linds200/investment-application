import { useState } from 'react'
import { Modal, Form, Button, Alert } from 'react-bootstrap'

function CreatePortfolioModal({ show, onClose, onCreate, portfolios }) {
    const [name, setName] = useState('')
    const [description, setDescription] = useState('')
    const [error, setError] = useState(null)

    async function handleSubmit(e){
        e.preventDefault()

        const trimmedName = name.trim()
        if (!trimmedName) {
            setError('Portfolio name is required.')
            return
        }

        const duplicate = portfolios.some(p => p.name.toLowerCase() === trimmedName.toLowerCase())
        if (duplicate) {
            setError('A portfolio with this name already exists.')
            return
        }

        try {
            await onCreate(trimmedName, description)
            setName('')
            setDescription('')
            setError('')
        } catch (err) {
            setError(err.message || 'Failed to create portfolio.')
        }
    }

    function handleClose() {
        setName('')
        setDescription('')
        setError(null)
        onClose()
    }

    return <>
        <Modal show={show} onHide={handleClose}>
            <Modal.Header closeButton>
                <Modal.Title>Create New Portfolio</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                {error && <Alert variant="danger">{error}</Alert>}
                <Form onSubmit={handleSubmit} id="create-portfolio-form">
                    <Form.Group className="mb-3" controlId="portfolioName">
                        <Form.Label>Portfolio Name</Form.Label>
                        <Form.Control 
                            type="text" 
                            placeholder="Enter portfolio name"
                            value={name} 
                            onChange={(e) => setName(e.target.value)} 
                            autoFocus
                        />
                    </Form.Group>
                    <Form.Group controlId="portfolioDescription">
                        <Form.Label>Description</Form.Label>
                        <Form.Control 
                            as="textarea" 
                            rows={3} 
                            placeholder="Enter portfolio description"
                            value={description} 
                            onChange={(e) => setDescription(e.target.value)} 
                        />
                    </Form.Group>
                </Form>
            </Modal.Body>
            <Modal.Footer>
                <Button variant="secondary" onClick={handleClose}>Cancel</Button>
                <Button variant="success" type="submit" form="create-portfolio-form">Create</Button>
            </Modal.Footer>
        </Modal>
    </>
}

export default CreatePortfolioModal