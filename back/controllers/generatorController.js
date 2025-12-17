const { spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const OUTPUT_DIR = path.join(__dirname, '..', '..', 'data', 'generated');

exports.generate = async (req, res) => {
  try {
    const {
      total_midi_files,
      total_sequences,
      train_sequences,
      val_sequences,
      sequence_length,
      min_pitch,
      max_pitch,
      avg_pitch,
      total_notes
    } = req.body;

    // Create output dir if needed
    if (!fs.existsSync(OUTPUT_DIR)) {
      fs.mkdirSync(OUTPUT_DIR, { recursive: true });
    }

    // Generate unique filename
    const filename = `generated_${Date.now()}.mid`;
    const outputPath = path.join(OUTPUT_DIR, filename);

    const scriptPath = path.join(__dirname, '..', '..', 'src', 'generator.py');

    const result = spawnSync('python', [
      scriptPath,
      '--total_midi_files', total_midi_files,
      '--total_sequences', total_sequences,
      '--train_sequences', train_sequences,
      '--val_sequences', val_sequences,
      '--sequence_length', sequence_length,
      '--min_pitch', min_pitch,
      '--max_pitch', max_pitch,
      '--avg_pitch', avg_pitch,
      '--total_notes', total_notes,
      '--output', outputPath
    ]);

    if (result.status !== 0) {
      return res.status(500).json({ error: result.stderr.toString() });
    }

    // Send file as response
    res.download(outputPath, filename);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};
