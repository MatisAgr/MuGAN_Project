const express = require('express');
const router = express.Router();
const databasesController = require('../controllers/databaseController');

router.get('/', databasesController.getAll);
router.get('/:id', databasesController.getOne);
router.post('/', databasesController.create);
router.put('/:id', databasesController.update);
router.delete('/:id', databasesController.delete);

module.exports = router;
