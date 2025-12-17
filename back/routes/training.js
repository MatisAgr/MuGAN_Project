const express = require('express');
const router = express.Router();
const trainingController = require('../controllers/trainingController');

router.get('/', trainingController.getAll);
router.get('/:id', trainingController.getOne);
router.post('/', trainingController.create);
router.put('/:id', trainingController.update);
router.delete('/:id', trainingController.delete);

module.exports = router;
