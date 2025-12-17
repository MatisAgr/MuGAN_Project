const express = require('express');
const router = express.Router();
const generatorController = require('../controllers/generatorController');

router.post('/create', generatorController.generate);

module.exports = router;
