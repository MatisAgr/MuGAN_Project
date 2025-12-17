const mongoose = require('mongoose');

const databaseSchema = new mongoose.Schema({
  canonical_composer: { type: String, required: true },
  canonical_title: { type: String, required: true },
  split: { type: String, enum: ['train', 'validation', 'test'] },
  year: { type: Number },
  midi_filename: { type: String, required: true },
  audio_filename: { type: String },
  duration: { type: Number }
});

module.exports = mongoose.model('Database', databaseSchema);
