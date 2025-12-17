const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
require('dotenv').config();

const trainingRoutes = require('./routes/training');
const generatorRoutes = require('./routes/generator');
const databasesRoutes = require('./routes/database');

const app = express();

app.use(cors());
app.use(express.json());

// MongoDB connection
mongoose.connect(process.env.MONGO_URI)
  .then(() => console.log('MongoDB connected'))
  .catch(err => console.error('MongoDB connection error:', err));

// Routes
app.use('/api/training', trainingRoutes);
app.use('/api/generator', generatorRoutes);
app.use('/api/databases', databasesRoutes);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
